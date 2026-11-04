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


def nombre_legible(senal: str) -> str:
    """'missingindicator_img_cos' -> 'Sin dato: Imágenes parecidas (CLIP)'."""
    if senal.startswith("missingindicator_"):
        base = senal.removeprefix("missingindicator_")
        return f"Sin dato: {NOMBRES_SENALES.get(base, base)}"
    return NOMBRES_SENALES.get(senal, senal)


COLUMNAS_CANDIDATOS = ["Juego", "Desarrollador", "Fecha", "Prob. revisar", "Texto (palabras)",
                       "Texto (significado)", "Imagen (CLIP)", "Imagen idéntica", "Título", "Términos compartidos"]


class BuscadorModelo:
    def __init__(self, carpeta: str | Path):
        carpeta = Path(carpeta)
        faltan = [f for f in ARCHIVOS if not (carpeta / f).exists()]
        if faltan:
            raise FileNotFoundError(
                f"Faltan archivos del modelo en {carpeta}: {', '.join(faltan)}.\n"
                "Corre la sección 11 del notebook FairPlay_AI_Clasificador_Pares.ipynb y copia "
                "la carpeta salidas/paquete_app a esta ubicación.")

        art = joblib.load(carpeta / "modelo_pares.joblib")
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

    # ---- búsqueda ------------------------------------------------------------
    @property
    def usa_modelo_B(self) -> bool:
        return self.modelo_B is not None

    def probabilidad(self, pares: pd.DataFrame) -> np.ndarray:
        """Probabilidad de que el par merezca revisión: Modelo B si existe, si no Modelo A."""
        if self.usa_modelo_B:
            return self.modelo_B.predict_proba(pares[self.FEAT_B])[:, 1]
        return self.modelo_A.predict_proba(pares[self.FEAT_A])[:, 1]

    def vecinos(self, q: int) -> list[int]:
        """Los K más parecidos por palabras (TF-IDF) unidos a los K más parecidos por significado."""
        k = min(self.k_vecinos, len(self.df) - 1)
        s_tfidf = linear_kernel(self.tfidf.X[q], self.tfidf.X).ravel()
        s_emb = self.E @ self.E[q]
        s_tfidf[q] = s_emb[q] = -np.inf
        return sorted(set(np.argsort(-s_tfidf)[:k]) | set(np.argsort(-s_emb)[:k]))

    def candidatos(self, q: int, k: int = 10) -> pd.DataFrame:
        """Tabla de candidatos para el juego q, ordenada por probabilidad del modelo.

        Además de las columnas visibles, incluye `pos` (posición en el catálogo) y
        `appid`, que usa la app para mostrar imágenes y explicar un par.
        """
        otros = self.vecinos(q)
        p = self.senales.calcular([q] * len(otros), otros)
        p["prob"] = self.probabilidad(p)
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
            "Términos compartidos": [", ".join(self.tfidf.terminos_compartidos(self.tfidf.X[q], j, 5))
                                     for j in p["j"]],
            "pos": p["j"].to_numpy(),
            "appid": self.df.loc[p["j"], "appid"].to_numpy(),
        }).reset_index(drop=True)

    # ---- explicación ----------------------------------------------------------
    def explicar(self, a: int, b: int) -> tuple[float, pd.DataFrame]:
        """Probabilidad del par y cuánto empuja cada señal (positivo = hacia "revisar").

        Para una regresión logística, el aporte de cada señal es su valor estandarizado
        por su coeficiente: la suma de aportes (más el intercepto) da el logit.
        """
        fila = self.senales.calcular([a], [b])
        modelo, feats = ((self.modelo_B, self.FEAT_B) if self.usa_modelo_B else (self.modelo_A, self.FEAT_A))
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
