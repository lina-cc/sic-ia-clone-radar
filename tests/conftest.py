"""Configuración común de los tests.

La app vive en la carpeta "Primera fase práctica", que no es un paquete de Python
(tiene espacios y tilde en el nombre). Para poder hacer `import similitud` y
`import app` desde los tests, se agrega esa carpeta al path de importación.
"""

import sys
from pathlib import Path

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
