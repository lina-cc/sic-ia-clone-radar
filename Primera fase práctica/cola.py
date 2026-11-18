"""Cola de revisión: entrega pares de juegos uno a uno para etiquetarlos sin tener que buscar.

Cómo se arma la cola
--------------------
1. Se toman los juegos del catálogo con cierta cantidad de reseñas (los más conocidos) y se
   desordenan con una semilla fija: todas las personas ven la misma lista.
2. Cada persona parte en un punto distinto de esa lista (según su nombre), para no repetir
   el trabajo de otra.
3. Para cada juego se piden los candidatos del modelo y se elige uno según una estrategia que
   va rotando (ver ESTRATEGIAS). Así no se etiqueta solo lo que el modelo pone primero, que
   haría ver al modelo mejor de lo que es.
4. Los pares que alguien del equipo ya etiquetó se saltan.

Ejemplo
-------
    cola = ColaRevision(modelo, Path("casos/casos_guardados.csv"))
    par = cola.siguiente(cola.inicio("Sergio"))
    par["a"]["nombre"], par["b"]["nombre"]   # ('Stardew Valley', 'Cornucopia®')
    cola.progreso("Sergio")                  # {'tuyos': 12, 'meta': 30, 'positivos': 4, ...}
"""
from __future__ import annotations

import zlib
from pathlib import Path

import numpy as np
import pandas as pd

# Qué candidato se muestra de cada juego. Se elige según la posición del juego en la cola:
#   "modelo": el que el modelo considera más probable
#   "texto":  el más parecido por palabras (lo que encontraría la línea base TF-IDF)
#   "bajo":   el que el modelo considera menos probable (control: debería ser "No similar")
ESTRATEGIAS = ["modelo", "texto", "modelo", "bajo"]

META_POR_PERSONA = 30     # pares que se le piden a cada integrante
MINIMO_POR_CLASE = 10     # el notebook entrena el Modelo B con al menos 10 positivos y 10 negativos
POSITIVAS = {"posible copia"}
NEGATIVAS = {"similar", "no similar"}
MAX_INTENTOS = 40         # juegos que se prueban antes de decir "no quedan pares"


def _par(a: str, b: str) -> frozenset:
    """Clave de un par sin importar el orden: (A, B) y (B, A) son el mismo par."""
    return frozenset((str(a), str(b)))


def ficha(M, pos: int) -> dict:
    """Lo que se muestra de un juego: nombre, estudio, fecha, géneros, descripción, imagen y enlace.

    `M` es el BuscadorModelo y `pos` la posición del juego en su catálogo.
    """
    fila = M.df.iloc[pos]
    fecha = pd.to_datetime(fila.get("release_date"), errors="coerce")
    appid = pd.to_numeric(fila.get("appid"), errors="coerce")
    texto = fila.get("text")
    return {
        "nombre": M.tfidf.nombre(pos),
        "desarrollador": fila.get("developer") if isinstance(fila.get("developer"), str) else "",
        "fecha": fecha.strftime("%Y-%m-%d") if pd.notna(fecha) else "",
        "generos": fila.get("genres") if isinstance(fila.get("genres"), str) else "",
        "texto": texto if isinstance(texto, str) else "",
        "imagen": M.url_imagen(pos),
        "enlace": f"https://store.steampowered.com/app/{int(appid)}" if pd.notna(appid) else None,
    }


class ColaRevision:
    def __init__(self, modelo, ruta_casos: str | Path, semilla: int = 2026, min_resenas: int = 100):
        self.M = modelo
        self.ruta_casos = Path(ruta_casos)
        df = modelo.df
        resenas = (pd.to_numeric(df["n_resenas"], errors="coerce").fillna(0).to_numpy()
                   if "n_resenas" in df.columns else np.zeros(len(df)))
        conocidos = np.flatnonzero(resenas >= min_resenas)
        if len(conocidos) < 50:          # catálogos chicos (por ejemplo, el de los tests): se usan todos
            conocidos = np.arange(len(df))
        self.orden = np.random.default_rng(semilla).permutation(conocidos)

    # ---- casos ya guardados ----------------------------------------------------
    def casos(self) -> pd.DataFrame:
        """Los casos guardados por la app (tabla vacía si todavía no hay ninguno)."""
        columnas = ["anotador", "consulta", "juego_comparado", "etiqueta"]
        if not self.ruta_casos.exists():
            return pd.DataFrame(columns=columnas)
        try:
            c = pd.read_csv(self.ruta_casos, encoding="utf-8-sig", dtype=str).fillna("")
        except (pd.errors.EmptyDataError, pd.errors.ParserError):
            return pd.DataFrame(columns=columnas)
        return c if set(columnas) <= set(c.columns) else pd.DataFrame(columns=columnas)

    def progreso(self, anotador: str | None) -> dict:
        """Cuánto lleva esta persona y cuánto le falta al equipo para entrenar el Modelo B.

        Un par etiquetado varias veces cuenta una sola vez para el equipo (vale la última etiqueta).
        """
        c = self.casos()
        nombre = (anotador or "").strip().lower() or "anónimo"
        etiqueta = c["etiqueta"].str.strip().str.lower()
        utiles = c[etiqueta.isin(POSITIVAS | NEGATIVAS)]
        tuyos = int((utiles["anotador"].str.strip().str.lower() == nombre).sum())
        ultima = {_par(r.consulta, r.juego_comparado): r.etiqueta.strip().lower() for r in utiles.itertuples()}
        positivos = sum(e in POSITIVAS for e in ultima.values())
        negativos = len(ultima) - positivos
        return {"tuyos": tuyos, "meta": META_POR_PERSONA, "positivos": positivos, "negativos": negativos,
                "minimo": MINIMO_POR_CLASE,
                "listo": positivos >= MINIMO_POR_CLASE and negativos >= MINIMO_POR_CLASE}

    # ---- la cola ---------------------------------------------------------------
    def inicio(self, anotador: str | None) -> int:
        """Punto de partida de una persona: depende de su nombre y es siempre el mismo."""
        nombre = (anotador or "").strip().lower() or "anónimo"
        return zlib.crc32(nombre.encode("utf-8")) % len(self.orden)

    def siguiente(self, cursor: int, saltados=()) -> dict | None:
        """El próximo par sin etiquetar a partir de `cursor`, o None si no se encontró ninguno.

        `saltados` son los pares que la persona dejó pasar en esta sesión (lista de [a, b]).
        El resultado trae `cursor` ya avanzado, para pedir el siguiente.
        """
        c = self.casos()
        hechos = {_par(r.consulta, r.juego_comparado) for r in c.itertuples()}
        hechos |= {_par(*s) for s in saltados}
        n = len(self.orden)
        for paso in range(min(n, MAX_INTENTOS)):
            i = (cursor + paso) % n
            q = int(self.orden[i])
            res = self.M.candidatos(q, 20)
            if res.empty:
                continue
            estrategia = ESTRATEGIAS[i % len(ESTRATEGIAS)]
            if estrategia == "texto" and res["Texto (palabras)"].notna().any():
                fila = res.loc[res["Texto (palabras)"].idxmax()]
            elif estrategia == "bajo":
                fila = res.iloc[-1]
            else:
                fila = res.iloc[0]
            a, b = self.M.tfidf.nombre(q), str(fila["Juego"])
            if a == b or _par(a, b) in hechos:
                continue
            return {"cursor": i + 1, "q": q, "pos": int(fila["pos"]), "prob": float(fila["Prob. revisar"]),
                    "estrategia": estrategia, "a": ficha(self.M, q), "b": ficha(self.M, int(fila["pos"]))}
        return None
