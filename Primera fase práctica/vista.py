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
@media (max-width:820px){
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
