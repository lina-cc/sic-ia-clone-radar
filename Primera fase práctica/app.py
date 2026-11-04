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
    with gr.Blocks(title="FairPlay AI · Similitud entre videojuegos") as demo:
        gr.Markdown("# FairPlay AI: similitud entre videojuegos")
        gr.Markdown("Las tres primeras pestañas usan la **línea base TF-IDF** (solo palabras). "
                    "La pestaña **Modelo entrenado** combina texto, imágenes y metadatos.")
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

        with gr.Tab("Modelo entrenado"):
            if modelo is None:
                gr.Markdown(SIN_MODELO)
            else:
                agregar_pestana_modelo(modelo, anotador, registrar)
    return demo


def agregar_pestana_modelo(M, anotador, registrar) -> None:
    """Contenido de la pestaña "Modelo entrenado" (se llama dentro de gr.Blocks)."""
    from modelo import COLUMNAS_CANDIDATOS

    cual = ("Modelo B (todas las señales, entrenado con etiquetas humanas)" if M.usa_modelo_B
            else "Modelo A (imágenes, título, tags y fechas; entrenado con etiquetas débiles)")
    vacia = pd.DataFrame(columns=COLUMNAS_CANDIDATOS)

    def sin_opciones():
        # Se crea al responder (no al construir la pestaña) para no dibujar un componente extra
        return gr.Dropdown(choices=[], value=None)

    def accion(nombre, k):
        nombre = (nombre or "").strip()
        if not nombre:
            return "Escribe el título de un juego.", vacia, [], None, sin_opciones()
        try:
            q = M.tfidf.buscar(nombre)
        except KeyError:
            sug = M.tfidf.sugerencias(nombre)
            msg = f"No encontré **{nombre}** en el catálogo del modelo."
            if sug:
                msg += "\n\nQuizás buscabas: " + ", ".join(f"`{s}`" for s in sug)
            return msg, vacia, [], None, sin_opciones()
        res = M.candidatos(q, int(k))
        etiquetas = [f"{n + 1}. {j}" for n, j in enumerate(res["Juego"])]
        estado = {"q": q, "consulta": M.tfidf.nombre(q),
                  "cands": {e: (int(p), str(j), float(pr))
                            for e, p, j, pr in zip(etiquetas, res["pos"], res["Juego"], res["Prob. revisar"])}}
        galeria = [(u, c) for u, c in
                   [(M.url_imagen(q), f"Consultado: {M.tfidf.nombre(q)}")] +
                   [(M.url_imagen(int(p)), f"{e} · prob. {pr:.2f}")
                    for e, p, pr in zip(etiquetas, res["pos"], res["Prob. revisar"])] if u]
        msg = (f"Candidatos para **{M.tfidf.nombre(q)}**, ordenados por probabilidad. Modelo usado: {cual}.\n\n"
               "*Una probabilidad alta significa \"vale la pena revisarlo\", no \"es una copia\".*")
        return (msg, res[COLUMNAS_CANDIDATOS], galeria, estado,
                gr.Dropdown(choices=etiquetas, value=etiquetas[0] if etiquetas else None))

    def explicar(estado, elegido):
        if not estado or not elegido:
            return "Primero busca un juego y elige un candidato.", pd.DataFrame(), []
        pos, nombre, _ = estado["cands"][elegido]
        prob, aportes = M.explicar(estado["q"], pos)
        a_favor = aportes[aportes["Aporte"] > 0]["Señal"].head(3).tolist()
        en_contra = aportes[aportes["Aporte"] < 0]["Señal"].head(3).tolist()
        msg = (f"**{estado['consulta']}** frente a **{nombre}**: probabilidad de revisar = **{prob:.2f}**.\n\n"
               f"- Lo que más **sube** la probabilidad: {', '.join(a_favor) or 'nada'}\n"
               f"- Lo que más la **baja**: {', '.join(en_contra) or 'nada'}\n\n"
               "*Aporte* = cuánto empuja cada señal (positivo hacia \"revisar\", negativo hacia \"no revisar\"). "
               "Las filas *Sin dato* indican que esa señal no se pudo calcular (por ejemplo, sin imágenes).")
        imgs = [(u, c) for u, c in [(M.url_imagen(estado["q"]), estado["consulta"]),
                                    (M.url_imagen(pos), nombre)] if u]
        return msg, aportes, imgs

    def guardar(an, estado, elegido, etiqueta, comentario):
        if not estado or not elegido:
            return "Primero busca un juego y elige un candidato."
        _, nombre, prob = estado["cands"][elegido]
        return registrar(an, "modelo", estado["consulta"], nombre, prob, etiqueta, comentario)

    gr.Markdown(EXPLICACION_MODELO)
    with gr.Row():
        nombre = gr.Textbox(label="Título de un juego del catálogo", scale=3)
        k = gr.Slider(3, 20, value=10, step=1, label="Cuántos candidatos", scale=1)
    boton = gr.Button("Buscar candidatos", variant="primary")
    msg = gr.Markdown()
    tabla = gr.Dataframe(interactive=False, wrap=True)
    galeria = gr.Gallery(label="Imágenes de cabecera en Steam", columns=4, height="auto")
    estado = gr.State()
    with gr.Accordion("Explicar un candidato", open=True):
        elegido = gr.Dropdown(label="Candidato", choices=[])
        boton_exp = gr.Button("Explicar")
        msg_exp = gr.Markdown()
        tabla_exp = gr.Dataframe(interactive=False, label="Aporte de cada señal")
        galeria_exp = gr.Gallery(label="Lado a lado", columns=2, height="auto")
    with gr.Accordion("Guardar este candidato como caso", open=False):
        etiq = gr.Radio(ETIQUETAS, label="Etiqueta")
        com = gr.Textbox(label="Comentario (opcional)")
        boton_guardar = gr.Button("Guardar caso")
        res_guardar = gr.Markdown()

    salidas = [msg, tabla, galeria, estado, elegido]
    boton.click(accion, [nombre, k], salidas, api_name="modelo_buscar")
    nombre.submit(accion, [nombre, k], salidas)
    boton_exp.click(explicar, [estado, elegido], [msg_exp, tabla_exp, galeria_exp], api_name="modelo_explicar")
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

    print(f"Descargando {ruta.name} desde el dataset {repo} de Hugging Face...")
    descargado = hf_hub_download(repo_id=repo, filename=ruta.name, repo_type="dataset",
                                 token=os.environ.get("HF_TOKEN"), local_dir=ruta.parent)
    return Path(descargado)


def cargar_modelo(carpeta: str | Path):
    """Carga el modelo entrenado si existe; si no, devuelve None y la app sigue sin esa pestaña.

    En Spaces, si la carpeta no existe y está FAIRPLAY_HF_DATASET, descarga los archivos
    desde la carpeta del mismo nombre dentro del dataset (por ejemplo modelo/catalogo.parquet).
    """
    from modelo import ARCHIVOS, BuscadorModelo

    carpeta = Path(carpeta)
    repo = os.environ.get("FAIRPLAY_HF_DATASET")
    if not carpeta.exists() and repo:
        from huggingface_hub import hf_hub_download

        print(f"Descargando el modelo desde el dataset {repo} de Hugging Face...")
        try:
            for f in ARCHIVOS:
                hf_hub_download(repo_id=repo, filename=f"{carpeta.name}/{f}", repo_type="dataset",
                                token=os.environ.get("HF_TOKEN"), local_dir=carpeta.parent)
        except Exception as e:
            print(f"No se pudo descargar el modelo ({e}). La pestaña del modelo quedará desactivada.")
            return None
    if not carpeta.exists():
        print(f"Sin modelo entrenado en {carpeta}: la pestaña 'Modelo entrenado' explicará cómo generarlo.")
        return None
    print("Cargando el modelo entrenado...")
    m = BuscadorModelo(carpeta)
    print(f"Modelo listo: {len(m.df)} juegos en su catálogo.")
    return m


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--datos", default=os.environ.get("FAIRPLAY_DATOS", "data/juegos_texto_en.parquet"))
    p.add_argument("--modelo", default=os.environ.get("FAIRPLAY_MODELO", "modelo"),
                   help="carpeta con el paquete exportado por el notebook (sección 11)")
    p.add_argument("--casos", default="casos/casos_guardados.csv")
    p.add_argument("--puerto", type=int, default=int(os.environ.get("GRADIO_SERVER_PORT", 7860)))
    p.add_argument("--share", action="store_true", help="enlace público temporal")
    args = p.parse_args()

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
        server_port=args.puerto)
 
 
if __name__ == "__main__":
    main()
