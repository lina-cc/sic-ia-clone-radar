"""Lógica de similitud TF-IDF entre videojuegos (sin interfaz).

La app (app.py) solo llama a esta clase. Así se puede cambiar 
Gradio por otra interfaz, o TF-IDF por embeddings, sin reescribir 
todo

Espera un parquet con, al menos, las columnas `name` y `text` 
(descripción ya limpia). Usa si existen: `genres`, `release date`,
`appid`, `n_resenas`.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

COLUMNAS_TABLA = ["Juego", "Puntaje", "Géneros", "Fecha", 
                  "Términos compartidos", "Steam"]

def limpiar(texto:str) -> str:
    """"Misma limpieza del notebook 01: entidades HTML, etiquetas 
    y espacios."""
    t = html.unescape(str(texto))
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).strip()

class BuscadorTfidf:
    def __init__(self, ruta_parquet:str | Path, 
                 usar_cache:bool = True):
        ruta = Path(ruta_parquet)
        if not ruta.exists():
            raise FileNotFoundError(
                f"No encuentro el archivo de datos: {ruta}\n"
                "Pide el archivo juegos_texto_en.parquet a quien " \
                "te envió la app y ponlo en la carpeta data/ (o indica" \
                "otra ruta con --datos)."
                "Si eres quien genera los datos, corre antes el " \
                "notebook 01_preprocesamiento." \
                    )
        self.df = pd.read_parquet(ruta).reset_index(drop=True)
        faltan = {"name", "text"} - set(self.df.columns)

        if faltan:
            raise ValueError(f"Al parquet le faltan las \
                             columnas:{sorted(faltan)}")

        self.tfidf, self.X = self._cargar_o_ajustar(ruta, usar_cache)
        assert self.X.shape[0] == len(self.df), "X y la tabla no coinciden"
        self.vocab = self.tfidf.get_feature_names_out()
        self._nombres = self.df["name"].astype(str)
        self._nombres_lower = self._nombres.str.lower()

    # ---- ajuste / caché ---------------------------------------------------
    def _cargar_o_ajustar(self, ruta: Path, usar_cache:bool):
        cache = ruta.with_name(ruta.stem + ".tfidf.joblib")
        if usar_cache and cache.exists() and cache.stat().st_mtime >= ruta.stat().st_mtime:
            tfidf, X = joblib.load(cache)
            if X.shape[0] == len(self.df):
                return tfidf, X
        tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                                min_df=2, max_features=50000, sublinear_tf=True)
        X = tfidf.fit_transform(self.df["text"].fillna(""))
        if usar_cache:
            joblib.dump((tfidf, X), cache)
        return tfidf, X

    # ---- búsqueda por nombre ----------------------------------------------
    def existe(self, nombre: str) -> bool:
        return bool((self._nombres_lower == nombre.strip().lower()).any())

    def sugerencias(self, fragmento: str, n: int = 8) -> list[str]:
        f = fragmento.strip().lower()
        if not f:
            return []
        return self._nombres[self._nombres_lower.str.contains(f, regex=False)].head(n).tolist()

    def buscar(self, nombre: str) -> int:
        """Posición del juego. Si hay homónimos, el más reseñado"""
        filas = self.df.index[self._nombres_lower == nombre.strip().lower()]
        if len(filas) == 0:
            raise KeyError(nombre)
        if "n_resenas" in self.df.columns and len(filas) > 1:
            return int(self.df.loc[filas, "n_resenas"].idxmax())
        return int(filas[0])

    def nombre(self, i: int) -> str:
        return str(self._nombres.iloc[i])

    # ---- similitud ---------------------------------------------------------
    def _vector_texto(self, texto:str):
        return self.tfidf.transform([limpiar(texto)])

    def _top(self, sims: np.ndarray, k: int, excluir: int | None = None) -> list[int]:
        orden = sims.argsort()[::-1]
        return [int(j) for j in orden if j!=excluir][:k]

    def similares(self, i:int, k: int = 10) -> pd.DataFrame:
        sims = linear_kernel(self.X[i], self.X).ravel()
        return self._tabla(self.X[i], sims, self._top(sims, k, excluir=i))

    def similares_texto(self, texto: str, k: int = 10) -> pd.DataFrame:
        v = self._vector_texto(texto)
        if v.nnz == 0:
            return pd.DataFrame(columns=COLUMNAS_TABLA) # ningún término conocido
        sims = linear_kernel(v, self.X).ravel()
        return self._tabla(v, sims, self._top(sims, k))

    # ---- evidencia ---------------------------------------------------------
    def _aportes(self, vec, j: int) -> np.ndarray:
        return vec.multiply(self.X[j]).toarray().ravel()

    def terminos_compartidos(self, vec,j: int, n: int = 5) -> list[str]:
        prod = self._aportes(vec, j)
        orden = prod.argsort()[::-1][:n]
        return [str(self.vocab[t]) for t in orden if prod[t] > 0] 
            
    def comparar(self, i: int, j: int, n: int = 15) -> tuple[float, pd.DataFrame]:
        """Puntaje entre dos juegos y los términos que más aportan."""
        score = float(linear_kernel(self.X[i], self.X[j])[0, 0])
        a = self.X[i].toarray().ravel()
        b = self.X[j].toarray().ravel()
        prod = a * b
        orden = prod.argsort()[::-1][:n]
        filas = [
            {"Término": str(self.vocab[t]), "Peso en A": round(float(a[t]), 3),
             "Peso en B": round(float(b[t]), 3), "Aporte": round(float(prod[t]), 4)}
            for t in orden if prod[t] > 0
        ]
        return score, pd.DataFrame(filas, columns=["Término", "Peso en A", "Peso en B", "Aporte"])
 
    # ---- formato de resultados -----------------------------------------
    def _tabla(self, vec, sims: np.ndarray, posiciones: list[int]) -> pd.DataFrame:
        filas = []
        for j in posiciones:
            fila = self.df.iloc[j]
            fecha = fila.get("release date", "")
            fecha = "" if pd.isna(fecha) else str(fecha)[:10]
            appid = fila.get("appid", "")
            steam = (f"[ver](https://store.steampowered.com/app/{int(float(appid))})"
                     if str(appid).replace(".0", "").isdigit() else "")
            filas.append({
                "Juego": str(fila["name"]),
                "Puntaje": round(float(sims[j]), 3),
                "Géneros": "" if pd.isna(fila.get("genres", "")) else str(fila.get("genres", "")),
                "Fecha": fecha,
                "Términos compartidos": ", ".join(self.terminos_compartidos(vec, j)),
                "Steam": steam,
            })
        return pd.DataFrame(filas, columns=COLUMNAS_TABLA)

