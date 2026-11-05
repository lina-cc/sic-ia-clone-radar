"""Tests de la lógica de similitud TF-IDF (similitud.py).

Cada test comprueba un comportamiento que la app y el informe dan por hecho.
Se corren con:  pytest
"""

import pandas as pd
import pytest

from similitud import COLUMNAS_TABLA, BuscadorTfidf, limpiar


def test_limpiar_quita_html_y_espacios():
    assert limpiar("<p>Hola&nbsp;&amp;   <b>mundo</b></p>") == "Hola & mundo"


def test_archivo_inexistente_da_error_claro(tmp_path):
    with pytest.raises(FileNotFoundError, match="No encuentro el archivo de datos"):
        BuscadorTfidf(tmp_path / "no_existe.parquet")


def test_faltan_columnas_obligatorias(tmp_path):
    ruta = tmp_path / "malo.parquet"
    pd.DataFrame({"titulo": ["a"], "descripcion": ["b"]}).to_parquet(ruta)
    with pytest.raises(ValueError, match="faltan"):
        BuscadorTfidf(ruta)


def test_el_clon_es_el_mas_parecido_y_no_se_incluye_a_si_mismo(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    res = b.similares(b.buscar("Escape the Walls"), k=3)
    assert list(res.columns) == COLUMNAS_TABLA
    assert res.iloc[0]["Juego"] == "Escape Walls Obby"
    assert "Escape the Walls" not in set(res["Juego"])
    assert res["Puntaje"].is_monotonic_decreasing


def test_terminos_compartidos_explican_el_parecido(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    res = b.similares(b.buscar("Escape the Walls"), k=1)
    assert "walls" in res.iloc[0]["Términos compartidos"]


def test_comparar_es_simetrico_y_esta_entre_0_y_1(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    i, j = b.buscar("Farm Tycoon"), b.buscar("My Farm Empire")
    s_ij, terminos = b.comparar(i, j)
    s_ji, _ = b.comparar(j, i)
    assert s_ij == pytest.approx(s_ji)
    assert 0 < s_ij <= 1 + 1e-9  # margen por redondeo de punto flotante
    assert not terminos.empty
    assert (terminos["Aporte"] > 0).all()


def test_juegos_sin_relacion_puntuan_menos_que_el_clon(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    original = b.buscar("Escape the Walls")
    clon, _ = b.comparar(original, b.buscar("Escape Walls Obby"))
    otro, _ = b.comparar(original, b.buscar("Farm Tycoon"))
    assert clon > otro


def test_texto_sin_vocabulario_conocido_devuelve_tabla_vacia(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    assert b.similares_texto("zzzz qqqq xxxx").empty


def test_texto_nuevo_encuentra_el_juego_correcto(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    res = b.similares_texto("grow crops on your farm and sell products", k=2)
    assert set(res["Juego"]) == {"Farm Tycoon", "My Farm Empire"}


def test_busqueda_por_nombre_ignora_mayusculas_y_sugiere(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    assert b.existe("  escape THE walls ")
    assert not b.existe("Juego inventado")
    assert "Escape Walls Obby" in b.sugerencias("obby")
    with pytest.raises(KeyError):
        b.buscar("Juego inventado")


def test_homonimos_elige_el_mas_resenado(ruta_parquet):
    b = BuscadorTfidf(ruta_parquet, usar_cache=False)
    i = b.buscar("Racing Legends")
    assert b.df.loc[i, "n_resenas"] == 800


def test_cache_se_crea_y_se_reutiliza(ruta_parquet):
    b1 = BuscadorTfidf(ruta_parquet)
    cache = ruta_parquet.with_name(ruta_parquet.stem + ".tfidf.joblib")
    assert cache.exists()
    b2 = BuscadorTfidf(ruta_parquet)
    assert (b1.X != b2.X).nnz == 0
