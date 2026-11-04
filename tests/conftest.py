"""Configuración común de los tests.

La app vive en la carpeta "Primera fase práctica", que no es un paquete de Python
(tiene espacios y tilde en el nombre). Para poder hacer `import similitud` y
`import app` desde los tests, se agrega esa carpeta al path de importación.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

CARPETA_APP = Path(__file__).resolve().parents[1] / "Primera fase práctica"
sys.path.insert(0, str(CARPETA_APP))


@pytest.fixture
def ruta_parquet(tmp_path: Path) -> Path:
    """Catálogo mínimo con un clon evidente, un par del mismo género y juegos sin relación.

    Las palabras se repiten en al menos dos descripciones porque el TF-IDF de la app
    usa min_df=2 (ignora términos que aparecen en un solo juego).
    """
    juegos = pd.DataFrame({
        "name": ["Escape the Walls", "Escape Walls Obby", "Farm Tycoon", "My Farm Empire",
                 "Space Miner", "Racing Legends", "Racing Legends"],
        "text": [
            "escape the closing walls dodge obstacles and survive until the exit",
            "escape the closing walls dodge obstacles and survive until the exit fast",
            "build your farm grow crops sell products and hire helpers",
            "build a farm empire grow crops and sell products",
            "mine asteroids sell minerals and upgrade your ship to survive",
            "race cars upgrade your ship engine and dodge obstacles",
            "race cars on city tracks and upgrade engine",
        ],
        "appid": [1, 2, 3, 4, 5, 6, 7],
        "genres": ["Action", "Action", "Simulation", "Simulation", "Simulation", "Racing", "Racing"],
        "release date": pd.to_datetime(["2026-10-14", "2026-10-16", "2020-01-01", "2021-05-05",
                                        "2019-03-03", "2018-07-07", "2022-02-02"]),
        "n_resenas": [500, 3, 900, 40, 10, 5, 800],
    })
    ruta = tmp_path / "juegos.parquet"
    juegos.to_parquet(ruta)
    return ruta


def _pipeline_logistica():
    """Mismo tipo de modelo que entrena el notebook (sección 6)."""
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                         StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=2000))


@pytest.fixture
def paquete_modelo(tmp_path: Path, ruta_parquet: Path) -> Path:
    """Paquete como el que exporta la sección 11 del notebook, pero diminuto.

    - catálogo: los 7 juegos de `ruta_parquet`
    - embeddings de texto: hashing de la descripción (parecidos si el texto se parece)
    - imágenes: Escape the Walls y su clon comparten una imagen idéntica; Farm Tycoon
      tiene otra; el resto no tiene imágenes (para probar las señales vacías)
    - modelos A y B: entrenados con datos aleatorios donde "revisar" = texto e imagen altos
    """
    import joblib
    from sklearn.feature_extraction.text import HashingVectorizer

    carpeta = tmp_path / "modelo"
    carpeta.mkdir()
    cat = pd.read_parquet(ruta_parquet).rename(columns={"release date": "release_date"})
    cat["developer"] = ["Pandorio", "Copion", "Granja SA", "Granja SA", "", "Autos", "Autos"]
    cat["tags"] = ["Escape, Obby", "Escape, Obby", "Farming", "Farming", "", "Cars", "Cars"]
    cat.to_parquet(carpeta / "catalogo.parquet", index=False)

    E = HashingVectorizer(n_features=64, alternate_sign=False).transform(cat["text"]).toarray()
    E = E / np.linalg.norm(E, axis=1, keepdims=True)
    np.save(carpeta / "emb_texto.npy", E.astype(np.float16))

    rng = np.random.default_rng(0)
    comun = rng.normal(size=(1, 16))
    comun /= np.linalg.norm(comun)
    bits = rng.random((1, 64)) > 0.5
    otra = rng.normal(size=(1, 16))
    otra /= np.linalg.norm(otra)
    joblib.dump({1: {"emb": comun, "hash": bits}, 2: {"emb": comun, "hash": bits},
                 3: {"emb": otra, "hash": ~bits}}, carpeta / "imagenes.joblib")

    FEAT_A = ["img_cos", "phash_sim", "titulo_sim", "tags_jaccard", "log_dias"]
    FEAT_B = ["tfidf_cos", "emb_cos"] + FEAT_A + ["mismo_dev"]
    X = pd.DataFrame(rng.random((300, len(FEAT_B))), columns=FEAT_B)
    X.loc[rng.random(300) < 0.3, ["img_cos", "phash_sim"]] = np.nan
    y = ((X["tfidf_cos"] + X["phash_sim"].fillna(0.5)) > 1).astype(int)
    joblib.dump({"modelo_A": _pipeline_logistica().fit(X[FEAT_A], y),
                 "modelo_B": _pipeline_logistica().fit(X[FEAT_B], y),
                 "FEAT_A": FEAT_A, "FEAT_B": FEAT_B, "config": {"K_VECINOS": 3}},
                carpeta / "modelo_pares.joblib")
    return carpeta
