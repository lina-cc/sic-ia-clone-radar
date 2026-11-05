"""App Gradio para explorar la similitud TF-IDF entre videojuegos.
 
Uso:
    python app.py                       # datos en data/juegos_texto_en.parquet
    python app.py --datos otra/ruta.parquet
    python app.py --share               # enlace público temporal mientras la app corre

Los casos que el grupo marque se guardan en casos/casos_guardados.csv.

Variables de entorno (sirven para desplegar en Hugging Face Spaces sin tocar el código):
    FAIRPLAY_DATOS       ruta del parquet (por defecto data/juegos_texto_en.parquet)
    FAIRPLAY_MODELO      carpeta del modelo entrenado (por defecto modelo/). Si no existe,
                         la pestaña "Modelo entrenado" explica cómo generarla.
    FAIRPLAY_HF_DATASET  si el parquet o el modelo no están en disco, se descargan de este dataset de
                         Hugging Face (por ejemplo "usuario/fairplay-datos", puede ser privado)
    HF_TOKEN             token de lectura, necesario si ese dataset es privado
    GRADIO_SERVER_NAME   dirección donde escucha la app (Spaces usa 0.0.0.0)
    GRADIO_SERVER_PORT   puerto (por defecto 7860)
"""

from __future__ import annotations

import argparse
import csv
import os
import threading
from html import escape
from datetime import datetime
from pathlib import Path

import gradio as gr
import pandas as pd
import vista
from similitud import COLUMNAS_TABLA, BuscadorTfidf

ETIQUETAS = ["Similar", "No similar", "Posible copia"]
ASSETS = Path(__file__).parent / "assets"
COLUMNAS_CASOS = ["fecha", "anotador", "tipo", "consulta", "juego_comparado",
                  "puntaje", "etiqueta", "comentario"]
ANCHOS = ["20%", "9%", "16%", "11%", "36%", "8%"]   # Juego, Puntaje, Géneros, Fecha, Términos, Steam
EJEMPLOS = ["Project Zomboid", "Left 4 Dead 2", "Stardew Valley"]
EJEMPLOS_MODELO = ["Stardew Valley", "Vampire Survivors", "Project Zomboid", "Among Us"]
 
_lock = threading.Lock()
 
 
def guardar_caso(ruta: Path, fila: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        nuevo = not ruta.exists()
        with ruta.open("a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS_CASOS)
            if nuevo:
                w.writeheader()
            w.writerow(fila)
 
 
AVISO_CORTO = (
    "<b>La similitud no es plagio.</b> Compartir género, mecánicas o vocabulario es normal. "
    "FairPlay AI solo ordena candidatos para que <b>una persona</b> los revise."
)

ACERCA = """
### Cómo funciona

1. **Candidatos:** para el juego que buscas, se toman sus vecinos más cercanos por palabras (TF-IDF) y por significado (embeddings).
2. **Señales:** para cada par se mide el parecido de géneros y tags, imágenes (CLIP y hash perceptual), título, texto y fechas.
3. **Modelo:** una regresión logística combina las señales en la **probabilidad de que el par merezca revisión humana**.
4. **Tú decides:** cada caso que marcas se guarda como etiqueta humana y sirve para entrenar y evaluar el modelo.

### Qué significa cada señal

| Señal | Pregunta |
|---|---|
| Géneros y tags | ¿Comparten géneros y etiquetas de Steam? |
| Imágenes | ¿Sus imágenes se ven parecidas? (CLIP) |
| Imagen idéntica | ¿Comparten una imagen casi igual? (hash perceptual) |
| Título | ¿Los nombres se parecen? |
| Significado | ¿Las descripciones dicen lo mismo, aunque con otras palabras? |
| Palabras | ¿Las descripciones usan las mismas palabras? |

Todas van de 0 (nada parecido) a 1 (idéntico); "—" significa que no había dato.

### Qué etiqueta poner

* **Posible copia:** coincidencias específicas que justifican que un especialista lo mire.
* **Similar:** se parecen, pero por razones normales (mismo género, misma mecánica).
* **No similar:** el parecido es casual.

Datos: catálogo público de Steam (dataset de Kaggle) e imágenes de la tienda, con fines académicos.
"""

SIN_MODELO = (
    "**El modelo entrenado no está cargado.** Para activarlo:\n\n"
    "1. Corre el notebook `FairPlay_AI_Clasificador_Pares.ipynb` hasta la sección 11.\n"
    "2. Copia la carpeta `salidas/paquete_app` a `Primera fase práctica/modelo/`.\n"
    "3. Vuelve a abrir la app (o usa `--modelo otra/carpeta`)."
)

EXPLICACION_MODELO = (
    "Esta pestaña usa el **modelo entrenado** del notebook. Para cada candidato calcula la "
    "**probabilidad de que el par merezca revisión humana**, combinando texto, imágenes, título, "
    "tags y fechas. Las columnas muestran cada señal entre 0 (nada parecido) y 1 (idéntico); "
    "vacío = no había imagen procesada para ese juego. "
    "Solo busca juegos que estén en el catálogo del modelo."
)


def encabezado() -> str:
    """Logo y nombre de la app (el SVG va en línea para no depender de rutas servidas)."""
    logo = (ASSETS / "logo-icono.svg").read_text(encoding="utf-8")
    logo = logo.replace('width="128" height="128"', 'width="56" height="56"', 1)   # solo el marco exterior
    return (f'<div class="fp-header">{logo}<div><div class="fp-name">FairPlay <span>AI</span></div>'
            '<div class="fp-tag">Prioriza qué pares de juegos de Steam vale la pena revisar por posible réplica'
            '</div></div></div>')


PIE = ('<div class="fp-pie">Proyecto capstone · Samsung Innovation Campus 2026 · Equipo FairPlay AI · '
       '<a href="https://github.com/sergiorebolledo/sic-ia-clone-radar" target="_blank" rel="noopener">'
       'Código y documentación</a></div>')


def crear_app(buscador: BuscadorTfidf, ruta_casos: Path, modelo=None) -> gr.Blocks:
    """Construye la interfaz. `modelo` es un BuscadorModelo (modelo.py) o None si no hay paquete."""
    B = buscador
    tabla_vacia = pd.DataFrame(columns=COLUMNAS_TABLA)
 
    def no_encontrado(nombre: str) -> str:
        sug = B.sugerencias(nombre)
        msg = f"No encontré **{nombre}** en el dataset (solo hay juegos con descripción en inglés)."
        if sug:
            msg += "\n\nQuizás buscabas: " + ", ".join(f"`{s}`" for s in sug)
        return msg
 
    def registrar(anotador, tipo, consulta, comparado, puntaje, etiqueta, comentario):
        if not consulta or comparado is None or not etiqueta:
            return "Primero haz una búsqueda y elige el caso y la etiqueta."
        guardar_caso(ruta_casos, {
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "anotador": (anotador or "anónimo").strip() or "anónimo",
            "tipo": tipo, "consulta": consulta, "juego_comparado": comparado,
            "puntaje": puntaje, "etiqueta": etiqueta, "comentario": comentario or "",
        })
        return f"Guardado: **{comparado}** → {etiqueta}."
 
    # ---- acciones de cada pestaña --------------------------------------
    def accion_buscar(nombre, k):
        nombre = (nombre or "").strip()
        if not nombre:
            return "Escribe el título de un juego.", tabla_vacia, None, gr.Dropdown(choices=[], value=None)
        try:
            i = B.buscar(nombre)
        except KeyError:
            return no_encontrado(nombre), tabla_vacia, None, gr.Dropdown(choices=[], value=None)
        res = B.similares(i, int(k))
        estado = {"consulta": B.nombre(i), "puntajes": dict(zip(res["Juego"], res["Puntaje"]))}
        return (f"Juegos más parecidos a **{B.nombre(i)}**:", res, estado,
                gr.Dropdown(choices=list(res["Juego"]), value=None))
 
    def accion_texto(texto, k):
        texto = (texto or "").strip()
        if len(texto) < 20:
            return "Escribe una descripción de al menos 20 caracteres.", tabla_vacia, None, gr.Dropdown(choices=[], value=None)
        res = B.similares_texto(texto, int(k))
        if res.empty:
            return ("Ninguna palabra del texto está en el vocabulario del modelo "
                    "(¿está en inglés?)."), tabla_vacia, None, gr.Dropdown(choices=[], value=None)
        estado = {"consulta": "texto nuevo: " + texto[:80],
                  "puntajes": dict(zip(res["Juego"], res["Puntaje"]))}
        return ("Juegos más parecidos a tu texto:", res, estado,
                gr.Dropdown(choices=list(res["Juego"]), value=None))
 
    def accion_comparar(a, b):
        a, b = (a or "").strip(), (b or "").strip()
        if not a or not b:
            return "Escribe los dos títulos.", pd.DataFrame(), None
        for n in (a, b):
            if not B.existe(n):
                return no_encontrado(n), pd.DataFrame(), None
        i, j = B.buscar(a), B.buscar(b)
        score, terminos = B.comparar(i, j)
        msg = (f"**{B.nombre(i)}** frente a **{B.nombre(j)}**: similitud coseno = **{score:.3f}** "
               f"(0 = sin palabras en común, 1 = textos equivalentes).")
        if terminos.empty:
            msg += "\n\nNo comparten ningún término del vocabulario."
        estado = {"a": B.nombre(i), "b": B.nombre(j), "puntaje": round(score, 3)}
        return msg, terminos, estado
 
    def guardar_busqueda(anotador, tipo, estado, elegido, etiqueta, comentario):
        if not estado:
            return "Primero haz una búsqueda."
        return registrar(anotador, tipo, estado["consulta"], elegido,
                         estado["puntajes"].get(elegido), etiqueta, comentario)
 
    def guardar_comparacion(anotador, estado, etiqueta, comentario):
        if not estado:
            return "Primero compara dos juegos."
        return registrar(anotador, "comparar", estado["a"], estado["b"],
                         estado["puntaje"], etiqueta, comentario)
 
    # ---- interfaz --------------------------------------------------------
    def pestanas_linea_base():
        gr.Markdown("Compara solo **las palabras** de las descripciones (TF-IDF). Es la referencia contra la "
                    "que se mide el modelo: rápida y explicable, pero da falsas alarmas entre juegos del mismo "
                    "género y no ve imágenes.")
        with gr.Tabs():
            with gr.Tab("Buscar similares"):
                with gr.Row(equal_height=True):
                    nombre = gr.Textbox(label="Título de un juego del dataset", placeholder="Ej.: Project Zomboid",
                                        scale=4)
                    k1 = gr.Slider(3, 30, value=10, step=1, label="Cuántos mostrar", scale=1)
                boton1 = gr.Button("Buscar", variant="primary")
                ejemplos = [[n] for n in EJEMPLOS if B.existe(n)]
                if ejemplos:
                    gr.Examples(examples=ejemplos, inputs=[nombre], label="Ejemplos")
                msg1 = gr.Markdown()
                tabla1 = gr.Dataframe(headers=COLUMNAS_TABLA, interactive=False, wrap=True,
                                      datatype=["str", "number", "str", "str", "str", "markdown"],
                                      column_widths=ANCHOS)
                estado1 = gr.State()
                with gr.Accordion("Guardar un caso", open=False):
                    elegido1 = gr.Dropdown(label="¿Qué resultado quieres marcar?", choices=[])
                    etiq1 = gr.Radio(ETIQUETAS, label="Etiqueta")
                    com1 = gr.Textbox(label="Comentario (opcional)")
                    guardar1 = gr.Button("Guardar caso")
                    res_guardar1 = gr.Markdown()
                boton1.click(accion_buscar, [nombre, k1], [msg1, tabla1, estado1, elegido1], api_name="buscar")
                nombre.submit(accion_buscar, [nombre, k1], [msg1, tabla1, estado1, elegido1])
                guardar1.click(lambda an, es, el, et, co: guardar_busqueda(an, "buscar", es, el, et, co),
                               [anotador, estado1, elegido1, etiq1, com1], res_guardar1, api_name="guardar_buscar")

            with gr.Tab("Comparar dos juegos"):
                with gr.Row():
                    a = gr.Textbox(label="Juego A", placeholder="Ej.: Stardew Valley")
                    b = gr.Textbox(label="Juego B", placeholder="Ej.: Coral Island")
                boton2 = gr.Button("Comparar", variant="primary")
                msg2 = gr.Markdown()
                tabla2 = gr.Dataframe(interactive=False, wrap=True,
                                      label="Términos que más aportan al parecido")
                estado2 = gr.State()
                with gr.Accordion("Guardar este par", open=False):
                    etiq2 = gr.Radio(ETIQUETAS, label="Etiqueta")
                    com2 = gr.Textbox(label="Comentario (opcional)")
                    guardar2 = gr.Button("Guardar caso")
                    res_guardar2 = gr.Markdown()
                boton2.click(accion_comparar, [a, b], [msg2, tabla2, estado2], api_name="comparar")
                guardar2.click(guardar_comparacion, [anotador, estado2, etiq2, com2],
                               res_guardar2, api_name="guardar_comparar")

            with gr.Tab("Texto nuevo"):
                texto = gr.Textbox(label="Descripción del juego (en inglés)", lines=6,
                                   placeholder="Pega aquí la descripción de un juego, en inglés.")
                k3 = gr.Slider(3, 30, value=10, step=1, label="Cuántos mostrar")
                boton3 = gr.Button("Buscar", variant="primary")
                msg3 = gr.Markdown()
                tabla3 = gr.Dataframe(headers=COLUMNAS_TABLA, interactive=False, wrap=True,
                                      datatype=["str", "number", "str", "str", "str", "markdown"],
                                      column_widths=ANCHOS)
                estado3 = gr.State()
                with gr.Accordion("Guardar un caso", open=False):
                    elegido3 = gr.Dropdown(label="¿Qué resultado quieres marcar?", choices=[])
                    etiq3 = gr.Radio(ETIQUETAS, label="Etiqueta")
                    com3 = gr.Textbox(label="Comentario (opcional)")
                    guardar3 = gr.Button("Guardar caso")
                    res_guardar3 = gr.Markdown()
                boton3.click(accion_texto, [texto, k3], [msg3, tabla3, estado3, elegido3], api_name="texto_nuevo")
                guardar3.click(lambda an, es, el, et, co: guardar_busqueda(an, "texto_nuevo", es, el, et, co),
                               [anotador, estado3, elegido3, etiq3, com3], res_guardar3, api_name="guardar_texto")

    with gr.Blocks(title="FairPlay AI · Similitud entre videojuegos") as demo:
        # Se crea antes de las pestañas (las usan al guardar casos) y se dibuja al final
        anotador = gr.Textbox(show_label=False, placeholder="anónimo", render=False)
        with gr.Row(equal_height=True):
            with gr.Column(scale=3):
                gr.HTML(encabezado())
            with gr.Column(scale=2, min_width=280):
                gr.HTML(f'<div class="fp-aviso">{AVISO_CORTO}</div>')
        # El modelo entrenado es la herramienta principal; la línea base queda como referencia
        with gr.Tabs():
            if modelo is not None:
                with gr.Tab("Buscar candidatos"):
                    agregar_pestana_modelo(modelo, anotador, registrar)
                with gr.Tab("Línea base (solo palabras)"):
                    pestanas_linea_base()
            else:
                with gr.Tab("Línea base (solo palabras)"):
                    pestanas_linea_base()
                with gr.Tab("Modelo entrenado"):
                    gr.Markdown(SIN_MODELO)
            with gr.Tab("Acerca de"):
                gr.Markdown(ACERCA)
        with gr.Accordion("Tu nombre, para registrar los casos que marques", open=False):
            anotador.render()
        gr.HTML(PIE)
    return demo


def agregar_pestana_modelo(M, anotador, registrar) -> None:
    """Pestaña principal: candidatos del modelo entrenado, explicación de un par y veredicto."""
    from modelo import COLUMNAS_CANDIDATOS

    cual = ("Modelo B: todas las señales, entrenado con etiquetas humanas" if M.usa_modelo_B
            else "Modelo A: imágenes, título, tags y fechas, entrenado con etiquetas automáticas")
    vacia = pd.DataFrame(columns=COLUMNAS_CANDIDATOS)
    inicio = vista.vacio("Escribe el nombre de un juego de Steam, o elige un ejemplo, "
                         "para ver qué juegos <b>vale la pena revisar</b> junto a él.")
    inicio_exp = vista.vacio("Cuando busques un juego, aquí verás <b>por qué</b> el modelo recomienda revisar "
                             "cada candidato.")

    def sin_opciones():
        return gr.Dropdown(choices=[], value=None)

    def accion(nombre, k):
        nombre = (nombre or "").strip()
        if not nombre:
            return vista.vacio("Escribe el título de un juego."), vacia, None, sin_opciones()
        try:
            q = M.tfidf.buscar(nombre)
        except KeyError:
            sug = M.tfidf.sugerencias(nombre)
            msg = f"No encontré <b>{escape(nombre)}</b> en el catálogo."
            if sug:
                msg += "<br>¿Quizás buscabas " + ", ".join(f"<b>{escape(x)}</b>" for x in sug) + "?"
            return vista.vacio(msg), vacia, None, sin_opciones()
        res = M.candidatos(q, int(k))
        etiquetas = [f"{n + 1}. {j}" for n, j in enumerate(res["Juego"])]
        estado = {"q": q, "consulta": M.tfidf.nombre(q),
                  "cands": {e: (int(p), str(j), float(pr))
                            for e, p, j, pr in zip(etiquetas, res["pos"], res["Juego"], res["Prob. revisar"])}}
        html = vista.tarjetas(res, [M.url_imagen(int(p)) for p in res["pos"]], M.tfidf.nombre(q), cual)
        return (html, res[COLUMNAS_CANDIDATOS], estado,
                gr.Dropdown(choices=etiquetas, value=etiquetas[0] if etiquetas else None))

    def explicar(estado, elegido):
        if not estado or not elegido or elegido not in estado["cands"]:
            return inicio_exp
        pos, nombre, _ = estado["cands"][elegido]
        prob, aportes = M.explicar(estado["q"], pos)
        return vista.explicacion(estado["consulta"], nombre, prob, aportes,
                                 M.url_imagen(estado["q"]), M.url_imagen(pos))

    def guardar(an, estado, elegido, etiqueta, comentario):
        if not estado or not elegido:
            return "Primero busca un juego y elige un candidato."
        if not etiqueta:
            return "Elige una etiqueta antes de guardar."
        _, nombre, prob = estado["cands"][elegido]
        return registrar(an, "modelo", estado["consulta"], nombre, prob, etiqueta, comentario)

    with gr.Row(equal_height=True):
        nombre = gr.Textbox(label="Juego de Steam", placeholder="Ej.: Stardew Valley", scale=5)
        k = gr.Slider(3, 20, value=8, step=1, label="Candidatos", scale=2, min_width=160)
        boton = gr.Button("Buscar", variant="primary", scale=1, min_width=110, elem_classes="fp-btn")
    ejemplos = [n for n in EJEMPLOS_MODELO if M.tfidf.existe(n)]
    botones = []
    if ejemplos:
        with gr.Row():
            gr.Markdown("**Prueba con:**")
            botones = [gr.Button(n, size="sm", variant="secondary") for n in ejemplos]
    resultados = gr.HTML(inicio)
    with gr.Accordion("Ver los resultados como tabla", open=False):
        tabla = gr.Dataframe(interactive=False, wrap=True)
    estado = gr.State()

    gr.Markdown("### ¿Por qué este candidato?")
    elegido = gr.Dropdown(label="Elige un candidato para ver la explicación", choices=[])
    explicacion = gr.HTML(inicio_exp)

    gr.Markdown("### Tu veredicto")
    with gr.Row(equal_height=True):
        etiq = gr.Radio(ETIQUETAS, label="¿Qué es este par?", scale=2)
        com = gr.Textbox(label="Comentario (opcional)", scale=3)
        boton_guardar = gr.Button("Guardar caso", variant="primary", scale=1, min_width=120, elem_classes="fp-btn")
    res_guardar = gr.Markdown()

    salidas = [resultados, tabla, estado, elegido]
    boton.click(accion, [nombre, k], salidas, api_name="modelo_buscar")
    nombre.submit(accion, [nombre, k], salidas)
    for b, n in zip(botones, ejemplos):
        b.click(lambda n=n: n, None, nombre).then(accion, [nombre, k], salidas)
    elegido.change(explicar, [estado, elegido], explicacion, api_name="modelo_explicar")
    boton_guardar.click(guardar, [anotador, estado, elegido, etiq, com], res_guardar, api_name="guardar_modelo")


def resolver_datos(ruta: str | Path) -> Path:
    """Devuelve la ruta del parquet. Si no existe y está definido FAIRPLAY_HF_DATASET,
    lo descarga desde Hugging Face a la misma carpeta (así funciona en Spaces, donde
    los datos no pueden ir dentro del repositorio público)."""
    ruta = Path(ruta)
    repo = os.environ.get("FAIRPLAY_HF_DATASET")
    if ruta.exists() or not repo:
        return ruta
    from huggingface_hub import hf_hub_download  # viene instalado con gradio

    # Ruta relativa (p. ej. modelo/catalogo.parquet): se busca con esa misma ruta dentro del dataset.
    # Ruta absoluta: se busca solo por el nombre del archivo, en la raíz del dataset.
    nombre, destino = (ruta.name, ruta.parent) if ruta.is_absolute() else (ruta.as_posix(), Path("."))
    print(f"Descargando {nombre} desde el dataset {repo} de Hugging Face...")
    descargado = hf_hub_download(repo_id=repo, filename=nombre, repo_type="dataset",
                                 token=os.environ.get("HF_TOKEN"), local_dir=destino)
    return Path(descargado)


def cargar_modelo(carpeta: str | Path):
    """Carga el modelo entrenado si existe; si no, devuelve None y la app sigue sin esa pestaña.

    En Spaces, si la carpeta no existe y está FAIRPLAY_HF_DATASET, descarga los archivos
    desde la carpeta del mismo nombre dentro del dataset (por ejemplo modelo/catalogo.parquet).
    """
    from modelo import ARCHIVOS, BuscadorModelo

    carpeta = Path(carpeta)
    repo = os.environ.get("FAIRPLAY_HF_DATASET")
    faltan = [f for f in ARCHIVOS if not (carpeta / f).exists()]
    if faltan and repo:  # la carpeta puede existir a medias (p. ej. si --datos apunta a modelo/catalogo.parquet)
        from huggingface_hub import hf_hub_download

        print(f"Descargando el modelo desde el dataset {repo} de Hugging Face...")
        try:
            for f in faltan:
                hf_hub_download(repo_id=repo, filename=f"{carpeta.name}/{f}", repo_type="dataset",
                                token=os.environ.get("HF_TOKEN"), local_dir=carpeta.parent)
        except Exception as e:
            print(f"No se pudo descargar el modelo ({e}). La pestaña del modelo quedará desactivada.")
            return None
    if not carpeta.exists():
        print(f"Sin modelo entrenado en {carpeta}: la pestaña 'Modelo entrenado' explicará cómo generarlo.")
        return None
    print("Cargando el modelo entrenado...")
    try:
        m = BuscadorModelo(carpeta)
    except RuntimeError as e:  # versión de scikit-learn distinta a la del notebook
        print(f"\nNo se pudo cargar el modelo: {e}\nLa pestaña del modelo quedará desactivada.\n")
        return None
    print(f"Modelo listo: {len(m.df)} juegos en su catálogo.")
    return m


DATOS_POR_DEFECTO = "data/juegos_texto_en.parquet"


def credenciales() -> tuple[str, str] | None:
    """Usuario y contraseña para entrar a la app, si FAIRPLAY_CLAVE está definida.

    Sirve para publicarla en un servidor (por ejemplo OCI) sin que cualquiera pueda marcar casos.
    El usuario es FAIRPLAY_USUARIO, o "fairplay" si no está definido. Sin FAIRPLAY_CLAVE, la app queda abierta.
    """
    clave = os.environ.get("FAIRPLAY_CLAVE", "").strip()
    if not clave:
        return None
    return os.environ.get("FAIRPLAY_USUARIO", "fairplay").strip() or "fairplay", clave


def elegir_datos(datos: str, carpeta_modelo: str) -> str:
    """Si no se indicó otro parquet y el de siempre no está, usa el catálogo del modelo.

    Así basta con copiar el paquete del modelo (o tener FAIRPLAY_HF_DATASET) para abrir la app.
    """
    catalogo = Path(carpeta_modelo) / "catalogo.parquet"
    if datos == DATOS_POR_DEFECTO and not Path(datos).exists() and (
            catalogo.exists() or os.environ.get("FAIRPLAY_HF_DATASET")):
        return catalogo.as_posix()
    return datos


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--datos", default=os.environ.get("FAIRPLAY_DATOS", DATOS_POR_DEFECTO),
                   help="parquet de la línea base (si falta, se usa el catálogo del modelo)")
    p.add_argument("--modelo", default=os.environ.get("FAIRPLAY_MODELO", "modelo"),
                   help="carpeta con el paquete exportado por el notebook (sección 11)")
    p.add_argument("--casos", default="casos/casos_guardados.csv")
    p.add_argument("--puerto", type=int, default=int(os.environ.get("GRADIO_SERVER_PORT", 7860)))
    p.add_argument("--share", action="store_true", help="enlace público temporal")
    args = p.parse_args()
    args.datos = elegir_datos(args.datos, args.modelo)

    print("Cargando datos y ajustando TF-IDF (la primera vez tarda; luego usa caché)...")
    try:
        buscador = BuscadorTfidf(resolver_datos(args.datos))
    except FileNotFoundError as e:
        raise SystemExit(f"\nERROR: {e}")
    print(f"Listo: {len(buscador.df)} juegos, matriz {buscador.X.shape}.")
    modelo = cargar_modelo(args.modelo)
    # En local escucha solo en 127.0.0.1; en Spaces la variable GRADIO_SERVER_NAME vale 0.0.0.0
    crear_app(buscador, Path(args.casos), modelo).launch(
        share=args.share, server_name=os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=args.puerto, favicon_path=str(ASSETS / "favicon.png"),
        theme=vista.TEMA, css=vista.CSS, auth=credenciales(),
        auth_message="FairPlay AI: ingresa el usuario y la contraseña del equipo.")
 
 
if __name__ == "__main__":
    main()
