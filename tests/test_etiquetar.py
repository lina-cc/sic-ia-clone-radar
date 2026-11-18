"""Tests de lo que ayuda a etiquetar: deshacer, últimos casos, pasos y el aviso del modelo en uso."""

import csv

import pandas as pd

import app
import vista


def _guardar(ruta, anotador, a, b, etiqueta):
    fila = {c: "" for c in app.COLUMNAS_CASOS}
    fila.update(anotador=anotador, consulta=a, juego_comparado=b, etiqueta=etiqueta)
    app.guardar_caso(ruta, fila)


def _leer(ruta):
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_deshacer_borra_solo_el_ultimo_caso_de_esa_persona(tmp_path):
    ruta = tmp_path / "casos.csv"
    _guardar(ruta, "Sergio", "A", "B", "Similar")
    _guardar(ruta, "Catalina", "A", "B", "Posible copia")
    _guardar(ruta, "Sergio", "A", "B", "No similar")
    assert app.borrar_ultimo_caso(ruta, " Sergio ", "A", "B")
    filas = _leer(ruta)
    assert [(f["anotador"], f["etiqueta"]) for f in filas] == [("Sergio", "Similar"), ("Catalina", "Posible copia")]
    assert list(filas[0]) == app.COLUMNAS_CASOS            # el archivo conserva sus columnas


def test_deshacer_no_toca_nada_si_no_encuentra_el_caso(tmp_path):
    ruta = tmp_path / "casos.csv"
    assert not app.borrar_ultimo_caso(ruta, "Sergio", "A", "B")       # todavía no hay archivo
    _guardar(ruta, "Sergio", "A", "B", "Similar")
    assert not app.borrar_ultimo_caso(ruta, "Sergio", "A", "Otro juego")
    assert not app.borrar_ultimo_caso(ruta, "Catalina", "A", "B")
    assert len(_leer(ruta)) == 1


def test_ultimos_casos_muestra_los_de_la_persona_del_mas_nuevo_al_mas_antiguo():
    casos = pd.DataFrame({"anotador": ["Sergio", "Catalina", "sergio "],
                          "consulta": ["A", "C", "<b>E</b>"], "juego_comparado": ["B", "D", "F"],
                          "etiqueta": ["Similar", "No similar", "Posible copia"]})
    html = vista.ultimos(casos, "Sergio")
    assert html.index("Posible copia") < html.index("Similar")
    assert "No similar" not in html and "&lt;b&gt;E" in html
    assert "Escribe tu nombre" in vista.ultimos(casos, "")
    assert "Todavía no has guardado" in vista.ultimos(casos, "Avelyn")


def test_pasos_numera_y_escapa():
    html = vista.pasos([("Compara", "Mira <los> dos"), ("Decide", "Elige")])
    assert html.count('class="fp-rank"') == 2 and "&lt;los&gt;" in html


def test_encabezado_dice_que_modelo_esta_en_uso(paquete_modelo):
    modelo = app.cargar_modelo(paquete_modelo)
    assert "Modelo B" in app.encabezado(modelo)             # el paquete de prueba trae Modelo B
    modelo.modelo_B = None
    assert "Modelo A" in app.encabezado(modelo)
    assert "fp-chip" not in app.encabezado()
