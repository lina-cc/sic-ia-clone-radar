"""Pares de estudios distintos que dicen lo mismo con otras palabras: ¿traducciones o reescrituras?

Toma los candidatos de ../casi_identicos/buscar.py y se queda con los pares de estudios claramente
distintos cuya descripción tiene el mismo significado (embeddings ≥ 0,9) pero comparte pocas palabras
(TF-IDF < 0,5). Adivina el idioma de cada descripción con una regla simple y arma un Excel para
revisarlos a mano.

Uso, desde la raíz del repositorio:

    python experimentos/descripciones_traducidas/revisar.py

Deja salidas/pares_para_revisar.xlsx (no se sube: tiene textos de Steam) y salidas/resumen.json.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
UMBRAL_SIGNIFICADO = 0.9
UMBRAL_PALABRAS = 0.5

# Palabras muy frecuentes de cada idioma: alcanzan para distinguir idiomas en textos largos
FRECUENTES = {
    "inglés": {"the", "and", "of", "to", "you", "your", "in", "is", "with", "for", "a", "an", "game", "can"},
    "español": {"el", "la", "de", "que", "y", "los", "las", "en", "un", "una", "con", "para", "tu", "juego"},
    "portugués": {"o", "a", "de", "que", "e", "os", "as", "em", "um", "uma", "com", "para", "você", "jogo"},
    "francés": {"le", "la", "les", "de", "des", "et", "un", "une", "vous", "votre", "dans", "pour", "jeu"},
    "alemán": {"der", "die", "das", "und", "du", "ein", "eine", "mit", "ist", "zu", "den", "nicht", "spiel"},
    "italiano": {"il", "la", "di", "che", "e", "un", "una", "per", "con", "gioco", "del", "della", "sono"},
    "ruso": {"и", "в", "на", "не", "с", "что", "ты", "по", "игра", "для", "это", "из", "как"},
}
_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def idioma(texto: str) -> str:
    """Idioma probable de un texto: por alfabeto si no es latino, y por palabras frecuentes si lo es.

    >>> idioma("Explore the world and fight with your friends")
    'inglés'
    """
    t = texto or ""
    letras = [ch for ch in t if ch.isalpha()]
    if not letras:
        return "sin texto"
    def frac(desde, hasta):
        return sum(desde <= ch <= hasta for ch in letras) / len(letras)
    if frac("぀", "ヿ") > 0.05:
        return "japonés"
    if frac("가", "힯") > 0.2:
        return "coreano"
    if frac("一", "鿿") > 0.2:
        return "chino"
    palabras = [p.lower() for p in _PALABRA.findall(t)]
    puntos = {k: sum(p in v for p in palabras) for k, v in FRECUENTES.items()}
    mejor = max(puntos, key=puntos.get)
    return mejor if puntos[mejor] >= 3 else "no se sabe"


def elegir(c: pd.DataFrame) -> pd.DataFrame:
    """Pares de estudios claramente distintos con el mismo significado y pocas palabras en común."""
    return c[(c.mismo_dev == 0) & (c.dev_sim < 0.6) & (c.emb_cos >= UMBRAL_SIGNIFICADO)
             & (c.tfidf_cos < UMBRAL_PALABRAS)].copy()


def main():
    aqui = Path(__file__).parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidatos", default=str(aqui.parent / "casi_identicos" / "salidas" / "candidatos.parquet"))
    ap.add_argument("--catalogo", default=str(RAIZ / "Primera fase práctica" / "modelo" / "catalogo.parquet"))
    ap.add_argument("--salidas", default=str(aqui / "salidas"))
    args = ap.parse_args()

    d = elegir(pd.read_parquet(args.candidatos))
    texto = pd.read_parquet(args.catalogo, columns=["appid", "text"]).set_index("appid")["text"].fillna("")
    for lado in "ab":
        d[f"texto_{lado}"] = d[f"appid_{lado}"].map(texto).fillna("")
        d[f"idioma_{lado}"] = d[f"texto_{lado}"].map(idioma)
        d[f"url_{lado}"] = "https://store.steampowered.com/app/" + d[f"appid_{lado}"].astype(int).astype(str)
    d["idiomas"] = ["distintos" if a != b and "no se sabe" not in (a, b) else
                    ("iguales" if a == b and a != "no se sabe" else "no se sabe")
                    for a, b in zip(d.idioma_a, d.idioma_b)]
    d["que_es"] = ""             # a mano: traducción, reescritura, plantilla, mismo autor, otro
    d["etiqueta_en_la_app"] = ""
    d = d.sort_values(["idiomas", "emb_cos"], ascending=[True, False])

    resumen = {
        "pares": len(d),
        "idiomas": d.idiomas.value_counts().to_dict(),
        "combinaciones": (d.idioma_a + " · " + d.idioma_b).value_counts().head(10).to_dict(),
        "prob_modelo_mediana": round(float(d.prob_modelo.median()), 2) if len(d) else None,
    }
    salidas = Path(args.salidas)
    salidas.mkdir(parents=True, exist_ok=True)
    cols = ["juego_a", "juego_b", "idioma_a", "idioma_b", "idiomas", "que_es", "etiqueta_en_la_app",
            "emb_cos", "tfidf_cos", "img_cos", "phash_sim", "titulo_sim", "prob_modelo",
            "dev_a", "dev_b", "texto_a", "texto_b", "url_a", "url_b"]
    with pd.ExcelWriter(salidas / "pares_para_revisar.xlsx") as w:
        d[cols].round(2).to_excel(w, sheet_name="Pares", index=False)
    (salidas / "resumen.json").write_text(json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
