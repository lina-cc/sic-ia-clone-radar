"""Tests del análisis de reseñas (resenas.py). No consultan internet."""

import json
import urllib.error

import pytest

import resenas
from resenas import Titulos, analizar, tiene_alerta

CATALOGO = {1: "Escape the Walls", 2: "Escape Walls Obby", 3: "Portal", 4: "Terraforming",
            5: "Racing Legends", 6: "Racing Legends"}


@pytest.mark.parametrize("texto", [
    "A shameless clone of the original", "total RIP-OFF", "this is an asset flip", "They stole the art",
    "blatant copy, avoid", "es una copia descarada", "puro plagio", "copied everything",
])
def test_detecta_expresiones_de_copia(texto):
    assert tiene_alerta(texto)


@pytest.mark.parametrize("texto", [
    "I bought a copy for my friend", "great farming game", "", "the cyclone level is hard",
    "at this price it's a STEAL", "a physical and digital copy of the game",
])
def test_no_confunde_usos_normales(texto):
    assert not tiene_alerta(texto)


def test_titulos_ignora_palabras_comunes_y_nombres_repetidos():
    t = Titulos(CATALOGO)
    assert t.menciones("better than Portal and Racing Legends") == set()   # corto y repetido
    assert t.menciones("a Terraforming sim, like ESCAPE THE WALLS!") == {4, 1}
    assert t.menciones("Escape the Walls is great", propio=1) == set()      # no se cuenta a sí mismo


def test_analizar_cuenta_alertas_y_menciones():
    r = analizar(2, ["A shameless clone of Escape the Walls", "fun game", "clone of escape the walls again",
                     "I love Escape the Walls"], Titulos(CATALOGO))
    assert (r["n_resenas"], r["n_alerta"], r["frac_alerta"]) == (4, 2, 0.5)
    assert r["menciones"] == {1: 2}          # la reseña sin alerta no cuenta como mención
    assert "clone of Escape the Walls" in r["ejemplo"]
    # El nombre tiene que estar cerca de la alerta, no en cualquier parte de la reseña
    lejos = "total clone. " + "bla " * 60 + "By the way I also play Terraforming."
    assert analizar(2, [lejos], Titulos(CATALOGO))["menciones"] == {}
    vacio = analizar(9, [], Titulos(CATALOGO))
    assert vacio["frac_alerta"] == 0.0 and vacio["menciones"] == {} and vacio["ejemplo"] == ""


def test_titulos_solo_juegos_conocidos_si_se_pasan_las_resenas():
    resenas_por_juego = {1: 900, 2: 3, 4: 900}
    t = Titulos(CATALOGO, resenas=resenas_por_juego, min_resenas=500)
    assert t.menciones("Escape the Walls, Escape Walls Obby and Terraforming") == {1}   # 4: una palabra pide 2500


class _Respuesta:
    def __init__(self, cuerpo): self.cuerpo = cuerpo
    def read(self): return self.cuerpo.encode("utf-8")
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_descargar_prueba_la_segunda_ruta_si_la_primera_no_devuelve_json(monkeypatch):
    pedidas = []

    def falso_urlopen(pedido, timeout):
        pedidas.append(pedido.full_url)
        if len(pedidas) == 1:
            return _Respuesta("<!DOCTYPE html><html>portada</html>")
        return _Respuesta(json.dumps({"success": 1, "reviews": [{"review": "hola"}, {"review": "clone"}]}))

    monkeypatch.setattr(resenas.urllib.request, "urlopen", falso_urlopen)
    assert resenas.descargar(123) == ["hola", "clone"]
    assert len(pedidas) == 2 and "/123?" in pedidas[0] and "num_per_page=100" in pedidas[0] and "filter=recent" in pedidas[0]


def test_descargar_devuelve_none_si_no_hay_conexion(monkeypatch):
    def falso_urlopen(pedido, timeout):
        raise urllib.error.URLError("sin red")

    monkeypatch.setattr(resenas.urllib.request, "urlopen", falso_urlopen)
    assert resenas.descargar(123) is None
