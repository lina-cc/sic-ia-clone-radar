"""Filtra los candidatos de buscar.py y arma un Excel para etiquetar.

Uso, desde la raíz del repositorio:

    python experimentos/casi_identicos/lista.py

Lee salidas/candidatos.parquet y deja salidas/pares_casi_identicos.xlsx (no se sube al
repositorio: tiene datos de Steam). La etiqueta la decide una persona.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

MIRAR, SERIE, MISMA_OBRA = "1 · Mirar con atención", "2 · Misma plantilla o serie", "3 · Probablemente la misma obra"
MAX_POR_JUEGO = 2        # hay familias enormes (el mismo juego republicado decenas de veces)
MIN_LARGO = 300          # caracteres: con descripciones cortas, «texto igual» no dice mucho


def filtrar(p: pd.DataFrame) -> pd.DataFrame:
    """Pares de estudios claramente distintos con texto o imagen casi idénticos, agrupados y ordenados.

    * Estudios distintos: `mismo_dev == 0` y nombres poco parecidos (`dev_sim < 0.6`).
    * Texto casi idéntico: `tfidf_cos` y `emb_cos` ≥ 0.9 y ambas descripciones de `MIN_LARGO` o más.
    * Imagen casi idéntica: `phash_sim` ≥ 0.9.
    * Grupo según el parecido de los títulos: casi iguales suele ser la misma obra (demo, VR, otro editor).
    * Cada juego entra en `MAX_POR_JUEGO` pares como máximo.
    """
    d = p[(p["mismo_dev"] == 0) & (p["dev_sim"] < 0.6)].copy()
    texto = ((d.tfidf_cos >= 0.9) & (d.emb_cos >= 0.9) & (d.largo_a >= MIN_LARGO) & (d.largo_b >= MIN_LARGO))
    imagen = d.phash_sim >= 0.9
    d = d[texto | imagen].copy()
    d["texto_igual_flag"], d["imagen_igual_flag"] = texto[d.index], imagen[d.index]
    d["grupo"] = [MISMA_OBRA if t >= 0.8 else (SERIE if t >= 0.6 else MIRAR) for t in d.titulo_sim]
    d["orden"] = d.grupo.map({MIRAR: 0, SERIE: 1, MISMA_OBRA: 2})
    d["fuerza"] = d.imagen_igual_flag.astype(int) + d.texto_igual_flag.astype(int)
    d["res"] = d[["resenas_a", "resenas_b"]].max(axis=1)
    d = d.sort_values(["orden", "fuerza", "res"], ascending=[True, False, False])
    usos, filas = Counter(), []
    for r in d.itertuples():
        if usos[r.appid_a] < MAX_POR_JUEGO and usos[r.appid_b] < MAX_POR_JUEGO:
            usos[r.appid_a] += 1
            usos[r.appid_b] += 1
            filas.append(r.Index)
    return d.loc[filas].reset_index(drop=True)


def motivo(grupo: str, texto: bool, imagen: bool) -> str:
    que = ("la misma imagen y el mismo texto" if texto and imagen else
           "la misma imagen de portada o captura, con otro texto" if imagen else "la descripción casi idéntica")
    if grupo == MISMA_OBRA:
        return f"Títulos casi iguales y {que}: suele ser demo, prólogo, versión VR o cambio de editor."
    if grupo == SERIE:
        return f"Títulos de la misma serie y {que}: revisar si los dos estudios son en realidad el mismo."
    return f"Nombres distintos, estudios distintos y {que}."


AYUDA = [
    "Pares del catálogo con la descripción o una imagen casi idéntica, publicados por estudios con nombres distintos.",
    "Salen de una búsqueda automática: son CANDIDATOS. La etiqueta la decide la persona que revisa.",
    "",
    "1. Repartan las filas y escriban su nombre en «responsable». Empiecen por el grupo 1.",
    "2. Abran la app, pestaña «Comparar dos juegos», y escriban los dos nombres (o abran url_a y url_b).",
    "3. Elijan la etiqueta en la app y anótenla en «etiqueta_en_la_app».",
    "",
    "Grupo 1 · Mirar con atención: nombres y estudios distintos con el mismo material.",
    "Grupo 2 · Misma plantilla o serie: si es el mismo autor con otro nombre, es «Similar».",
    "Grupo 3 · Probablemente la misma obra: demo, prólogo, versión VR o cambio de editor. Casi siempre «Similar».",
    "",
    "Que dos estudios tengan nombres distintos no prueba que sean personas distintas: revisen el editor en Steam.",
    "Privado: contiene datos de Steam. No subir al repositorio.",
]


def main():
    aqui = Path(__file__).parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default=str(aqui / "salidas" / "candidatos.parquet"))
    ap.add_argument("--salida", default=str(aqui / "salidas" / "pares_casi_identicos.xlsx"))
    args = ap.parse_args()

    d = filtrar(pd.read_parquet(args.entrada))
    d["por_que_aparece"] = [motivo(g, t, i) for g, t, i in zip(d.grupo, d.texto_igual_flag, d.imagen_igual_flag)]
    d["n"] = d.index + 1
    d["responsable"] = d["etiqueta_en_la_app"] = ""
    for lado in "ab":
        d[f"url_{lado}"] = "https://store.steampowered.com/app/" + d[f"appid_{lado}"].astype(int).astype(str)
        d[f"anio_{lado}"] = d[f"fecha_{lado}"].str[:4]
    d = d.rename(columns={"dev_a": "estudio_a", "dev_b": "estudio_b", "tfidf_cos": "texto_igual",
                          "phash_sim": "imagen_igual", "titulo_sim": "titulo_parecido"})
    cols = ["n", "juego_a", "juego_b", "grupo", "por_que_aparece", "responsable", "etiqueta_en_la_app",
            "estudio_a", "estudio_b", "anio_a", "anio_b", "resenas_a", "resenas_b",
            "texto_igual", "imagen_igual", "titulo_parecido", "prob_modelo", "url_a", "url_b"]
    for c in ("texto_igual", "imagen_igual", "titulo_parecido", "prob_modelo"):
        d[c] = d[c].round(2)
    with pd.ExcelWriter(args.salida) as w:
        d[cols].to_excel(w, sheet_name="Pares para etiquetar", index=False)
        pd.DataFrame({"Cómo usar esta lista": AYUDA}).to_excel(w, sheet_name="Cómo usar", index=False)
    print(f"{len(d)} pares en {args.salida}")
    print(d.grupo.value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()
