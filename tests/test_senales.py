"""Tests de las señales por par (senales.py).

Estas señales deben calcularse igual que en el notebook, porque el modelo
entrenado allí las recibe como entrada en la app.
"""

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from senales import SENALES, CalculadoraSenales, comparar_imagenes, conjunto_tags, jaccard


def test_conjunto_tags_une_generos_y_tags_sin_mayusculas_ni_vacios():
    assert conjunto_tags("Action, Indie", "Platformer, ") == {"action", "indie", "platformer"}
    assert conjunto_tags(None, None) == frozenset()


def test_jaccard():
    assert jaccard(frozenset("ab"), frozenset("bc")) == pytest.approx(1 / 3)
    assert np.isnan(jaccard(frozenset(), frozenset()))


def test_imagen_identica_da_uno_en_ambas_senales():
    img = {"emb": np.array([[0.6, 0.8]]), "hash": np.array([[True] * 32 + [False] * 32])}
    assert comparar_imagenes(img, img) == pytest.approx((1.0, 1.0))


def test_imagenes_se_comparan_todas_contra_todas_y_gana_la_mejor():
    a = {"emb": np.array([[1.0, 0.0], [0.0, 1.0]]), "hash": np.zeros((2, 64), bool)}
    b = {"emb": np.array([[0.0, 1.0]]), "hash": np.ones((1, 64), bool)}
    img_cos, phash = comparar_imagenes(a, b)
    assert img_cos == pytest.approx(1.0)   # la segunda imagen de A coincide con la de B
    assert phash == pytest.approx(0.0)     # todos los bits distintos


def test_sin_imagen_las_senales_quedan_vacias():
    img = {"emb": np.ones((1, 2)), "hash": np.zeros((1, 64), bool)}
    assert all(np.isnan(v) for v in comparar_imagenes(img, None))


def _calculadora():
    X = sp.csr_matrix(np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]))
    E = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    df = pd.DataFrame({
        "appid": [10, 11, 12],
        "name": ["Escape the Walls", "Walls Escape the", "Farm Tycoon"],
        "developer": ["Pandorio", "Pandorio", ""],
        "release_date": pd.to_datetime(["2026-10-14", "2026-10-16", None]),
        "genres": ["Action", "Action", "Simulation"],
        "tags": ["Escape", "Escape", ""],
    })
    img = {"emb": np.array([[1.0, 0.0]]), "hash": np.zeros((1, 64), bool)}
    return CalculadoraSenales(X, E, df, {10: img, 11: img})


def test_calculadora_devuelve_todas_las_senales():
    res = _calculadora().calcular([0], [1])
    assert list(res.columns) == ["i", "j"] + SENALES


def test_par_identico_en_texto_titulo_e_imagen():
    fila = _calculadora().calcular([0], [1]).iloc[0]
    assert fila["tfidf_cos"] == pytest.approx(1)
    assert fila["emb_cos"] == pytest.approx(1)
    assert fila["titulo_sim"] == pytest.approx(1)   # mismas palabras en otro orden
    assert fila["tags_jaccard"] == pytest.approx(1)
    assert fila["img_cos"] == pytest.approx(1)
    assert fila["phash_sim"] == pytest.approx(1)
    assert fila["log_dias"] == pytest.approx(np.log1p(2))
    assert fila["mismo_dev"] == 1


def test_datos_faltantes_quedan_vacios_y_no_rompen():
    fila = _calculadora().calcular([0], [2]).iloc[0]
    assert fila["tfidf_cos"] == pytest.approx(0)
    assert np.isnan(fila["img_cos"]) and np.isnan(fila["phash_sim"])   # el juego 12 no tiene imágenes
    assert np.isnan(fila["log_dias"])                                  # sin fecha
    assert np.isnan(fila["mismo_dev"])                                 # desarrollador desconocido


def test_tamanos_distintos_dan_error_claro():
    X = sp.csr_matrix(np.eye(2))
    with pytest.raises(ValueError, match="mismo paquete"):
        CalculadoraSenales(X, np.eye(3), pd.DataFrame({"name": ["a", "b"]}))
