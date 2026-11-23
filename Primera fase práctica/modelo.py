"""Usa el modelo entrenado en el notebook para buscar y explicar candidatos (sin interfaz).

Lee el "paquete" que exporta la sección 11 de FairPlay_AI_Clasificador_Pares.ipynb:

    modelo/
    ├── modelo_pares.joblib   modelos A y B, señales que usa cada uno y configuración
    ├── catalogo.parquet      catálogo limpio, en el mismo orden que los embeddings
    ├── emb_texto.npy         embeddings de texto (una fila por juego)
    └── imagenes.joblib       por appid: embeddings CLIP y hashes de sus imágenes

No necesita GPU ni descargar modelos de lenguaje o de visión: todo eso ya se
calculó en el notebook. Por eso solo puede buscar juegos que estén en el catálogo.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel

from senales import SENALES, CalculadoraSenales
from similitud import BuscadorTfidf

ARCHIVOS = ["modelo_pares.joblib", "catalogo.parquet", "emb_texto.npy", "imagenes.joblib"]
# Los candidatos salen del texto; además se suman los juegos con una imagen casi idéntica (coseno CLIP).
# Con este umbral las búsquedas normales no cambian y aparecen los clones que reescriben la descripción
# pero reutilizan imágenes (ver experimentos/vecinos_imagen).
UMBRAL_IMAGEN_IDENTICA = 0.96
URL_HEADER = "https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
# Nombres legibles de cada señal, para mostrar en la app en vez del nombre técnico
NOMBRES_SENALES = {
    "tfidf_cos": "Texto: mismas palabras",
    "emb_cos": "Texto: mismo significado",
    "img_cos": "Imágenes parecidas (CLIP)",
    "phash_sim": "Imagen casi idéntica (hash)",
    "titulo_sim": "Títulos parecidos",
    "tags_jaccard": "Géneros y tags en común",
    "log_dias": "Distancia entre fechas",
    "mismo_dev": "Mismo desarrollador",
}


def cargar_artefacto(ruta: Path) -> dict:
    """Carga modelo_pares.joblib y exige la misma versión de scikit-learn que lo entrenó.

    Un modelo guardado con una versión de scikit-learn puede fallar con otra (por ejemplo
    "'SimpleImputer' object has no attribute '_fill_dtype'"), así que se detiene antes con
    un mensaje que dice qué versión instalar.
    """
    import warnings

    import sklearn
    from sklearn.exceptions import InconsistentVersionWarning

    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always", InconsistentVersionWarning)
        art = joblib.load(ruta)
    distintas = {a.message.original_sklearn_version for a in avisos
                 if issubclass(a.category, InconsistentVersionWarning)}
    if distintas:
        raise RuntimeError(
            f"El modelo se entrenó con scikit-learn {', '.join(sorted(distintas))} y aquí está instalada "
            f"la {sklearn.__version__}. Vuelve a exportar el paquete con el notebook (que instala la misma "
            "versión que requirements.txt) o instala esa versión: pip install scikit-learn==<versión>.")
    return art


def nombre_legible(senal: str) -> str:
    """'missingindicator_img_cos' -> 'Sin dato: Imágenes parecidas (CLIP)'."""
    if senal.startswith("missingindicator_"):
        base = senal.removeprefix("missingindicator_")
        return f"Sin dato: {NOMBRES_SENALES.get(base, base)}"
    return NOMBRES_SENALES.get(senal, senal)


COLUMNAS_CANDIDATOS = ["Juego", "Desarrollador", "Fecha", "Prob. revisar", "Texto (palabras)",
                       "Texto (significado)", "Imagen (CLIP)", "Imagen idéntica", "Título", "Géneros y tags",
                       "Términos compartidos"]


class BuscadorModelo:
    def __init__(self, carpeta: str | Path):
        carpeta = Path(carpeta)
        faltan = [f for f in ARCHIVOS if not (carpeta / f).exists()]
        if faltan:
            raise FileNotFoundError(
                f"Faltan archivos del modelo en {carpeta}: {', '.join(faltan)}.\n"
                "Corre la sección 11 del notebook FairPlay_AI_Clasificador_Pares.ipynb y copia "
                "la carpeta salidas/paquete_app a esta ubicación.")

        art = cargar_artefacto(carpeta / "modelo_pares.joblib")
        self.modelo_A, self.modelo_B = art["modelo_A"], art.get("modelo_B")
        self.FEAT_A, self.FEAT_B = art["FEAT_A"], art["FEAT_B"]
        self.config = art.get("config", {})
        desconocidas = set(self.FEAT_A + self.FEAT_B) - set(SENALES)
        if desconocidas:
            raise ValueError(f"El modelo usa señales que la app no sabe calcular: {sorted(desconocidas)}. "
                             "Actualiza senales.py para que coincida con el notebook.")

        # El TF-IDF se recalcula (con caché) usando la misma configuración que el notebook
        self.tfidf = BuscadorTfidf(carpeta / "catalogo.parquet")
        self.df = self.tfidf.df
        E = np.load(carpeta / "emb_texto.npy").astype(np.float32)
        self.E = E
        self.senales = CalculadoraSenales(self.tfidf.X, E, self.df, joblib.load(carpeta / "imagenes.joblib"))
        self.k_vecinos = int(self.config.get("K_VECINOS", 10))
        self._indexar_imagenes()

    def _indexar_imagenes(self) -> None:
        """Junta los vectores CLIP de todas las imágenes en una matriz, para buscar por imagen.

        `self.imagenes` tiene una fila por imagen y `self.dueno_imagen` dice de qué juego es.
        Cada juego queda apuntando a su trozo de la matriz, así los vectores no se guardan dos veces.
        """
        img = self.senales.img
        trozos, dueno, partes, inicio = [], [], {}, 0
        for pos, x in enumerate(img):
            if x is None or id(x) in partes:       # sin imágenes, o el mismo appid repetido en el catálogo
                continue
            e = np.asarray(x["emb"], dtype=np.float32)
            partes[id(x)] = (x, inicio, inicio + len(e))
            trozos.append(e)
            dueno.extend([pos] * len(e))
            inicio += len(e)
        self.imagenes = np.vstack(trozos) if trozos else np.zeros((0, 0), dtype=np.float32)
        self.dueno_imagen = np.asarray(dueno, dtype=int)
        for x, ini, fin in partes.values():
            x["emb"] = self.imagenes[ini:fin]

    # ---- búsqueda ------------------------------------------------------------
    @property
    def usa_modelo_B(self) -> bool:
        return self.modelo_B is not None

    @property
    def modelos_disponibles(self) -> list[str]:
        """Modelos que trae el paquete, el que se usa por defecto primero."""
        return ["B", "A"] if self.usa_modelo_B else ["A"]

    def elegir_modelo(self, modelo: str | None = None) -> tuple[str, object, list[str]]:
        """(letra, modelo, señales) del modelo pedido. Sin pedir nada: el B si existe, si no el A."""
        letra = (modelo or self.modelos_disponibles[0]).strip().upper()
        if letra not in ("A", "B"):
            raise ValueError(f"Modelo desconocido: {modelo!r}. Usa 'A' o 'B'.")
        if letra == "B" and not self.usa_modelo_B:
            raise ValueError("Este paquete no trae Modelo B: faltan etiquetas humanas para entrenarlo.")
        return (letra, self.modelo_B, self.FEAT_B) if letra == "B" else (letra, self.modelo_A, self.FEAT_A)

    def probabilidad(self, pares: pd.DataFrame, modelo: str | None = None) -> np.ndarray:
        """Probabilidad de que el par merezca revisión según el modelo elegido (por defecto, el B si existe)."""
        _, m, feats = self.elegir_modelo(modelo)
        return m.predict_proba(pares[feats])[:, 1]

    def vecinos(self, q: int) -> list[int]:
        """Juegos que vale la pena comparar con q.

        Los K más parecidos por palabras (TF-IDF), los K más parecidos por significado y, además,
        los que tienen una imagen casi idéntica (hasta K). Sin lo último, un clon que reescribe la
        descripción pero reutiliza las capturas podía no aparecer nunca.
        """
        k = min(self.k_vecinos, len(self.df) - 1)
        s_tfidf = linear_kernel(self.tfidf.X[q], self.tfidf.X).ravel()
        s_emb = self.E @ self.E[q]
        s_tfidf[q] = s_emb[q] = -np.inf
        por_texto = set(np.argsort(-s_tfidf)[:k]) | set(np.argsort(-s_emb)[:k])
        return sorted(int(j) for j in por_texto | set(self.vecinos_imagen(q, k)))

    def vecinos_imagen(self, q: int, k: int | None = None,
                       umbral: float = UMBRAL_IMAGEN_IDENTICA) -> list[int]:
        """Hasta k juegos con alguna imagen casi idéntica a alguna de q, del más al menos parecido."""
        k = self.k_vecinos if k is None else k
        img = self.senales.img[q]
        if img is None or not len(self.imagenes) or k <= 0:
            return []
        s = (self.imagenes @ np.asarray(img["emb"], dtype=np.float32).T).max(axis=1)
        por_juego = np.full(len(self.df), -np.inf, dtype=np.float32)
        np.maximum.at(por_juego, self.dueno_imagen, s)
        por_juego[q] = -np.inf
        k = min(k, len(por_juego) - 1)
        top = np.argpartition(-por_juego, k)[:k] if k < len(por_juego) else np.arange(len(por_juego))
        top = top[np.argsort(-por_juego[top])]
        return [int(j) for j in top if por_juego[j] >= umbral]

    def candidatos(self, q: int, k: int = 10, modelo: str | None = None) -> pd.DataFrame:
        """Tabla de candidatos para el juego q, ordenada por probabilidad del modelo elegido.

        Además de las columnas visibles, incluye `pos` (posición en el catálogo) y
        `appid`, que usa la app para mostrar imágenes y explicar un par.
        """
        otros = self.vecinos(q)
        p = self.senales.calcular([q] * len(otros), otros)
        p["prob"] = self.probabilidad(p, modelo)
        p = p.sort_values(["prob", "tfidf_cos"], ascending=False).head(k)
        fecha = pd.to_datetime(self.df.loc[p["j"], "release_date"], errors="coerce")
        return pd.DataFrame({
            "Juego": self.df.loc[p["j"], "name"].to_numpy(),
            "Desarrollador": self.df.loc[p["j"], "developer"].fillna("").to_numpy(),
            "Fecha": fecha.dt.strftime("%Y-%m-%d").fillna("").to_numpy(),
            "Prob. revisar": p["prob"].round(2).to_numpy(),
            "Texto (palabras)": p["tfidf_cos"].round(2).to_numpy(),
            "Texto (significado)": p["emb_cos"].round(2).to_numpy(),
            "Imagen (CLIP)": p["img_cos"].round(2).to_numpy(),
            "Imagen idéntica": p["phash_sim"].round(2).to_numpy(),
            "Título": p["titulo_sim"].round(2).to_numpy(),
            "Géneros y tags": p["tags_jaccard"].round(2).to_numpy(),
            "Términos compartidos": [", ".join(self.tfidf.terminos_compartidos(self.tfidf.X[q], j, 5))
                                     for j in p["j"]],
            "pos": p["j"].to_numpy(),
            "appid": self.df.loc[p["j"], "appid"].to_numpy(),
        }).reset_index(drop=True)

    # ---- explicación ----------------------------------------------------------
    def explicar(self, a: int, b: int, modelo: str | None = None) -> tuple[float, pd.DataFrame]:
        """Probabilidad del par según el modelo elegido y cuánto empuja cada señal (positivo = hacia "revisar").

        Para una regresión logística, el aporte de cada señal es su valor estandarizado
        por su coeficiente: la suma de aportes (más el intercepto) da el logit.
        """
        fila = self.senales.calcular([a], [b])
        _, modelo, feats = self.elegir_modelo(modelo)
        prob = float(modelo.predict_proba(fila[feats])[0, 1])
        # El pipeline es: imputador (rellena vacíos y agrega indicadores) -> escalador -> logística
        nombres = modelo[:-1].get_feature_names_out(feats)
        imputado = modelo[0].transform(fila[feats])[0]
        z = modelo[:-1].transform(fila[feats])[0]
        original = fila.iloc[0]
        valores = []
        for n, v in zip(nombres, imputado):
            if n.startswith("missingindicator_"):
                valores.append("faltaba" if v == 1 else "no faltaba")
            elif pd.isna(original[n]):
                valores.append(f"sin dato (se usó {v:.2f})")
            else:
                valores.append(f"{float(original[n]):.3f}")
        aportes = pd.DataFrame({"Señal": [nombre_legible(n) for n in nombres], "Valor": valores,
                                "Aporte": (z * modelo[-1].coef_[0]).round(2)})
        aportes = aportes[aportes["Aporte"] != 0]
        aportes = aportes.loc[aportes["Aporte"].abs().sort_values(ascending=False).index]
        return prob, aportes.reset_index(drop=True)

    def url_imagen(self, pos: int) -> str | None:
        fila = self.df.iloc[pos]
        h = fila.get("header_image")
        if isinstance(h, str) and h.startswith("http"):
            return h
        a = pd.to_numeric(fila.get("appid"), errors="coerce")
        return URL_HEADER.format(appid=int(a)) if pd.notna(a) else None
