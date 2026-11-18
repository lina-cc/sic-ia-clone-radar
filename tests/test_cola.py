"""Tests de la cola de revisión (cola.py) y de su HTML (vista.py)."""

import app
import vista
from cola import ColaRevision


def _cola(paquete_modelo, tmp_path):
    modelo = app.cargar_modelo(paquete_modelo)
    return ColaRevision(modelo, tmp_path / "casos" / "casos.csv")


def _guardar(cola, anotador, a, b, etiqueta):
    fila = {c: "" for c in app.COLUMNAS_CASOS}
    fila.update(anotador=anotador, consulta=a, juego_comparado=b, etiqueta=etiqueta)
    app.guardar_caso(cola.ruta_casos, fila)


def test_la_cola_entrega_un_par_con_sus_fichas(paquete_modelo, tmp_path):
    cola = _cola(paquete_modelo, tmp_path)
    par = cola.siguiente(cola.inicio("Sergio"))
    assert par is not None
    assert par["a"]["nombre"] != par["b"]["nombre"]
    assert par["a"]["enlace"].startswith("https://store.steampowered.com/app/")
    assert 0 <= par["prob"] <= 1
    assert par["estrategia"] in {"modelo", "texto", "bajo"}


def test_cada_persona_parte_siempre_del_mismo_punto(paquete_modelo, tmp_path):
    cola = _cola(paquete_modelo, tmp_path)
    assert cola.inicio("Sergio") == cola.inicio("  sergio ")
    assert cola.inicio(None) == cola.inicio("anónimo")


def test_no_repite_pares_etiquetados_ni_saltados(paquete_modelo, tmp_path):
    cola = _cola(paquete_modelo, tmp_path)
    vistos, saltados, cursor = set(), [], 0
    for n in range(30):
        par = cola.siguiente(cursor, saltados)
        if par is None:
            break
        clave = frozenset((par["a"]["nombre"], par["b"]["nombre"]))
        assert clave not in vistos
        vistos.add(clave)
        cursor = par["cursor"]
        if n % 2:   # la mitad se etiqueta (en orden inverso: el par es el mismo) y la otra mitad se salta
            _guardar(cola, "Sergio", par["b"]["nombre"], par["a"]["nombre"], "Similar")
        else:
            saltados.append([par["a"]["nombre"], par["b"]["nombre"]])
    assert vistos
    assert cola.siguiente(cursor, saltados) is None   # el catálogo de prueba es diminuto: se acaba


def test_progreso_cuenta_a_la_persona_y_al_equipo(paquete_modelo, tmp_path):
    cola = _cola(paquete_modelo, tmp_path)
    assert cola.progreso("Sergio") == {"tuyos": 0, "meta": 30, "positivos": 0, "negativos": 0,
                                       "minimo": 10, "listo": False}
    _guardar(cola, "Sergio", "Escape the Walls", "Escape Walls Obby", "Posible copia")
    _guardar(cola, "Catalina", "Farm Tycoon", "My Farm Empire", "Similar")
    _guardar(cola, "Catalina", "Space Miner", "Farm Tycoon", "No similar")
    # El mismo par, etiquetado de nuevo por otra persona: para el equipo vale la última etiqueta
    _guardar(cola, "Catalina", "Escape Walls Obby", "Escape the Walls", "Similar")
    p = cola.progreso("catalina")
    assert (p["tuyos"], p["positivos"], p["negativos"], p["listo"]) == (3, 0, 3, False)
    assert cola.progreso("Sergio")["tuyos"] == 1


def test_html_del_progreso_y_del_par(paquete_modelo, tmp_path):
    cola = _cola(paquete_modelo, tmp_path)
    falta = vista.progreso(cola.progreso(None))
    assert "anónimo" in falta and "le faltan" in falta
    listo = vista.progreso({"tuyos": 30, "meta": 30, "positivos": 12, "negativos": 40, "minimo": 10,
                            "listo": True}, "<b>Ana</b>")
    assert "Ya hay etiquetas suficientes" in listo and "&lt;b&gt;Ana" in listo
    par = cola.siguiente(0)
    html = vista.par_cola(par["a"], par["b"])
    assert html.count('class="fp-juego"') == 2 and "Abrir en Steam" in html
    # No se muestra la probabilidad antes de decidir
    assert "probabilidad" not in html
