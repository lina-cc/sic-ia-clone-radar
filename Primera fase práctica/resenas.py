"""Reseñas de usuarios de Steam como pista para encontrar pares sospechosos.

Idea (sugerida por el profesor): los jugadores suelen ser los primeros en escribir
"esto es una copia de X". Este módulo busca esas reseñas para decidir **qué pares
etiquetar primero**. No es una señal del modelo ni una prueba: la decisión sigue siendo humana.

Qué se mide en las reseñas de un juego
--------------------------------------
* alerta:  la reseña usa una expresión como "clone", "rip-off", "asset flip", "stolen" o "copia".
* mención: cerca de esa expresión se nombra a OTRO juego conocido del catálogo ("clone of X").
           Eso apunta a un par concreto.

Cuidados
--------
* "Clone" también se usa como género ("un clon de Stardew muy bueno"): es una pista, no una acusación.
* Las reseñas son texto de usuarios: se guardan en Drive, nunca en el repositorio.
* Se consulta la tienda de Steam con una pausa entre juegos, para no sobrecargarla.

Ejemplo
-------
    titulos = Titulos({1: "Escape the Walls", 2: "Escape Walls Obby"})
    analizar(2, ["A shameless clone of Escape the Walls", "fun game"], titulos)
    # {'appid': 2, 'n_resenas': 2, 'n_alerta': 1, 'frac_alerta': 0.5,
    #  'menciones': {1: 1}, 'ejemplo': 'A shameless clone of Escape the Walls'}
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter

# La tienda responde en esta ruta; la documentada (/appreviews/) hoy redirige a la portada.
URLS = ["https://store.steampowered.com/ajaxappreviews/{appid}",
        "https://store.steampowered.com/appreviews/{appid}"]
# filter=recent trae las más recientes sin límite de fecha (filter=all solo mira los últimos días)
PARAMETROS = "?json=1&filter=recent&language=all&purchase_type=all&num_per_page={n}"

# Expresiones que suelen aparecer cuando alguien denuncia una copia (inglés y español).
# Quedan fuera a propósito, porque casi siempre significan otra cosa:
#   "copy" y "copy of": "ejemplar" ("I bought a copy", "a digital copy of the game")
#   "steal":            "ganga" ("at this price it's a steal")
ALERTAS = re.compile(
    r"\b(clon(e|ed|es|ing)?|copycat|copied|copy[- ]?paste[d]?|carbon copy|"
    r"(blatant|cheap|shameless|exact|direct|straight) cop(y|ies)|"
    r"rip[- ]?off|ripoff|ripped off|knock[- ]?off|asset[- ]?flip|bootleg|stolen|stole|"
    r"plagiari[sz](m|ed|es|e)|reskin(ned)?|"
    r"copia(do|da|ron)?|clon(ado|ada|es)?|plagio|plagiado|robad[oa]s?)\b", re.IGNORECASE)

# Títulos de una sola palabra que son palabras comunes: dan demasiadas falsas menciones.
_PALABRA = re.compile(r"[a-z0-9]+")
MAX_PALABRAS_TITULO = 6
VENTANA = 80     # caracteres antes y después de la alerta donde se busca el nombre de otro juego


def tiene_alerta(texto: str) -> bool:
    """True si la reseña usa alguna expresión de copia. Ej.: "total rip-off" -> True."""
    return bool(ALERTAS.search(texto or ""))


def _normalizar(texto: str) -> list[str]:
    """Minúsculas y solo letras y números: "Vampire Survivors!" -> ["vampire", "survivors"]."""
    return _PALABRA.findall((texto or "").lower())


class Titulos:
    """Índice de títulos del catálogo para encontrar qué juegos nombra una reseña.

    Solo entran títulos distintivos, porque muchos juegos se llaman como palabras comunes
    ("Strategy", "Controller"):
    * de dos o más palabras, o de una palabra de al menos `min_letras` letras;
    * si se pasa `resenas` ({appid: número de reseñas}), solo juegos conocidos: al menos
      `min_resenas` reseñas, y cinco veces más si el título es de una sola palabra.
    """

    def __init__(self, nombres: dict[int, str], resenas: dict[int, int] | None = None,
                 min_resenas: int = 500, min_letras: int = 8):
        self.indice: dict[tuple[str, ...], int] = {}
        repetidos = set()
        for appid, nombre in nombres.items():
            clave = tuple(_normalizar(nombre))
            if not clave or len(clave) > MAX_PALABRAS_TITULO:
                continue
            if len(clave) == 1 and len(clave[0]) < min_letras:
                continue
            if resenas is not None and resenas.get(appid, 0) < min_resenas * (5 if len(clave) == 1 else 1):
                continue
            if clave in self.indice:        # dos juegos con el mismo nombre: no se sabe cuál es
                repetidos.add(clave)
            self.indice[clave] = int(appid)
        for clave in repetidos:
            del self.indice[clave]
        self.max_palabras = max((len(c) for c in self.indice), default=0)

    def menciones(self, texto: str, propio: int | None = None) -> set[int]:
        """appid de los juegos que nombra el texto (sin contar el propio juego)."""
        palabras = _normalizar(texto)
        encontrados = set()
        for i in range(len(palabras)):
            for largo in range(1, self.max_palabras + 1):
                appid = self.indice.get(tuple(palabras[i:i + largo]))
                if appid is not None and appid != propio:
                    encontrados.add(appid)
        return encontrados


def analizar(appid: int, textos: list[str], titulos: Titulos) -> dict:
    """Resume las reseñas de un juego: cuántas tienen alerta y a qué otros juegos nombran.

    `menciones` es {appid_mencionado: número de reseñas que lo nombran cerca de una alerta}.
    `ejemplo` es el trozo de una reseña alrededor de la alerta, para revisarla a mano.
    """
    con_alerta = [t for t in textos if tiene_alerta(t)]
    menciones, ejemplos_mencion, ejemplos = Counter(), [], []
    for t in con_alerta:
        nombrados = set()
        for m in ALERTAS.finditer(t):
            trozo = t[max(0, m.start() - VENTANA):m.end() + VENTANA]
            encontrados = titulos.menciones(trozo, propio=appid)
            (ejemplos_mencion if encontrados else ejemplos).append(trozo)
            nombrados |= encontrados
        menciones.update(nombrados)
    ejemplo = " ".join((ejemplos_mencion or ejemplos or [""])[0].split())
    return {"appid": int(appid), "n_resenas": len(textos), "n_alerta": len(con_alerta),
            "frac_alerta": round(len(con_alerta) / len(textos), 3) if textos else 0.0,
            "menciones": dict(menciones), "ejemplo": ejemplo}


def descargar(appid: int, n: int = 100, espera: float = 20.0, intentos: int = 3) -> list[str] | None:
    """Hasta `n` reseñas (las más útiles, en cualquier idioma) de un juego. None si no se pudo.

    Si la tienda responde "demasiadas consultas" (429), espera y reintenta.
    """
    for base in URLS:
        url = base.format(appid=int(appid)) + PARAMETROS.format(n=min(int(n), 100))
        for intento in range(intentos):
            try:
                pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (proyecto académico)"})
                with urllib.request.urlopen(pedido, timeout=30) as r:
                    cuerpo = r.read().decode("utf-8", errors="replace")
                datos = json.loads(cuerpo)
                if datos.get("success") == 1:
                    return [x.get("review", "") for x in datos.get("reviews", [])]
                break                                   # respuesta válida pero sin éxito: probar la otra ruta
            except urllib.error.HTTPError as e:
                if e.code == 429 and intento < intentos - 1:
                    time.sleep(espera * (intento + 1))
                    continue
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                break                                   # p. ej. redirección a la portada (HTML, no JSON)
    return None
