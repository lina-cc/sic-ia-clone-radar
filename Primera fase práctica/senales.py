"""Señales por par de juegos (sin interfaz y sin GPU).

Calcula, para pares de juegos (a, b), las mismas señales que el notebook
FairPlay_AI_Clasificador_Pares.ipynb (sección 3 y 4). El modelo entrenado
en el notebook espera exactamente estas columnas, con este mismo cálculo:

    tfidf_cos     mismas palabras en la descripción (TF-IDF + coseno)
    emb_cos       mismo significado en la descripción (embeddings + coseno)
    img_cos       par de imágenes más parecido según CLIP (máximo entre todas)
    phash_sim     imagen casi idéntica según el hash perceptual (1 = idéntica)
    titulo_sim    parecido de los títulos (token_set_ratio / 100)
    tags_jaccard  géneros y tags en común / géneros y tags en total
    log_dias      log(1 + días entre lanzamientos)
    mismo_dev     1 si el desarrollador coincide, 0 si no, vacío si no se sabe

Si se cambia el cálculo de una señal aquí, hay que cambiarlo también en el
notebook (y volver a entrenar), o el modelo recibirá números distintos a los
que vio al entrenar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

SENALES = ["tfidf_cos", "emb_cos", "img_cos", "phash_sim", "titulo_sim",
           "tags_jaccard", "log_dias", "mismo_dev"]


def conjunto_tags(generos, tags) -> frozenset[str]:
    """'Action, Indie' + 'Platformer' -> {'action', 'indie', 'platformer'}."""
    texto = f"{'' if pd.isna(generos) else generos}, {'' if pd.isna(tags) else tags}"
    return frozenset(t.strip().lower() for t in texto.split(",") if t.strip())


def jaccard(a: frozenset, b: frozenset) -> float:
    union = a | b
    return len(a & b) / len(union) if union else np.nan


def comparar_imagenes(img_a: dict | None, img_b: dict | None) -> tuple[float, float]:
    """(img_cos, phash_sim) entre dos juegos.

    Cada juego es un dict con "emb" (n_imagenes x d, vectores CLIP normalizados)
    y "hash" (n_imagenes x 64, bits del hash perceptual). Se comparan todas las
    imágenes de A contra todas las de B y se queda el mejor resultado.
    Si falta alguno de los dos, devuelve (NaN, NaN).
    """
    if img_a is None or img_b is None:
        return np.nan, np.nan
    S = np.asarray(img_a["emb"], dtype=np.float32) @ np.asarray(img_b["emb"], dtype=np.float32).T
    H = (np.asarray(img_a["hash"])[:, None, :] != np.asarray(img_b["hash"])[None, :, :]).sum(axis=2)
    return float(S.max()), 1 - float(H.min()) / 64


class CalculadoraSenales:
    """Guarda lo que se necesita del catálogo y calcula señales para muchos pares a la vez.

    X       matriz TF-IDF (scipy sparse, filas normalizadas), una fila por juego
    E       embeddings de texto normalizados (numpy, n_juegos x d)
    df      catálogo con columnas name, developer, release_date, genres, tags, appid
    imagenes dict appid -> {"emb", "hash"} (puede estar vacío)
    """

    def __init__(self, X, E, df: pd.DataFrame, imagenes: dict | None = None):
        if X.shape[0] != len(df) or E.shape[0] != len(df):
            raise ValueError(f"Tamaños distintos: TF-IDF {X.shape[0]}, embeddings {E.shape[0]}, "
                             f"catálogo {len(df)}. El catálogo y los embeddings deben venir del mismo paquete.")
        self.X = X
        self.E = np.asarray(E, dtype=np.float32)
        col = lambda c: df[c] if c in df.columns else pd.Series([None] * len(df))
        self.nombre = col("name").fillna("").astype(str).to_numpy()
        self.dev = col("developer").fillna("").astype(str).str.lower().str.strip().to_numpy()
        self.fecha = pd.to_datetime(col("release_date"), errors="coerce").to_numpy()
        self.tags = [conjunto_tags(g, t) for g, t in zip(col("genres"), col("tags"))]
        appids = pd.to_numeric(col("appid"), errors="coerce")
        imagenes = imagenes or {}
        self.img = [imagenes.get(int(a)) if pd.notna(a) else None for a in appids]

    def calcular(self, a, b) -> pd.DataFrame:
        """Señales para los pares (a[n], b[n]); a y b son posiciones en el catálogo."""
        a, b = np.asarray(a, dtype=int), np.asarray(b, dtype=int)
        out = pd.DataFrame({"i": a, "j": b})
        out["tfidf_cos"] = np.asarray(self.X[a].multiply(self.X[b]).sum(axis=1)).ravel()
        out["emb_cos"] = (self.E[a] * self.E[b]).sum(axis=1).astype(np.float64)
        imgs = [comparar_imagenes(self.img[x], self.img[y]) for x, y in zip(a, b)]
        out["img_cos"] = [r[0] for r in imgs]
        out["phash_sim"] = [r[1] for r in imgs]
        out["titulo_sim"] = [fuzz.token_set_ratio(self.nombre[x], self.nombre[y]) / 100 for x, y in zip(a, b)]
        out["tags_jaccard"] = [jaccard(self.tags[x], self.tags[y]) for x, y in zip(a, b)]
        dias = np.abs((pd.to_datetime(self.fecha[a]) - pd.to_datetime(self.fecha[b])).days.to_numpy(dtype=float))
        out["log_dias"] = np.log1p(dias)
        conocido = (self.dev[a] != "") & (self.dev[b] != "")
        out["mismo_dev"] = np.where(conocido, (self.dev[a] == self.dev[b]).astype(float), np.nan)
        return out
