"""Aspecto visual de la app: tema de Gradio, estilos y el HTML de los resultados.

Separado de app.py para que la lógica (buscar, explicar, guardar) no se mezcle con el diseño,
y para poder probar el HTML sin levantar la interfaz.
"""
from __future__ import annotations

import math
from html import escape

import gradio as gr
import pandas as pd

# Azul de la marca (el de la plantilla del curso) y naranjo de acento, en la escala que pide Gradio
AZUL = gr.themes.Color(
    name="fairplay", c50="#eef2fc", c100="#dbe3f8", c200="#b8c7f1", c300="#8ea6e7", c400="#5f7fdb",
    c500="#3459cc", c600="#193eb0", c700="#15349a", c800="#122b7e", c900="#0f2466", c950="#0a1844")

TEMA = gr.themes.Soft(
    primary_hue=AZUL, secondary_hue=gr.themes.colors.orange, neutral_hue=gr.themes.colors.slate,
    radius_size=gr.themes.sizes.radius_lg,
    font=(gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"),
).set(
    button_primary_background_fill="*primary_600",
    button_primary_background_fill_hover="*primary_700",
    button_primary_text_color="white",
    block_title_text_weight="600",
)

# Señales que se dibujan en cada tarjeta: (columna de la tabla, nombre corto)
SENALES_TARJETA = [("Géneros y tags", "Géneros y tags"), ("Imagen (CLIP)", "Imágenes"),
                   ("Imagen idéntica", "Imagen idéntica"), ("Título", "Título"),
                   ("Texto (significado)", "Significado"), ("Texto (palabras)", "Palabras")]

CSS = """
.fp-header{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.fp-header .fp-name{font-size:28px;font-weight:800;line-height:1.05;letter-spacing:-.5px}
.fp-header .fp-name span{color:var(--primary-600)}
.fp-header .fp-tag{font-size:14px;color:var(--body-text-color-subdued);margin-top:4px}
.fp-aviso{border-radius:12px;padding:10px 14px;background:var(--secondary-50);
  border:1px solid var(--secondary-200);font-size:14px;line-height:1.45}
.dark .fp-aviso{background:rgba(232,122,26,.10);border-color:rgba(232,122,26,.35)}
.fp-vacio{border:1.5px dashed var(--border-color-primary);border-radius:14px;padding:28px;
  text-align:center;color:var(--body-text-color-subdued);font-size:15px}
.fp-vacio b{color:var(--body-text-color)}
.fp-resumen{font-size:15px;margin:2px 0 10px}
.fp-resumen small{display:block;color:var(--body-text-color-subdued);margin-top:2px}
.fp-cards{display:flex;flex-direction:column;gap:12px}
.fp-card{display:grid;grid-template-columns:200px minmax(0,1fr) 270px;gap:18px;align-items:start;
  padding:14px;border:1px solid var(--border-color-primary);border-radius:14px;
  background:var(--block-background-fill)}
.fp-thumb{width:200px;aspect-ratio:460/215;object-fit:cover;border-radius:8px;
  background:var(--background-fill-secondary);display:block}
.fp-sinimg{width:200px;aspect-ratio:460/215;border-radius:8px;background:var(--background-fill-secondary);
  display:flex;align-items:center;justify-content:center;font-size:12px;color:var(--body-text-color-subdued)}
.fp-titulo{font-size:17px;font-weight:700;line-height:1.25}
.fp-titulo a{color:inherit;text-decoration:none}
.fp-titulo a:hover{text-decoration:underline}
.fp-rank{display:inline-flex;align-items:center;justify-content:center;min-width:24px;height:24px;
  border-radius:99px;background:var(--primary-600);color:#fff;font-size:12px;font-weight:700;
  margin-right:8px;vertical-align:2px}
.fp-meta{font-size:13px;color:var(--body-text-color-subdued);margin-top:3px}
.fp-chips{margin-top:8px}
.fp-chips span{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;margin:4px 4px 0 0;
  background:var(--background-fill-secondary);border:1px solid var(--border-color-primary)}
.fp-prob{display:flex;align-items:baseline;gap:8px}
.fp-prob b{font-size:26px;font-weight:800;color:var(--primary-600)}
.dark .fp-prob b{color:var(--primary-300)}
.fp-prob small{font-size:12px;color:var(--body-text-color-subdued)}
.fp-barra{height:8px;border-radius:99px;background:var(--background-fill-secondary);overflow:hidden;margin:4px 0 10px}
.fp-barra i{display:block;height:100%;border-radius:99px;background:var(--primary-600)}
.fp-sig{display:grid;grid-template-columns:100px minmax(0,1fr) 34px;gap:5px 8px;align-items:center;font-size:12px}
.fp-sig .fp-mini{height:6px;border-radius:99px;background:var(--background-fill-secondary);overflow:hidden}
.fp-sig .fp-mini i{display:block;height:100%;background:var(--secondary-500)}
.fp-sig em{font-style:normal;color:var(--body-text-color-subdued);text-align:right}
.fp-exp-titulo{font-size:16px;margin-bottom:6px}
.fp-exp-titulo b.fp-p{color:var(--primary-600)}
.fp-motivos{display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 14px}
.fp-motivos div{flex:1 1 240px;border-radius:12px;padding:10px 12px;font-size:14px;
  background:var(--background-fill-secondary)}
.fp-aportes{display:grid;grid-template-columns:190px minmax(0,1fr) 60px;gap:8px 10px;align-items:center;font-size:13px}
.fp-eje{position:relative;height:14px}
.fp-eje::before{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;border-left:1px solid var(--border-color-primary)}
.fp-eje i{position:absolute;top:2px;height:10px;border-radius:3px}
.fp-eje i.pos{left:50%;background:var(--secondary-500)}
.fp-eje i.neg{right:50%;background:var(--neutral-400)}
.fp-aportes em{font-style:normal;text-align:right;font-variant-numeric:tabular-nums}
.fp-nota{font-size:12px;color:var(--body-text-color-subdued);margin-top:10px}
.fp-lado{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:14px}
.fp-lado figure{margin:0}
.fp-lado img{width:100%;max-height:230px;object-fit:cover;border-radius:10px;display:block}
.fp-btn{align-self:flex-end!important;max-height:52px;min-height:44px}
.fp-lado figcaption{font-size:13px;margin-top:4px;color:var(--body-text-color-subdued)}
.fp-pie{text-align:center;font-size:12px;color:var(--body-text-color-subdued);margin-top:8px}
.fp-pie a{color:inherit}
.fp-prog{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.fp-prog>div{border:1px solid var(--border-color-primary);border-radius:12px;padding:10px 14px;
  background:var(--block-background-fill)}
.fp-prog span{font-size:12px;color:var(--body-text-color-subdued);display:block}
.fp-prog b{font-size:20px;font-weight:800}
.fp-prog b small{font-size:13px;font-weight:500;color:var(--body-text-color-subdued)}
.fp-prog .fp-barra{margin:6px 0 0}
.fp-prog .fp-ok .fp-barra i{background:#2f9e5b}
.fp-prog-nota{font-size:14px;margin-top:10px}
.fp-par{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fp-juego{border:1px solid var(--border-color-primary);border-radius:14px;padding:14px;
  background:var(--block-background-fill)}
.fp-foto{width:100%;aspect-ratio:460/215;object-fit:cover;border-radius:10px;display:block;
  background:var(--background-fill-secondary)}
.fp-juego .fp-sinimg{width:100%}
.fp-juego .fp-titulo{margin-top:10px}
.fp-desc{font-size:13.5px;line-height:1.5;margin-top:8px;max-height:9em;overflow:auto}
.fp-abrir{display:inline-block;margin-top:10px;font-size:13px;font-weight:600;color:var(--primary-600)}
.dark .fp-abrir{color:var(--primary-300)}
.fp-chip{display:inline-block;margin-top:8px;padding:3px 10px;border-radius:99px;font-size:12px;font-weight:600;
  background:var(--background-fill-secondary);border:1px solid var(--border-color-primary)}
.fp-ambos{margin:0 0 10px;font-size:13px;color:var(--body-text-color-subdued)}
.fp-ambos .fp-chip{margin:4px 4px 0 0}
.fp-chip-b{background:#e7f6ec;border-color:#9fd3b1;color:#1d6b3a}
.dark .fp-chip-b{background:rgba(47,158,91,.18);border-color:rgba(47,158,91,.5);color:#8fdcaa}
.fp-quien-nota{font-size:13px;color:var(--body-text-color-subdued);padding-top:26px;line-height:1.45}
.fp-pasos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:4px}
.fp-pasos>div{display:flex;gap:10px;align-items:flex-start;font-size:13.5px;line-height:1.4}
.fp-pasos .fp-rank{flex:none;margin:1px 0 0}
.fp-pasos b{display:block;font-size:14.5px}
.fp-pasos span.t{color:var(--body-text-color-subdued)}
.fp-pista{font-size:12.5px;line-height:1.4;color:var(--body-text-color-subdued);text-align:center;padding:0 6px}
.fp-decision button{min-height:52px;font-weight:700;font-size:16px}
.fp-b-copia{background:var(--secondary-500)!important;color:#fff!important;border-color:var(--secondary-600)!important}
.fp-b-copia:hover{background:var(--secondary-600)!important}
.fp-b-similar{background:var(--primary-600)!important;color:#fff!important;border-color:var(--primary-700)!important}
.fp-b-similar:hover{background:var(--primary-700)!important}
.fp-b-no{background:var(--neutral-600)!important;color:#fff!important;border-color:var(--neutral-700)!important}
.fp-b-no:hover{background:var(--neutral-700)!important}
.fp-ultimos{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px 14px;font-size:13.5px}
.fp-ultimos em{font-style:normal;font-weight:600}
@media (max-width:820px){
  .fp-prog,.fp-par,.fp-pasos{grid-template-columns:1fr}
  .fp-quien-nota{padding-top:0}
  .fp-card{grid-template-columns:1fr}
  .fp-thumb,.fp-sinimg{width:100%}
  .fp-aportes{grid-template-columns:130px minmax(0,1fr) 48px}
  .fp-lado{grid-template-columns:1fr}
}
"""


def vacio(mensaje: str) -> str:
    """Recuadro que se muestra cuando todavía no hay resultados (o algo falló)."""
    return f'<div class="fp-vacio">{mensaje}</div>'


def _numero(v) -> float | None:
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) else v


def _mini(nombre: str, valor) -> str:
    v = _numero(valor)
    ancho = 0 if v is None else max(0.0, min(1.0, v)) * 100
    texto = "—" if v is None else f"{v:.2f}"
    return (f'<span>{escape(nombre)}</span><div class="fp-mini"><i style="width:{ancho:.0f}%"></i></div>'
            f'<em>{texto}</em>')


def tarjetas(res: pd.DataFrame, urls: list[str | None], consulta: str, modelo_usado: str) -> str:
    """Una tarjeta por candidato: imagen, datos, probabilidad y señales.

    `res` es la tabla de BuscadorModelo.candidatos; `urls` la imagen de cada fila (o None).
    """
    if res.empty:
        return vacio("El modelo no encontró candidatos para este juego.")
    filas = []
    for n, (fila, url) in enumerate(zip(res.to_dict("records"), urls), start=1):
        prob = _numero(fila.get("Prob. revisar")) or 0.0
        nombre = escape(str(fila.get("Juego", "")))
        appid = _numero(fila.get("appid"))
        enlace = f"https://store.steampowered.com/app/{int(appid)}" if appid is not None else None
        titulo = (f'<a href="{enlace}" target="_blank" rel="noopener">{nombre}</a>' if enlace else nombre)
        meta = " · ".join(escape(str(x)) for x in (fila.get("Desarrollador"), fila.get("Fecha")) if x)
        terminos = [t.strip() for t in str(fila.get("Términos compartidos") or "").split(",") if t.strip()]
        chips = "".join(f"<span>{escape(t)}</span>" for t in terminos[:5])
        imagen = (f'<img class="fp-thumb" src="{escape(url)}" alt="{nombre}" loading="lazy">' if url
                  else '<div class="fp-sinimg">sin imagen</div>')
        senales = "".join(_mini(corto, fila.get(col)) for col, corto in SENALES_TARJETA)
        filas.append(
            f'<div class="fp-card">{imagen}'
            f'<div><div class="fp-titulo"><span class="fp-rank">{n}</span>{titulo}</div>'
            f'<div class="fp-meta">{meta}</div>'
            + (f'<div class="fp-chips">{chips}</div>' if chips else "") +
            '</div>'
            f'<div><div class="fp-prob"><b>{prob * 100:.0f}%</b><small>probabilidad de revisar</small></div>'
            f'<div class="fp-barra"><i style="width:{prob * 100:.0f}%"></i></div>'
            f'<div class="fp-sig">{senales}</div></div>'
            '</div>')
    resumen = (f'<div class="fp-resumen">Candidatos para <b>{escape(consulta)}</b>, del más al menos '
               f'recomendable de revisar.<small>{escape(modelo_usado)}. Una probabilidad alta significa '
               '"vale la pena mirarlo", no "es una copia".</small></div>')
    return resumen + '<div class="fp-cards">' + "".join(filas) + "</div>"


def explicacion(consulta: str, candidato: str, prob: float, aportes: pd.DataFrame,
                imagen_a: str | None, imagen_b: str | None) -> str:
    """Por qué el modelo dio esa probabilidad: aporte de cada señal en barras a ambos lados de 0."""
    validos = aportes.dropna(subset=["Aporte"])
    a_favor = validos[validos["Aporte"] > 0]["Señal"].head(3).tolist()
    en_contra = validos[validos["Aporte"] < 0]["Señal"].head(3).tolist()
    tope = max(float(validos["Aporte"].abs().max()) if not validos.empty else 0.0, 1e-9)
    filas = []
    for _, f in aportes.iterrows():
        ap = _numero(f.get("Aporte"))
        if ap is None:
            continue
        ancho = abs(ap) / tope * 50
        clase = "pos" if ap > 0 else "neg"
        filas.append(f'<span>{escape(str(f["Señal"]))}</span>'
                     f'<div class="fp-eje"><i class="{clase}" style="width:{ancho:.1f}%"></i></div>'
                     f'<em>{ap:+.2f}</em>')
    lista = lambda xs: ", ".join(escape(x) for x in xs) or "ninguna"
    lado = "".join(f'<figure><img src="{escape(u)}" alt="{escape(c)}"><figcaption>{escape(c)}</figcaption></figure>'
                   for u, c in ((imagen_a, consulta), (imagen_b, candidato)) if u)
    return (
        f'<div class="fp-exp-titulo"><b>{escape(consulta)}</b> frente a <b>{escape(candidato)}</b>: '
        f'probabilidad de revisar <b class="fp-p">{prob * 100:.0f}%</b></div>'
        '<div class="fp-motivos">'
        f'<div>▲ <b>Lo que más la sube:</b> {lista(a_favor)}</div>'
        f'<div>▼ <b>Lo que más la baja:</b> {lista(en_contra)}</div></div>'
        f'<div class="fp-aportes">{"".join(filas)}</div>'
        '<div class="fp-nota">Cada barra es cuánto empuja esa señal: a la derecha hacia "revisar", a la izquierda '
        'hacia "no revisar". "Sin dato" indica que la señal no se pudo calcular (por ejemplo, sin imágenes).</div>'
        + (f'<div class="fp-lado">{lado}</div>' if lado else ""))


def progreso(p: dict, anotador: str | None = None, hay_modelo_B: bool = False) -> str:
    """Tres contadores de la cola de revisión: los pares de la persona y lo que le falta al equipo.

    Si la app ya usa un Modelo B (`hay_modelo_B`), la nota invita a etiquetar para reentrenarlo.

    `p` es el resultado de ColaRevision.progreso, por ejemplo
    {"tuyos": 12, "meta": 30, "positivos": 4, "negativos": 25, "minimo": 10, "listo": False}.
    """
    def caja(titulo: str, valor: int, tope: int) -> str:
        ancho = min(valor / tope, 1) * 100 if tope else 0
        clase = ' class="fp-ok"' if valor >= tope else ""
        return (f'<div{clase}><span>{escape(titulo)}</span><b>{valor} <small>de {tope}</small></b>'
                f'<div class="fp-barra"><i style="width:{ancho:.0f}%"></i></div></div>')

    quien = (anotador or "").strip() or "anónimo"   # caja() lo escapa
    faltan_pos = max(p["minimo"] - p["positivos"], 0)
    faltan_neg = max(p["minimo"] - p["negativos"], 0)
    partes = [f"<b>{n}</b> {txt}" for n, txt in ((faltan_pos, "con «Posible copia»"),
                                                (faltan_neg, "con «Similar» o «No similar»")) if n]
    if hay_modelo_B:
        nota = ("El <b>Modelo B</b> ya está entrenado con el lote del equipo. Cada par que etiquetes aquí "
                "sirve para reentrenarlo y mejorarlo")
        nota += (". ✅ Ya hay pares suficientes para reentrenarlo; cada par extra mejora la evaluación."
                 if p["listo"] else ": para la próxima versión faltan " + " y ".join(partes) + ".")
    elif p["listo"]:
        nota = "✅ Ya hay etiquetas suficientes para entrenar el <b>Modelo B</b>. Cada par extra mejora la evaluación."
    else:
        nota = "Para entrenar el <b>Modelo B</b> al equipo le faltan " + " y ".join(partes) + "."
    return ('<div class="fp-prog">'
            + caja(f"Tus pares ({quien})", p["tuyos"], p["meta"])
            + caja("Equipo · «Posible copia»", p["positivos"], p["minimo"])
            + caja("Equipo · «Similar» y «No similar»", p["negativos"], p["minimo"])
            + f'</div><div class="fp-prog-nota">{nota}</div>')


def _ficha(j: dict, letra: str) -> str:
    nombre = escape(j.get("nombre") or "")
    imagen = (f'<img class="fp-foto" src="{escape(j["imagen"])}" alt="{nombre}">' if j.get("imagen")
              else '<div class="fp-sinimg">sin imagen</div>')
    meta = " · ".join(escape(str(x)) for x in (j.get("desarrollador"), j.get("fecha"), j.get("generos")) if x)
    texto = (j.get("texto") or "").strip()
    texto = escape(texto[:600] + ("…" if len(texto) > 600 else ""))
    enlace = (f'<a class="fp-abrir" href="{escape(j["enlace"])}" target="_blank" rel="noopener">'
              'Abrir en Steam ↗</a>' if j.get("enlace") else "")
    return (f'<div class="fp-juego">{imagen}'
            f'<div class="fp-titulo"><span class="fp-rank">{letra}</span>{nombre}</div>'
            f'<div class="fp-meta">{meta}</div><div class="fp-desc">{texto}</div>{enlace}</div>')


def par_cola(a: dict, b: dict) -> str:
    """Los dos juegos de un par, lado a lado, con lo necesario para decidir sin ver puntajes.

    `a` y `b` son fichas de ColaRevision: nombre, desarrollador, fecha, generos, texto, imagen y enlace.
    """
    return f'<div class="fp-par">{_ficha(a, "A")}{_ficha(b, "B")}</div>'


def pasos(lista: list[tuple[str, str]]) -> str:
    """Tira de pasos numerados. `lista` es [(título, texto), ...]; por ejemplo [("Compara", "Mira los dos juegos.")]."""
    return '<div class="fp-pasos">' + "".join(
        f'<div><span class="fp-rank">{n}</span><div><b>{escape(titulo)}</b><span class="t">{escape(texto)}</span></div></div>'
        for n, (titulo, texto) in enumerate(lista, start=1)) + "</div>"


def ultimos(casos: pd.DataFrame, anotador: str | None, n: int = 8) -> str:
    """Los últimos `n` casos que guardó la persona, del más nuevo al más antiguo.

    `casos` es la tabla de ColaRevision.casos (columnas anotador, consulta, juego_comparado y etiqueta).
    """
    nombre = (anotador or "").strip().lower()
    if not nombre:
        return vacio("Escribe tu nombre arriba para ver los casos que has guardado.")
    mios = casos[casos["anotador"].str.strip().str.lower() == nombre].tail(n).iloc[::-1]
    if mios.empty:
        return vacio("Todavía no has guardado casos con este nombre.")
    filas = "".join(f'<span>{escape(str(r.consulta))} ↔ {escape(str(r.juego_comparado))}</span>'
                    f'<em>{escape(str(r.etiqueta))}</em>' for r in mios.itertuples())
    return f'<div class="fp-ultimos">{filas}</div>'
