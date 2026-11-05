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


def test_la_interfaz_se_construye_con_el_modelo(ruta_parquet, paquete_modelo, tmp_path):
    modelo = app.cargar_modelo(paquete_modelo)
    assert modelo is not None
    demo = app.crear_app(BuscadorTfidf(ruta_parquet, usar_cache=False), tmp_path / "casos.csv", modelo)
    assert isinstance(demo, gr.Blocks)


def test_sin_carpeta_de_modelo_la_app_sigue_sin_esa_pestana(tmp_path, monkeypatch):
    monkeypatch.delenv("FAIRPLAY_HF_DATASET", raising=False)
    assert app.cargar_modelo(tmp_path / "no_existe") is None


def test_resolver_datos_relativa_conserva_la_carpeta_dentro_del_dataset(monkeypatch, tmp_path):
    """En Spaces, FAIRPLAY_DATOS=modelo/catalogo.parquet descarga modelo/catalogo.parquet del dataset."""
    import huggingface_hub

    pedidos = []

    def falso_hf_hub_download(repo_id, filename, repo_type, token, local_dir):
        pedidos.append((filename, str(local_dir)))
        return str(tmp_path / filename)

    monkeypatch.setenv("FAIRPLAY_HF_DATASET", "usuario/datos")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", falso_hf_hub_download)
    app.resolver_datos("modelo/catalogo.parquet")
    assert pedidos == [("modelo/catalogo.parquet", ".")]


def test_cargar_modelo_completa_una_carpeta_a_medias(paquete_modelo, monkeypatch):
    """Si la carpeta ya existe pero le faltan archivos, descarga solo los que faltan."""
    import shutil

    import huggingface_hub

    respaldo = paquete_modelo.parent / "respaldo.joblib"
    shutil.move(paquete_modelo / "modelo_pares.joblib", respaldo)
    pedidos = []

    def falso_hf_hub_download(repo_id, filename, repo_type, token, local_dir):
        pedidos.append(filename)
        shutil.copy(respaldo, paquete_modelo / "modelo_pares.joblib")

    monkeypatch.setenv("FAIRPLAY_HF_DATASET", "usuario/datos")
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", falso_hf_hub_download)
    assert app.cargar_modelo(paquete_modelo) is not None
    assert pedidos == [f"{paquete_modelo.name}/modelo_pares.joblib"]


def test_sin_parquet_de_la_linea_base_usa_el_catalogo_del_modelo(paquete_modelo, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FAIRPLAY_HF_DATASET", raising=False)
    assert app.elegir_datos(app.DATOS_POR_DEFECTO, str(paquete_modelo)) == (paquete_modelo / "catalogo.parquet").as_posix()
    # Si se pide otro parquet a propósito, se respeta
    assert app.elegir_datos("otro.parquet", str(paquete_modelo)) == "otro.parquet"
    # Sin modelo ni dataset, se mantiene la ruta de siempre (y la app explica qué falta)
    assert app.elegir_datos(app.DATOS_POR_DEFECTO, str(tmp_path / "nada")) == app.DATOS_POR_DEFECTO
