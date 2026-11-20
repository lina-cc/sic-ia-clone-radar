"""Busca en todo el catálogo pares con la descripción o una imagen casi idéntica.

Son candidatos para que una persona los revise, no etiquetas ni acusaciones.

Uso, desde la raíz del repositorio y con el paquete del modelo en "Primera fase práctica/modelo":

    python experimentos/casi_identicos/buscar.py

Deja experimentos/casi_identicos/salidas/candidatos.parquet (no se sube al repositorio).
Sin GPU tarda unos 6 minutos con todo el catálogo.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "Primera fase práctica"))
from modelo import BuscadorModelo  # noqa: E402

UMBRAL_TEXTO = 0.92    # coseno de embeddings de texto
UMBRAL_IMAGEN = 0.96   # coseno de CLIP entre dos imágenes cualesquiera de los juegos
K = 4                  # vecinos que se miran por fila


def vecinos(A: np.ndarray, dueno: np.ndarray, umbral: float, k: int = K, lote: int = 500) -> set[tuple[int, int]]:
    """Pares (i, j), con i < j, de dueños distintos cuyo coseno supera el umbral.

    A tiene una fila normalizada por vector; dueno[f] es el juego al que pertenece la fila f
    (un juego puede tener varias imágenes).
    """
    pares = set()
    for ini in range(0, len(A), lote):
        sim = A[ini:ini + lote] @ A.T
        filas = np.arange(sim.shape[0])
        sim[filas, ini + filas] = -1
        top = np.argpartition(-sim, k, axis=1)[:, :k]
        for f in filas:
            for c in top[f]:
                a, b = int(dueno[ini + f]), int(dueno[c])
                if sim[f, c] >= umbral and a != b:
                    pares.add((min(a, b), max(a, b)))
    return pares


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", default=str(RAIZ / "Primera fase práctica" / "modelo"))
    ap.add_argument("--salida", default=str(Path(__file__).parent / "salidas" / "candidatos.parquet"))
    args = ap.parse_args()
    t0 = time.time()

    M = BuscadorModelo(args.modelo)
    df, S = M.df, M.senales
    print("juegos:", len(df), flush=True)

    p_texto = vecinos(S.E, np.arange(len(df)), UMBRAL_TEXTO)
    print(f"por texto: {len(p_texto)} pares ({time.time() - t0:.0f} s)", flush=True)

    filas, dueno = [], []
    for pos, img in enumerate(S.img):
        if img is not None:
            e = np.asarray(img["emb"], dtype=np.float32)
            filas.append(e)
            dueno.extend([pos] * len(e))
    p_img = vecinos(np.vstack(filas), np.asarray(dueno), UMBRAL_IMAGEN)
    print(f"por imagen: {len(p_img)} pares ({time.time() - t0:.0f} s)", flush=True)

    todos = sorted(p_texto | p_img)
    a = np.array([p[0] for p in todos])
    b = np.array([p[1] for p in todos])
    out = pd.concat([S.calcular(a[i:i + 20000], b[i:i + 20000]) for i in range(0, len(a), 20000)],
                    ignore_index=True)
    out["prob_modelo"] = M.probabilidad(out)
    out["dev_sim"] = [fuzz.token_set_ratio(S.dev[x], S.dev[y]) / 100 for x, y in zip(a, b)]
    for lado, pos in (("a", a), ("b", b)):
        d = df.iloc[pos].reset_index(drop=True)
        out[f"appid_{lado}"] = d["appid"].to_numpy()
        out[f"juego_{lado}"] = d["name"].to_numpy()
        out[f"dev_{lado}"] = d["developer"].to_numpy()
        out[f"fecha_{lado}"] = d["release_date"].astype(str).str[:10].to_numpy()
        out[f"resenas_{lado}"] = d["n_resenas"].to_numpy()
        out[f"largo_{lado}"] = d["text"].fillna("").str.len().to_numpy()

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(salida)
    print(f"listo: {len(out)} candidatos en {salida} ({time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
