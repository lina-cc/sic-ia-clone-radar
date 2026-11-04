# SIC IA Clone Radar 🎮🔍

**FairPlay AI: sistema de detección de similitudes entre videojuegos (Proyecto capstone SIC 2026)**

Equipo: Ignacio Hidalgo, Sergio Rebolledo, Catalina Caris, Avelyn García.

Este repositorio contiene la investigación, la documentación y el prototipo de un sistema que identifica y documenta similitudes entre videojuegos de Steam usando descripciones, imágenes y metadatos, con un modelo entrenado y evaluado por el equipo.

> ⚠️ **Aviso metodológico y ético:** la similitud técnica no equivale a plagio. Compartir mecánicas, convenciones de género o vocabulario es parte natural de la industria. Este sistema entrega **evidencia técnica preliminar, reproducible y explicable** para orientar la revisión de especialistas humanos.

📘 **¿Primera vez aquí?** Lee la [Guía técnica](docs/GUIA_TECNICA.md): explica el flujo de datos, cada señal, el modelo, las métricas, el stack y cómo correr todo.

---

## 📂 Estructura del repositorio

```plaintext
sic-ia-clone-radar/
├── FairPlay_AI_Clasificador_Pares.ipynb  # ⭐ Notebook principal: datos reales de Steam + modelo entrenado.
├── FairPlay_AI_DBSCAN.ipynb              # Primer experimento con datos simulados (antecedente).
├── Primera fase práctica/
│   ├── app.py                            # App web en Gradio (también desplegable en Hugging Face Spaces).
│   ├── modelo.py                         # Usa el modelo entrenado: candidatos y explicación de pares.
│   ├── senales.py                        # Señales por par, calculadas igual que en el notebook.
│   ├── similitud.py                      # Lógica de la línea base TF-IDF + similitud coseno.
│   ├── LEEME_PROBADORES.md               # Guía para quienes prueban la app.
│   ├── README.md                         # Instrucciones de la app.
│   ├── requirements.txt                  # Dependencias de la app (versiones fijas).
│   └── environment.yml                   # Entorno Conda equivalente.
├── tests/                                # Tests automáticos (pytest).
├── docs/
│   └── GUIA_TECNICA.md                   # Documentación técnica completa.
├── Documentos/                           # Informe, pitch y hoja de trabajo del equipo.
├── .github/workflows/tests.yml           # Corre los tests en cada push (GitHub Actions).
├── requirements-dev.txt                  # Dependencias para desarrollar (app + pytest).
├── requirements-notebook.txt             # Dependencias del notebook fuera de Colab.
└── pytest.ini
```

Los datos de Steam (`data/`) y los casos etiquetados (`casos/`) **no** se suben al repositorio.

---

## ⭐ Clasificador de pares con datos reales (`FairPlay_AI_Clasificador_Pares.ipynb`)

Responde la pregunta: **¿este par de juegos merece revisión humana?**

1. **Catálogo real de Steam** (el parquet del equipo o el dataset de Kaggle).
2. **Pares candidatos:** para cada juego, sus vecinos más cercanos por TF-IDF y por embeddings de texto.
3. **Señales por par:**
   * Texto: TF-IDF y embeddings multilingües (Hugging Face).
   * Imágenes reales (header y capturas): CLIP y hash perceptual.
   * Título, tags y fechas.
4. **Etiquetas:** humanas (plantilla de registro y app) y débiles (automáticas).
5. **Modelo A:** regresión logística que aprende a reconocer clones **sin mirar el texto**, para detectar clones con la descripción reescrita.
6. **Modelo B:** usa todas las señales y se entrena solo con etiquetas humanas.
7. **Evaluación** contra la línea base TF-IDF (PR-AUC, precisión@20), con validación cruzada por familias.
8. **Explicación** de cada par (palabras compartidas, peso de cada señal, imágenes lado a lado), búsqueda por juego y exportación de pares para etiquetar.
9. **Exporta un paquete** con el modelo y todo lo ya calculado, para que la app lo use sin GPU.

Se corre en Google Colab con GPU. Las instrucciones paso a paso están en la [Guía técnica](docs/GUIA_TECNICA.md#7-cómo-correr-cada-parte).

---

## 🚀 App web (Gradio)

**Modelo entrenado:** busca candidatos para un juego con el modelo del notebook, muestra la probabilidad de que cada par merezca revisión, el valor de cada señal y las imágenes de Steam, y explica qué señales subieron o bajaron la probabilidad. Se activa copiando el paquete que exporta el notebook (sección 11) a `Primera fase práctica/modelo/`.

**Línea base TF-IDF:**

1. **Buscar similares:** muestra los juegos más cercanos y los términos clave compartidos.
2. **Comparar dos juegos:** desglosa el aporte de cada palabra a la similitud.
3. **Texto nuevo:** busca a partir de una descripción escrita en inglés.
4. **Validación humana:** etiqueta casos (*Similar*, *No similar*, *Posible copia*). Esas etiquetas alimentan el notebook principal.

```bash
# Con Conda
conda env create -f "Primera fase práctica/environment.yml"
conda activate similitud-juegos

# O con un entorno virtual (Python 3.12)
python -m venv .venv
.venv\Scripts\activate            # En Mac/Linux: source .venv/bin/activate
pip install -r "Primera fase práctica/requirements.txt"

# Ejecutar
cd "Primera fase práctica"
python app.py
```

Más detalles, incluido el despliegue en Hugging Face Spaces, en [`Primera fase práctica/README.md`](Primera%20fase%20práctica/README.md).

---

## ✅ Tests

```bash
pip install -r requirements-dev.txt
pytest
```

34 tests que comprueban la línea base (que el clon quede primero, puntajes simétricos, caché, homónimos), las señales por par (imágenes idénticas, datos faltantes), el uso del modelo entrenado (candidatos ordenados, explicación legible, Modelo A cuando no hay B) y la app (guardar casos, construir la interfaz con y sin modelo). Se corren solos en GitHub en cada push.

---

## 🧪 Primer experimento: DBSCAN con datos simulados (`FairPlay_AI_DBSCAN.ipynb`)

Evaluó la hipótesis central sobre un catálogo simulado de 28 juegos (clones de *Escape the Walls*, *Farm Tycoon*, *Racing Legends* y señuelos del mismo género):

* **Línea base (TF-IDF + DBSCAN):** F1 = 0,636 y precisión de 47,9 %, por falsas alarmas entre juegos del mismo género.
* **Texto + imagen simulada + DBSCAN:** F1 = 0,912, precisión de 100 % y ARI = 0,883.

**Limitación:** los "embeddings de imagen" de ese experimento eran simulados, y los clones compartían un centro visual por construcción. Por eso el resultado muestra que *combinar señales ayuda si la imagen es informativa*, pero no mide el rendimiento con juegos reales. Esa es la razón del notebook principal.

---

## 🔮 Trabajo futuro

* Comparar videos y más capturas por juego.
* Sumar otras plataformas (Roblox, itch.io).
* **Comparación de código** (grafos de flujo de control), solo cuando exista acceso legítimo al código fuente.
