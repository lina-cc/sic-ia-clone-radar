"""Tests del uso del modelo entrenado en la app (modelo.py)."""

import joblib
import pytest

from modelo import COLUMNAS_CANDIDATOS, BuscadorModelo, nombre_legible


def test_sin_paquete_explica_como_generarlo(tmp_path):
    with pytest.raises(FileNotFoundError, match="sección 11"):
        BuscadorModelo(tmp_path)


def test_rechaza_un_modelo_con_senales_desconocidas(paquete_modelo):
    ruta = paquete_modelo / "modelo_pares.joblib"
    art = joblib.load(ruta)
    art["FEAT_A"] = art["FEAT_A"] + ["senal_inventada"]
    joblib.dump(art, ruta)
    with pytest.raises(ValueError, match="senal_inventada"):
        BuscadorModelo(paquete_modelo)


def test_rechaza_un_modelo_de_otra_version_de_sklearn(paquete_modelo, monkeypatch):
    import warnings

    import modelo
    from sklearn.exceptions import InconsistentVersionWarning

    cargar = joblib.load

    def cargar_con_aviso(ruta):
        # Lo mismo que hace scikit-learn al abrir un modelo guardado con otra versión
        warnings.warn(InconsistentVersionWarning(estimator_name="SimpleImputer",
                                                 current_sklearn_version="9.9", original_sklearn_version="1.6.1"))
        return cargar(ruta)

    monkeypatch.setattr(modelo.joblib, "load", cargar_con_aviso)
    with pytest.raises(RuntimeError, match="scikit-learn 1.6.1"):
        BuscadorModelo(paquete_modelo)


def test_el_clon_es_el_primer_candidato(paquete_modelo):
    m = BuscadorModelo(paquete_modelo)
    res = m.candidatos(m.tfidf.buscar("Escape the Walls"), k=3)
    assert res.iloc[0]["Juego"] == "Escape Walls Obby"
    assert "Escape the Walls" not in set(res["Juego"])
    assert set(COLUMNAS_CANDIDATOS) <= set(res.columns)
    assert res["Prob. revisar"].between(0, 1).all()
    assert res["Prob. revisar"].is_monotonic_decreasing


def test_un_juego_con_la_misma_imagen_es_candidato_aunque_el_texto_sea_otro(paquete_modelo):
    import joblib

    imagenes = joblib.load(paquete_modelo / "imagenes.joblib")
    imagenes[6] = {"emb": imagenes[1]["emb"].copy(), "hash": imagenes[1]["hash"].copy()}   # Racing Legends
    joblib.dump(imagenes, paquete_modelo / "imagenes.joblib")
    m = BuscadorModelo(paquete_modelo)
    m.k_vecinos = 2                                     # tope de candidatos por cada vía
    escape, racing = m.tfidf.buscar("Escape the Walls"), 5
    assert m.df.loc[racing, "appid"] == 6
    assert set(m.vecinos_imagen(escape)) == {1, racing}  # Escape Walls Obby y Racing Legends
    assert racing in m.vecinos(escape)
    # Un juego cuya imagen no se parece a ninguna otra no suma candidatos por imagen
    farm = m.tfidf.buscar("Farm Tycoon")
    assert m.vecinos_imagen(farm) == []
    # Las señales siguen igual con los vectores ya indexados
    assert m.senales.calcular([escape], [racing]).iloc[0]["img_cos"] > 0.99


def test_sin_imagenes_los_candidatos_salen_solo_del_texto(paquete_modelo):
    import joblib

    joblib.dump({}, paquete_modelo / "imagenes.joblib")
    m = BuscadorModelo(paquete_modelo)
    escape = m.tfidf.buscar("Escape the Walls")
    assert m.vecinos_imagen(escape) == []
    assert len(m.candidatos(escape, k=3)) > 0


def test_explicar_usa_nombres_legibles_y_marca_lo_que_falta(paquete_modelo):
    m = BuscadorModelo(paquete_modelo)
    q = m.tfidf.buscar("Escape the Walls")
    prob, aportes = m.explicar(q, m.tfidf.buscar("Escape Walls Obby"))
    assert 0 <= prob <= 1
    assert "Texto: mismas palabras" in set(aportes["Señal"])
    assert not any(s.startswith("missingindicator_") for s in aportes["Señal"])

    # Space Miner no tiene imágenes: sus señales de imagen deben figurar como "sin dato"
    _, aportes2 = m.explicar(q, m.tfidf.buscar("Space Miner"))
    fila = aportes2[aportes2["Señal"] == "Imágenes parecidas (CLIP)"]
    assert fila.empty or fila.iloc[0]["Valor"].startswith("sin dato")


def test_sin_modelo_B_usa_el_modelo_A(paquete_modelo):
    ruta = paquete_modelo / "modelo_pares.joblib"
    art = joblib.load(ruta)
    art["modelo_B"] = None
    joblib.dump(art, ruta)
    m = BuscadorModelo(paquete_modelo)
    assert not m.usa_modelo_B
    assert len(m.candidatos(0, k=2)) == 2


def test_nombre_legible():
    assert nombre_legible("phash_sim") == "Imagen casi idéntica (hash)"
    assert nombre_legible("missingindicator_img_cos") == "Sin dato: Imágenes parecidas (CLIP)"


def test_url_de_imagen_por_appid(paquete_modelo):
    m = BuscadorModelo(paquete_modelo)
    assert m.url_imagen(0).endswith("/apps/1/header.jpg")
