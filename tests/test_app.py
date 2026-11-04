"""Tests de la app Gradio (app.py) que no necesitan abrir el navegador."""

import csv

import gradio as gr

import app
from similitud import BuscadorTfidf


def test_guardar_caso_escribe_encabezado_una_sola_vez(tmp_path):
    ruta = tmp_path / "casos" / "casos.csv"
    fila = {c: "x" for c in app.COLUMNAS_CASOS}
    app.guardar_caso(ruta, fila)
    app.guardar_caso(ruta, fila)
    with ruta.open(encoding="utf-8-sig") as f:
        filas = list(csv.reader(f))
    assert filas[0] == app.COLUMNAS_CASOS
    assert len(filas) == 3  # encabezado + 2 casos


def test_resolver_datos_sin_hugging_face_devuelve_la_misma_ruta(tmp_path, monkeypatch):
    monkeypatch.delenv("FAIRPLAY_HF_DATASET", raising=False)
    ruta = tmp_path / "no_existe.parquet"
    assert app.resolver_datos(ruta) == ruta


def test_resolver_datos_no_descarga_si_el_archivo_ya_existe(ruta_parquet, monkeypatch):
    monkeypatch.setenv("FAIRPLAY_HF_DATASET", "usuario/dataset-que-no-existe")
    assert app.resolver_datos(ruta_parquet) == ruta_parquet


def test_la_interfaz_se_construye(ruta_parquet, tmp_path):
    demo = app.crear_app(BuscadorTfidf(ruta_parquet, usar_cache=False), tmp_path / "casos.csv")
    assert isinstance(demo, gr.Blocks)
