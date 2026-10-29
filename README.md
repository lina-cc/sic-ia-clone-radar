# SIC IA Clone Radar 🎮🔍

**Sistema de detección de similitudes entre videojuegos (Proyecto SIC 2026)**

Este repositorio contiene la investigación, documentación y prototipo experimental asistido por Inteligencia Artificial para identificar y documentar patrones de similitud y posibles réplicas entre videojuegos utilizando información técnica y análisis estadístico.

> ⚠️ **Aviso metodológico y ético:** La similitud técnica no equivale a plagio. Compartir mecánicas, convenciones de género o vocabulario es parte natural de la industria. Este sistema actúa como herramienta de **evidencia técnica preliminar, reproducible y explicable** para orientar la revisión de especialistas humanos.

---

## 📂 Estructura del Repositorio

```plaintext
sic-ia-clone-radar/
├── Documentos/
│   ├── Clase 9/                   # Hoja de trabajo y actividades Capstone.
│   ├── Proyecto Final/            # Guías oficiales, pautas y rúbricas SIC 2026.
│   ├── Informe mirror.docx        # Documento del proyecto: antecedentes, problemática y técnicas.
│   └── pitch_5_minutos.md         # Guion estructurado del pitch oral.
├── Primera fase práctica/
│   ├── app.py                     # Interfaz web interactiva en Gradio.
│   ├── similitud.py               # Lógica de cálculo TF-IDF y similitud coseno.
│   ├── LEEME_PROBADORES.md        # Guía para evaluadores humanos.
│   ├── README.md                  # Instrucciones específicas de ejecución del prototipo.
│   ├── requirements.txt           # Dependencias para pip.
│   └── environment.yml            # Configuración de entorno Conda.
├── FairPlay_AI_DBSCAN.ipynb        # Notebook experimental: TF-IDF vs. multimodal con DBSCAN.
└── .gitignore
```

---

## 🚀 Primera Fase Práctica (Línea Base TF-IDF)

La primera etapa del proyecto implementa una línea base de comparación léxica basada en **TF-IDF + Similitud Coseno** sobre descripciones de videojuegos:

1. **Buscar similares:** Consulta videojuegos dentro del dataset y muestra los títulos más cercanos con sus términos clave compartidos.
2. **Comparar dos juegos:** Comparación directa 1 a 1 desglosando el aporte individual de cada palabra a la similitud final.
3. **Texto nuevo:** Búsqueda abierta introduciendo descripciones arbitrarias en lenguaje natural.
4. **Validación humana:** Módulo integrado para etiquetar casos (*Similar*, *No similar*, *Posible copia*) para alimentar el estudio empírico.

### Instalación y Ejecución

Consulta los detalles completos en [`Primera fase práctica/README.md`](Primera%20fase%20práctica/README.md).

```bash
# Con Conda
conda env create -f "Primera fase práctica/environment.yml"
conda activate similitud-juegos

# O con entorno virtual Python (3.11+)
python -m venv .venv
# En Windows:
.venv\Scripts\activate
pip install -r "Primera fase práctica/requirements.txt"

# Ejecución
cd "Primera fase práctica"
python app.py
```

---

## 🧪 Experimentación Multimodal con DBSCAN (`FairPlay_AI_DBSCAN.ipynb`)

El repositorio incluye un notebook experimental que evalúa cuantitativamente la hipótesis central del proyecto sobre un dataset controlado con clones de *Escape the Walls*, *Farm Tycoon*, *Racing Legends* y juegos señuelo del mismo género:
* **Línea Base (TF-IDF + DBSCAN):** Alcanza un $F_1 = 0.636$ y precisión de $47.9\%$ debido a falsos positivos entre juegos que comparten vocabulario de género sin ser réplicas.
* **Modelo Base Multimodal (Texto + Imagen + DBSCAN):** Al combinar distancias léxicas con embeddings visuales de CNN, la precisión se eleva al **$100\%$** con un $F_1 = 0.912$ y $ARI = 0.883$, aislando los clones reales de los señuelos independientes.

---

## 🔮 Trabajo Futuro y Ampliaciones

Siguiendo el marco del proyecto SIC 2026, el sistema incorporará de manera complementaria:
- **Embeddings semánticos:** Modelos de lenguaje pre-entrenados (Hugging Face) para detectar relaciones conceptuales aún con diferente vocabulario.
- **Visión por computadora (CNN con Transfer Learning):** Modelos como ResNet o MobileNet para análisis comparativo de capturas de pantalla, arte e interfaces de usuario.
- **Grafos de Flujo de Control (CFG):** Comparación estructural y de flujo lógico en código fuente o descompilado.
