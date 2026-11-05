"""El HTML de los resultados: que muestre lo importante y no rompa con datos raros."""
import math

import pandas as pd

import vista


def _candidatos():
    return pd.DataFrame({
        "Juego": ["Coral <Island>", "Forager"], "Desarrollador": ["Stairway Games", None],
        "Fecha": ["2023-11-14", ""], "Prob. revisar": [0.29, 0.1], "Texto (palabras)": [0.17, 0.2],
        "Texto (significado)": [0.39, 0.3], "Imagen (CLIP)": [0.52, math.nan], "Imagen idéntica": [0.53, math.nan],
        "Título": [0.31, 0.29], "Géneros y tags": [0.7, 0.4], "Términos compartidos": ["farm, crops", ""],
        "pos": [1, 2], "appid": [1158160, None]})


def test_tarjetas_muestran_probabilidad_enlace_y_terminos():
    html = vista.tarjetas(_candidatos(), ["https://img/1.jpg", None], "Stardew Valley", "Modelo A")
    assert html.count('class="fp-card"') == 2
    assert "29%" in html and "store.steampowered.com/app/1158160" in html
    assert "<span>farm</span>" in html
    assert "Coral &lt;Island&gt;" in html          # el nombre se escapa
    assert "sin imagen" in html and "—" in html    # sin imagen ni dato de imagen: no rompe


def test_tarjetas_sin_resultados_muestran_un_aviso():
    assert "fp-vacio" in vista.tarjetas(_candidatos().iloc[0:0], [], "X", "Modelo A")


def test_explicacion_separa_lo_que_sube_y_lo_que_baja():
    aportes = pd.DataFrame({"Señal": ["Géneros y tags en común", "Imágenes parecidas (CLIP)", "Sin dato: Título"],
                            "Valor": [0.7, 0.57, math.nan], "Aporte": [0.73, -0.61, math.nan]})
    html = vista.explicacion("Stardew Valley", "Cornucopia", 0.37, aportes, "https://a", None)
    assert "37%" in html
    assert "sube:</b> Géneros y tags en común" in html and "baja:</b> Imágenes parecidas (CLIP)" in html
    assert 'class="pos"' in html and 'class="neg"' in html
    assert html.count("<figure>") == 1             # solo la imagen que existe
