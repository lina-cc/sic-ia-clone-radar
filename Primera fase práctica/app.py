"""App Gradio para explorar la similitud TF-IDF entre videojuegos.
 
Uso:
    python app.py                       # datos en data/juegos_texto_en.parquet
    python app.py --datos otra/ruta.parquet
    python app.py --share               # enlace público temporal mientras la app corre
 
Los casos que el grupo marque se guardan en casos/casos_guardados.csv.
"""
 
from __future__ import annotations

import argparse
import csv
import threading
from datetime import datetime
from pathlib import Path

import gradio as gr
import pandas as pd
from similitud import COLUMNAS_TABLA, BuscadorTfidf

ETIQUETAS = ["Similar", "No similar", "Posible copia"]
COLUMNAS_CASOS = ["fecha", "anotador", "tipo", "consulta", "juego_comparado",
                  "puntaje", "etiqueta", "comentario"]
ANCHOS = ["20%", "9%", "16%", "11%", "36%", "8%"]   # Juego, Puntaje, Géneros, Fecha, Términos, Steam
EJEMPLOS = ["Project Zomboid", "Left 4 Dead 2", "Stardew Valley"]
 
AVISO = (
    "**La similitud no es plagio.** Compartir género, mecánicas o vocabulario es normal. "
    "Esta herramienta solo sugiere candidatos para una revisión humana. "
    "TF-IDF compara palabras, no significado: dos juegos del mismo tema con vocabulario "
    "distinto pueden salir poco parecidos."
)
 
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
 
 
def crear_app(buscador: BuscadorTfidf, ruta_casos: Path) -> gr.Blocks:
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
    with gr.Blocks(title="Similitud entre videojuegos (TF-IDF)") as demo:
        gr.Markdown("# Similitud entre videojuegos: línea base TF-IDF")
        gr.Markdown(AVISO)
        anotador = gr.Textbox(label="Tu nombre (para registrar los casos que marques)",
                              placeholder="anónimo")
 
        with gr.Tab("Buscar similares"):
            with gr.Row():
                nombre = gr.Textbox(label="Título de un juego del dataset", scale=3)
                k1 = gr.Slider(3, 30, value=10, step=1, label="Cuántos mostrar", scale=1)
            boton1 = gr.Button("Buscar", variant="primary")
            msg1 = gr.Markdown()
            tabla1 = gr.Dataframe(headers=COLUMNAS_TABLA, interactive=False, wrap=True,
                                  datatype=["str", "number", "str", "str", "str", "markdown"],
                                  column_widths=ANCHOS)
            estado1 = gr.State()
            ejemplos = [[n] for n in EJEMPLOS if B.existe(n)]
            if ejemplos:
                gr.Examples(examples=ejemplos, inputs=[nombre], label="Ejemplos")
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
                a = gr.Textbox(label="Juego A")
                b = gr.Textbox(label="Juego B")
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
            texto = gr.Textbox(label="Descripción del juego (en inglés)", lines=6)
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
    return demo
 
 
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--datos", default="data/juegos_texto_en.parquet")
    p.add_argument("--casos", default="casos/casos_guardados.csv")
    p.add_argument("--puerto", type=int, default=7860)
    p.add_argument("--share", action="store_true", help="enlace público temporal")
    args = p.parse_args()
 
    print("Cargando datos y ajustando TF-IDF (la primera vez tarda; luego usa caché)...")
    try:
        buscador = BuscadorTfidf(args.datos)
    except FileNotFoundError as e:
        raise SystemExit(f"\nERROR: {e}")
    print(f"Listo: {len(buscador.df)} juegos, matriz {buscador.X.shape}.")
    crear_app(buscador, Path(args.casos)).launch(
        share=args.share, server_name="127.0.0.1", server_port=args.puerto)
 
 
if __name__ == "__main__":
    main()
