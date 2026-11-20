"""¿Cuántos pares con la misma imagen llegan a ser candidatos en «Buscar un juego»?

Compara dos formas de elegir candidatos:
  * actual: los K más parecidos por palabras (TF-IDF) y por significado (embeddings), como hoy en la app;
  * con imagen: lo mismo, más los K más parecidos por imagen (CLIP, la mejor de sus imágenes);
  * con imagen casi idéntica: lo mismo, pero solo los vecinos por imagen con coseno ≥ UMBRAL_CLIP.

Para cada par con imagen casi idéntica (hash perceptual ≥ 0,9) se busca cada juego y se mira si el
otro aparece (a) entre los candidatos y (b) entre los 10 que la app muestra, ordenados por probabilidad.
También mide, en juegos al azar, cuánto cambian los 10 que se muestran.

Uso, desde la raíz del repositorio (necesita salidas/candidatos.parquet de ../casi_identicos/buscar.py):

    python experimentos/vecinos_imagen/medir.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "Primera fase práctica"))
from modelo import BuscadorModelo  # noqa: E402

MOSTRADOS = 10          # filas que muestra «Buscar un juego»
UMBRAL_HASH = 0.9
UMBRAL_TEXTO_DISTINTO = 0.5
UMBRAL_CLIP = 0.96      # el mismo de casi_identicos/buscar.py


class VecinosImagen:
    """Los juegos con la imagen más parecida a alguna imagen del juego consultado."""

    def __init__(self, img: list, n_juegos: int):
        filas, dueno = [], []
        for pos, x in enumerate(img):
            if x is not None:
                e = np.asarray(x["emb"], dtype=np.float32)
                filas.append(e)
                dueno.extend([pos] * len(e))
        self.I = np.vstack(filas)
        self.dueno = np.asarray(dueno)
        self.img = img
        self.n = n_juegos

    def __call__(self, q: int, k: int, umbral: float = -1.0) -> list[int]:
        if self.img[q] is None:
            return []
        s = (self.I @ np.asarray(self.img[q]["emb"], dtype=np.float32).T).max(axis=1)
        por_juego = np.full(self.n, -np.inf, dtype=np.float32)
        np.maximum.at(por_juego, self.dueno, s)
        por_juego[q] = -np.inf
        top = np.argsort(-por_juego)[:k]
        return [int(j) for j in top if por_juego[j] >= umbral]


def mostrados(M: BuscadorModelo, q: int, pool: list[int]) -> list[int]:
    """Los que vería la persona: el pool ordenado por probabilidad, como en candidatos()."""
    p = M.senales.calcular([q] * len(pool), pool)
    p["prob"] = M.probabilidad(p)
    return list(p.sort_values(["prob", "tfidf_cos"], ascending=False).head(MOSTRADOS)["j"])


def main():
    aqui = Path(__file__).parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", default=str(RAIZ / "Primera fase práctica" / "modelo"))
    ap.add_argument("--candidatos", default=str(aqui.parent / "casi_identicos" / "salidas" / "candidatos.parquet"))
    ap.add_argument("--al-azar", type=int, default=300, help="juegos al azar para medir cuánto cambia la lista")
    ap.add_argument("--salida", default=str(aqui / "salidas" / "resultados.json"))
    args = ap.parse_args()
    t0 = time.time()

    M = BuscadorModelo(args.modelo)
    pos = {int(a): i for i, a in enumerate(M.df["appid"])}
    vi = VecinosImagen(M.senales.img, len(M.df))
    k = M.k_vecinos

    c = pd.read_parquet(args.candidatos)
    c = c[c.phash_sim >= UMBRAL_HASH].copy()
    c["texto_distinto"] = c.tfidf_cos < UMBRAL_TEXTO_DISTINTO
    print(f"pares con imagen casi idéntica: {len(c)} (texto distinto: {int(c.texto_distinto.sum())})", flush=True)

    cache: dict[int, tuple] = {}

    def buscar(q: int):
        if q not in cache:
            actual = M.vecinos(q)
            con_img = sorted(set(actual) | set(vi(q, k)))
            con_ident = sorted(set(actual) | set(vi(q, k, UMBRAL_CLIP)))
            cache[q] = (actual, mostrados(M, q, actual), con_img, mostrados(M, q, con_img),
                        con_ident, mostrados(M, q, con_ident))
        return cache[q]

    filas = []
    for n, r in enumerate(c.itertuples()):
        a, b = pos[int(r.appid_a)], pos[int(r.appid_b)]
        for q, otro in ((a, b), (b, a)):           # se puede buscar cualquiera de los dos juegos
            actual, vis_actual, con_img, vis_img, con_ident, vis_ident = buscar(q)
            filas.append({"texto_distinto": r.texto_distinto, "mismo_dev": r.mismo_dev,
                          "pool_actual": otro in actual, "visto_actual": otro in vis_actual,
                          "pool_imagen": otro in con_img, "visto_imagen": otro in vis_img,
                          "pool_identica": otro in con_ident, "visto_identica": otro in vis_ident})
        if n % 100 == 0:
            print(f"  {n}/{len(c)}  {time.time() - t0:.0f} s", flush=True)
    f = pd.DataFrame(filas)

    def resumen(g: pd.DataFrame) -> dict:
        return {"busquedas": len(g), **{col: round(float(g[col].mean()), 3) for col in
                                         ("pool_actual", "visto_actual", "pool_imagen", "visto_imagen",
                                                     "pool_identica", "visto_identica")}}

    res = {"todos": resumen(f), "texto_distinto": resumen(f[f.texto_distinto]),
           "estudios_distintos": resumen(f[f.mismo_dev == 0])}

    # ¿Cuánto cambia la lista que se muestra en una búsqueda cualquiera?
    rng = np.random.default_rng(2026)
    con_imagen = [i for i, x in enumerate(M.senales.img) if x is not None]
    nuevos, nuevos_ident, tiempos = [], [], []
    for q in rng.choice(con_imagen, size=args.al_azar, replace=False):
        t = time.time()
        vi(int(q), k)
        tiempos.append(time.time() - t)
        _, vis_actual, _, vis_img, _, vis_ident = buscar(int(q))
        nuevos.append(len(set(vis_img) - set(vis_actual)))
        nuevos_ident.append(len(set(vis_ident) - set(vis_actual)))
    res["al_azar"] = {"juegos": args.al_azar, "nuevos_en_los_10_promedio": round(float(np.mean(nuevos)), 2),
                      "busquedas_sin_cambios": round(float(np.mean(np.array(nuevos) == 0)), 3),
                      "identica_nuevos_en_los_10_promedio": round(float(np.mean(nuevos_ident)), 2),
                      "identica_busquedas_sin_cambios": round(float(np.mean(np.array(nuevos_ident) == 0)), 3),
                      "segundos_extra_por_busqueda": round(float(np.median(tiempos)), 3)}

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))
    print(f"listo en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
