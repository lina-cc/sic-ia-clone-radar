<p align="center">
  <img src="docs/img/logo.svg" alt="FairPlay AI · Clone Radar" width="420">
</p>

# FairPlay AI · SIC IA Clone Radar

**Sistema que prioriza qué pares de juegos de Steam vale la pena que revise una persona por posible réplica, combinando su descripción, sus imágenes y sus metadatos.**

Proyecto capstone del **Samsung Innovation Campus 2026 · Inteligencia Artificial**.
Equipo: **Ignacio Hidalgo, Sergio Rebolledo, Catalina Caris y Avelyn García**.

[![tests](https://github.com/lina-cc/sic-ia-clone-radar/actions/workflows/tests.yml/badge.svg)](https://github.com/lina-cc/sic-ia-clone-radar/actions/workflows/tests.yml)
[![Abrir notebook principal en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/lina-cc/sic-ia-clone-radar/blob/main/FairPlay_AI_Clasificador_Pares.ipynb)

> ⚠️ **La similitud no es plagio.** Compartir mecánicas, convenciones de género o vocabulario es parte natural de la industria. FairPlay AI **no acusa ni decide**: ordena candidatos y entrega evidencia técnica, reproducible y explicable para que una persona especialista los revise.

<p align="center">
  <img src="docs/img/app_modelo.png" alt="App de FairPlay AI: candidatos para Stardew Valley ordenados por probabilidad de revisión, con el valor de cada señal" width="900">
  <br><sub>La app buscando candidatos para <i>Stardew Valley</i> con el modelo entrenado. Cada columna es una señal entre 0 (nada parecido) y 1 (idéntico).</sub>
</p>

### ⏱️ En 30 segundos

| | |
|---|---|
| **Qué entra** | El nombre de un juego de Steam. |
| **Qué hace** | Busca los juegos más parecidos entre ~138 mil y mide cada par con 8 señales: texto, imágenes, título, tags, fechas y estudio. |
| **Qué sale** | Una lista ordenada por **probabilidad de que el par merezca revisión**, con la explicación de cada número. |
| **Quién decide** | Siempre una persona. Sus decisiones se guardan y vuelven a entrenar el modelo. |

---

## 📑 Contenido

1. [El problema](#-el-problema)
2. [Qué hace FairPlay AI](#-qué-hace-fairplay-ai)
3. [Cómo funciona](#️-cómo-funciona)
4. [Un ejemplo paso a paso](#-un-ejemplo-paso-a-paso)
5. [Arquitectura](#️-arquitectura)
6. [Resultados](#-resultados)
7. [Pruébalo](#-pruébalo)
8. [Estructura del repositorio](#-estructura-del-repositorio)
9. [Datos y ética](#-datos-y-ética)
10. [Limitaciones](#-limitaciones)
11. [Estado del proyecto y próximos pasos](#️-estado-del-proyecto-y-próximos-pasos)
12. [Antecedente: primer experimento con datos simulados](#-antecedente-primer-experimento-con-datos-simulados)
13. [Preguntas frecuentes](#-preguntas-frecuentes)
14. [Glosario](#-glosario)
15. [Documentación](#-documentación)

---

## 🎯 El problema

En Steam se publican miles de juegos al año. Cuando un juego independiente tiene éxito, aparecen réplicas que copian su descripción, su arte o su nombre. Casos conocidos como *Escape the Walls*, *Meccha Chameleon* o *Needle In A Haystack* muestran que el desarrollador afectado suele enterarse tarde y sin pruebas ordenadas.

Revisar el catálogo a mano es imposible (~138 mil juegos), y una búsqueda por palabras se equivoca en las dos direcciones:

* **Falsas alarmas:** dos juegos de granjas usan el mismo vocabulario sin que uno copie al otro.
* **Clones que se escapan:** una réplica puede reescribir la descripción y reutilizar las capturas.

**Pregunta que responde el sistema:** dado un par de juegos, *¿merece una revisión humana?*

---

## 💡 Qué hace FairPlay AI

<p align="center">
  <img src="docs/img/flujo.svg" alt="Flujo: catálogo de Steam, vecinos cercanos, 8 señales por par, regresión logística, app con candidatos ordenados y revisión humana que alimenta el modelo" width="900">
</p>

1. **Datos:** toma el catálogo público de Steam (137.976 juegos tras la limpieza) con descripción, imágenes, tags, desarrollador y fecha.
2. **Candidatos:** para cada juego busca sus vecinos más cercanos por palabras (TF-IDF) y por significado (embeddings). Así no compara todos contra todos.
3. **Señales:** para cada par calcula 8 medidas de parecido: texto, imágenes, título, tags, fechas y estudio.
4. **Modelo:** una regresión logística combina las señales en una **probabilidad de que el par merezca revisión**.
5. **App:** muestra los candidatos ordenados, el valor de cada señal, las imágenes lado a lado y **por qué** el modelo dio esa probabilidad.
6. **Ciclo humano:** el equipo etiqueta pares en la app o en un Excel, y esas etiquetas entrenan y evalúan el modelo final.

<p align="center">
  <img src="docs/img/app_uso.gif" alt="Uso de la app: se busca Stardew Valley, aparecen los candidatos ordenados, se abre la explicación del primero y se guarda el caso como Similar" width="820">
  <br><sub>La app en 17 segundos: buscar, leer la explicación y guardar la decisión. Las imágenes de los juegos se ocultan porque son arte de Steam.</sub>
</p>

---

## ⚙️ Cómo funciona

### Las señales

Cada una falla en casos distintos; por eso se combinan. Todas valen entre 0 y 1, salvo la distancia entre fechas.

| Señal | Qué pregunta responde | Cómo se calcula |
|---|---|---|
| `tfidf_cos` | ¿Usan **las mismas palabras**? | TF-IDF da más peso a las palabras raras; se mide la similitud coseno. |
| `emb_cos` | ¿Dicen **lo mismo** con otras palabras? | Modelo de lenguaje multilingüe (`paraphrase-multilingual-MiniLM-L12-v2`). |
| `img_cos` | ¿Sus imágenes **se ven parecidas**? | CLIP (`clip-ViT-B-32`) sobre la imagen de cabecera y hasta 3 capturas; se guarda el par más parecido. |
| `phash_sim` | ¿Comparten una imagen **casi idéntica**? | Hash perceptual de 64 bits: detecta capturas reutilizadas aunque cambie el tamaño. |
| `titulo_sim` | ¿Los **nombres** se parecen? | Comparación de las palabras del título, sin importar el orden. |
| `tags_jaccard` | ¿Comparten **géneros y tags**? | Tags en común ÷ tags totales. |
| `log_dias` | ¿Salieron **cerca en el tiempo**? | Logaritmo de los días entre lanzamientos. |
| `mismo_dev` | ¿Son del **mismo estudio**? | Una secuela propia no es un clon. |

### Las etiquetas

Un modelo necesita ejemplos de "sí merece revisión" y "no la merece":

* **Etiquetas débiles (automáticas):** pares de estudios distintos con descripción casi idéntica (`tfidf_cos ≥ 0,90` y `emb_cos ≥ 0,80`) como positivos, y pares del mismo tema con texto distinto como negativos. Hay miles, pero son aproximadas.
* **Etiquetas humanas:** el equipo revisa pares con criterios escritos en la [Guía de etiquetado](docs/GUIA_ETIQUETADO.md). El notebook genera un **lote de 100 pares** en Excel (lista desplegable, enlaces a Steam) y la app permite guardar casos con un clic.

### Dos modelos, para no hacer trampa

| | Modelo A | Modelo B |
|---|---|---|
| **Señales** | Imágenes, título, tags y fechas (**sin texto**) | Todas |
| **Etiquetas** | Débiles | Humanas |
| **Para qué** | Funciona desde el día 1. Como las etiquetas débiles salen del texto, el modelo **no puede ver el texto**: si lo viera, solo aprendería la regla que las creó. Así aprende a reconocer clones aunque la descripción esté reescrita. | Es el modelo final. Se activa solo cuando hay al menos 10 etiquetas humanas de cada clase. |

Ambos son una **regresión logística** (imputación de vacíos → estandarización → regresión), elegida porque es interpretable: el aporte de cada señal se puede mostrar en la app. Se compara con *gradient boosting* como referencia.

### Evaluación sin fugas

* **Validación cruzada por familias** (`GroupKFold`): un juego y sus clones nunca quedan repartidos entre entrenamiento y prueba.
* **Métricas pensadas para revisar pocos casos:** PR-AUC (útil cuando los positivos son pocos) y **precisión@20** (de los 20 pares que el modelo pone arriba, cuántos valían la pena), siempre contra la línea base TF-IDF y el azar.

### Explicación de cada par

Al elegir un candidato, la app muestra qué señales suben y cuáles bajan la probabilidad, y cuánto empujó cada una (debajo aparecen las imágenes de ambos juegos lado a lado; en las capturas se ocultan porque son arte de Steam):

<p align="center">
  <img src="docs/img/app_explicacion.png" alt="Explicación del par Stardew Valley y Cornucopia: aporte de cada señal a la probabilidad" width="800">
</p>

---

## 🔍 Un ejemplo paso a paso

Qué pasa cuando alguien busca ***Stardew Valley*** (ConcernedApe, 2016). Son valores reales del Modelo A.

**Paso 1 · Candidatos.** De 137.976 juegos, el sistema se queda con los vecinos más cercanos por palabras y por significado: hasta 20 juegos en vez de todo el catálogo.

**Paso 2 · Señales.** Para cada candidato se miden las señales. Estas son las del primero de la lista, *Cornucopia®* (2023, otro estudio):

| Señal | Valor | Lectura |
|---|---|---|
| Géneros y tags en común | 0,71 | Comparten 7 de cada 10 tags: muy alto. |
| Imágenes parecidas (CLIP) | 0,57 | Parecido visual moderado. |
| Imagen casi idéntica (hash) | 0,50 | No comparten ninguna imagen igual: 0,50 es lo que dan dos imágenes cualquiera. |
| Títulos parecidos | 0,16 | Los nombres no se parecen. |
| Días entre lanzamientos | ~2.700 | Salieron con más de 7 años de diferencia. |

**Paso 3 · El modelo suma.** Cada señal empuja la probabilidad hacia arriba o hacia abajo. El aporte es positivo si el valor está **por encima** de lo habitual en los pares de entrenamiento, y negativo si está por debajo:

| | Aporte |
|---|---|
| Punto de partida del modelo | −0,29 |
| Géneros y tags en común | **+0,73** |
| Imágenes parecidas (CLIP) | −0,61 |
| Imagen casi idéntica (hash) | −0,31 |
| Títulos parecidos | −0,12 |
| Distancia entre fechas | +0,07 |
| **Suma** | **−0,53** |

La regresión logística convierte esa suma en una probabilidad: 1 ÷ (1 + e^0,53) = **0,37**.

**Paso 4 · Lectura humana.** 37 % es el valor más alto de la lista, pero es bajo. El modelo dice: *"es el más parecido que encontré, sobre todo por los tags; las imágenes y el nombre no apuntan a una copia"*. La persona abre ambos juegos en Steam, compara y guarda su decisión (en la animación de arriba, **Similar**: mismo género, arte distinto). Esa decisión queda como etiqueta humana.

> Este ejemplo muestra justo el caso difícil: dos juegos del mismo género se parecen mucho en tags sin que uno copie al otro. Por eso el sistema explica cada número y no decide solo.

---

## 🏗️ Arquitectura

Dónde corre cada parte y cómo viajan los datos. Todo usa servicios gratuitos.

```mermaid
flowchart LR
    K[("Kaggle<br>catálogo de Steam")] --> NB
    IMG[("Tienda de Steam<br>imágenes públicas")] --> NB

    subgraph COLAB["Google Colab · GPU"]
        NB["Notebook principal<br>señales · entrenamiento · evaluación"]
    end

    NB -- "paquete del modelo" --> HF[("Hugging Face<br>dataset privado")]
    HF -- "se descarga al iniciar" --> APP

    subgraph OCI["Servidor OCI · siempre encendido"]
        CADDY["Caddy<br>HTTPS"] --> APP["App Gradio<br>candidatos y explicación"]
    end

    EQ(["Equipo<br>navegador + contraseña"]) --> CADDY
    APP -- "casos marcados" --> DRIVE[("Google Drive<br>etiquetas humanas")]
    XLS["Excel del lote<br>100 pares"] --> DRIVE
    DRIVE -- "reentrenar · Modelo B" --> NB
```

| Pieza | Qué hace | Por qué ahí |
|---|---|---|
| **Google Colab** | Calcula embeddings e imágenes, entrena y evalúa. | Necesita GPU y solo se usa de vez en cuando. |
| **Hugging Face (privado)** | Guarda el paquete del modelo (~630 MB). | Los datos de Steam no pueden ir en este repositorio público. |
| **Servidor OCI** | Muestra la app las 24 horas, con HTTPS y contraseña. | Solo carga resultados ya calculados: le basta 1 CPU y 6 GB de RAM. |
| **Google Drive** | Reúne las etiquetas del equipo. | El notebook las lee directo desde ahí. |

El círculo se cierra cuando las etiquetas vuelven al notebook: así se entrena el **Modelo B**. Los comandos de cada paso están en la [guía del despliegue](despliegue/oci/README.md).

---

## 📊 Resultados

Corrida completa en Google Colab (GPU T4), 4 de noviembre de 2026, sobre **137.976 juegos** de Steam. Todavía **no hay etiquetas humanas**, así que lo que se mide es el **Modelo A** con validación cruzada sobre 3.000 pares con etiquetas débiles (750 positivos):

<p align="center">
  <img src="docs/img/resultados.png" alt="PR-AUC: azar 0,247, regresión logística 0,363, gradient boosting 0,415. Precisión@20: 0,30, 0,45 y 0,50" width="820">
</p>

| Modelo | PR-AUC | ROC-AUC | Precisión@20 |
|---|---|---|---|
| Modelo A · regresión logística | 0,363 | 0,664 | 0,45 |
| Modelo A · gradient boosting | 0,415 | 0,722 | 0,50 |
| Azar (referencia) | 0,247 | 0,499 | 0,30 |

**¿Qué señales pesan más?** En la regresión logística, la que más empuja es la coincidencia de géneros y tags, seguida por el parecido de las imágenes:

<p align="center">
  <img src="docs/img/pesos_senales.png" alt="Coeficientes: géneros y tags 1,02; imágenes CLIP 0,27; hash 0,14; títulos 0,12; distancia entre fechas 0,05" width="680">
</p>

**Cómo leer estos números:**

* ✅ **Lo que muestran:** sin mirar el texto, el modelo ordena los pares mejor que el azar (+47 % en PR-AUC, de 6 a 9 aciertos de cada 20 con la regresión logística). Las imágenes aportan información real.
* ⚠️ **Lo que no muestran:** las etiquetas débiles salen del texto, así que esto no mide "detectar copias". La evaluación que vale para el informe es la del **Modelo B con etiquetas humanas** (pendiente: ver [próximos pasos](#️-estado-del-proyecto-y-próximos-pasos)).
* 🚫 **Corrida descartada:** una versión anterior dio PR-AUC 0,669, pero estaba inflada: a los negativos les faltaba la imagen mucho más que a los positivos y el modelo aprendió "sin imagen = no es copia". Se corrigió entrenando solo con pares que tienen imagen. **No citar ese número.**

---

## 🚀 Pruébalo

### Opción 1 · App publicada (lo más rápido)

La app está en línea las 24 horas en un servidor gratuito de Oracle Cloud. Pide un usuario y una contraseña porque guarda las etiquetas que entrenan el modelo.

**La dirección y la contraseña las entrega el equipo** (no se publican en el repositorio). Cómo está armado el servidor: [guía del despliegue](despliegue/oci/README.md).

### Opción 2 · Demo en Colab (sin instalar nada)

1. Abrir [`FairPlay_AI_Demo.ipynb`](FairPlay_AI_Demo.ipynb) en Google Colab (no necesita GPU).
2. *Entorno de ejecución → Ejecutar todo* y aceptar el acceso a Google Drive.
3. A los ~5 minutos aparece un enlace `https://….gradio.live`: ábrelo y compártelo.

El enlace funciona mientras la pestaña de Colab siga abierta (hasta una semana). Requiere que el paquete del modelo esté en `MyDrive/fairplay/salidas/paquete_app/` (lo crea el notebook principal). Los casos que se marquen en la demo se guardan en Drive. Para etiquetar en equipo conviene la app publicada, que reúne todos los casos en un solo archivo.

> Hugging Face Spaces con Gradio ahora exige la suscripción PRO, por eso la demo usa el enlace temporal de Gradio. Alternativas en la [Guía técnica §8](docs/GUIA_TECNICA.md#8-publicar-la-demo).

### Opción 3 · Entrenar el modelo (notebook principal)

1. Abrir [`FairPlay_AI_Clasificador_Pares.ipynb`](FairPlay_AI_Clasificador_Pares.ipynb) en Colab con el botón de arriba.
2. *Entorno de ejecución → Cambiar tipo de entorno → GPU T4*.
3. *Ejecutar todo* y aceptar el acceso a Drive.

Descarga el dataset de Kaggle, calcula embeddings e imágenes (todo queda en caché en Drive), entrena, evalúa, genera el lote para etiquetar y **exporta el paquete** que usa la app. La primera corrida es larga (solo las imágenes de cabecera de todo el catálogo toman unos 45 minutos); las siguientes reutilizan la caché.

### Opción 4 · App en tu computador

```bash
python -m venv .venv
.venv\Scripts\activate            # Mac/Linux: source .venv/bin/activate
pip install -r "Primera fase práctica/requirements.txt"
cd "Primera fase práctica"
python app.py                     # abre http://127.0.0.1:7860
```

Sin más pasos funciona la **línea base TF-IDF**. Para la pestaña **Modelo entrenado**, copia los cuatro archivos de `MyDrive/fairplay/salidas/paquete_app/` a `Primera fase práctica/modelo/`. En Windows, `.\demo.ps1` hace todo esto y además intenta abrir un enlace público. Detalles en el [README de la app](Primera%20fase%20práctica/README.md).

| Pestaña | Para qué sirve |
|---|---|
| **Modelo entrenado** | Candidatos para un juego, ordenados por probabilidad de revisión, con señales, imágenes y explicación. |
| Buscar similares | Línea base: juegos más parecidos por palabras y los términos que comparten. |
| Comparar dos juegos | Línea base: cuánto aporta cada palabra al parecido de dos juegos concretos. |
| Texto nuevo | Línea base: busca a partir de una descripción escrita (en inglés). |

En todas se puede guardar un caso (*Similar*, *No similar*, *Posible copia*) que se suma a las etiquetas humanas.

### Opción 5 · Ayudar a etiquetar

Sigue la [Guía de etiquetado](docs/GUIA_ETIQUETADO.md): copia `salidas/lote_para_etiquetar.xlsx` a `MyDrive/fairplay/data/lote_etiquetado.xlsx`, complétalo con la lista desplegable y vuelve a correr el notebook.

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

43 tests comprueban la línea base (el clon queda primero, puntajes simétricos, caché), las señales por par (imágenes idénticas, datos faltantes), el modelo entrenado (candidatos ordenados, explicación legible, versión de scikit-learn incompatible) y la app (guardar casos, construir la interfaz con y sin modelo, descargar desde Hugging Face, pedir contraseña solo si está configurada) y las tarjetas de la interfaz. Se corren solos en GitHub Actions en cada push.

---

## 📂 Estructura del repositorio

```plaintext
sic-ia-clone-radar/
├── FairPlay_AI_Clasificador_Pares.ipynb  # ⭐ Notebook principal: datos reales, señales, modelo, evaluación y exportación.
├── FairPlay_AI_Demo.ipynb                # Abre la app en Colab con un enlace público temporal.
├── FairPlay_AI_DBSCAN.ipynb              # Primer experimento con datos simulados (antecedente).
├── Primera fase práctica/                # La app web.
│   ├── app.py                            # Interfaz Gradio y registro de casos.
│   ├── vista.py                          # Tema, estilos y tarjetas HTML de la interfaz.
│   ├── modelo.py                         # Carga el paquete del modelo, busca candidatos y explica pares.
│   ├── senales.py                        # Señales por par, calculadas igual que en el notebook.
│   ├── similitud.py                      # Línea base TF-IDF + similitud coseno.
│   ├── demo.ps1                          # Un clic para abrir la app con enlace público (Windows).
│   ├── assets/                           # Logo e ícono de la app.
│   ├── LEEME_PROBADORES.md               # Guía para quienes prueban la app.
│   ├── README.md                         # Instrucciones de la app.
│   ├── requirements.txt                  # Dependencias con versiones fijas (Python 3.12).
│   └── environment.yml                   # Entorno Conda equivalente.
├── docs/
│   ├── GUIA_TECNICA.md                   # Documentación técnica completa (stack, señales, modelo, métricas).
│   ├── GUIA_ETIQUETADO.md                # Criterios y flujo para etiquetar pares.
│   └── img/                              # Logo e imágenes de este README.
├── despliegue/oci/                       # Servidor gratuito en Oracle Cloud: instalación, HTTPS y comandos para reentrenar.
├── tests/                                # Tests automáticos (pytest).
├── Documentos/                           # Informe, pitch y hoja de trabajo del equipo.
├── .github/workflows/tests.yml           # Corre los tests en cada push (GitHub Actions).
├── requirements-dev.txt                  # Dependencias para desarrollar (app + pytest).
└── requirements-notebook.txt             # Dependencias del notebook fuera de Colab.
```

### Stack

| Pieza | Uso |
|---|---|
| Python 3.12 · pandas · NumPy | Base de todo el proyecto. |
| scikit-learn 1.9.1 | TF-IDF, regresión logística, validación cruzada y métricas (versión fija en notebook y app). |
| sentence-transformers | Embeddings de texto multilingües y CLIP para imágenes. |
| imagehash · Pillow | Hash perceptual de imágenes. |
| PyTorch (Colab, GPU) | Búsqueda de vecinos en segundos sobre 138 mil juegos. |
| Gradio | App web y enlace público temporal. |
| Oracle Cloud (Always Free) · Caddy | Servidor siempre encendido con HTTPS automático. |
| Hugging Face Hub | Dataset privado con el paquete del modelo. |
| pytest · GitHub Actions | Tests automáticos en cada push. |

Por qué se eligió cada pieza, y lo que se descartó a propósito, en la [Guía técnica §4](docs/GUIA_TECNICA.md#4-el-stack-y-por-qué-se-eligió-cada-pieza).

---

## 🔒 Datos y ética

* **Fuente:** dataset público de Steam en Kaggle (FronkonGames) e imágenes del CDN público de la tienda, usados solo para análisis académico.
* **No se publican** datos de Steam, imágenes ni etiquetas del equipo en este repositorio: viven en Google Drive y en un dataset privado de Hugging Face. Las capturas de este README no incluyen arte de los juegos.
* **No se usa SteamDB** como fuente automática: sus términos prohíben el scraping y entrenar IA con sus datos.
* **El resultado es una prioridad de revisión, no un veredicto.** La app lo dice en cada búsqueda: una probabilidad alta significa "vale la pena revisarlo", no "es una copia".

---

## 🚧 Limitaciones

* Las etiquetas débiles salen del texto: miden "texto casi idéntico", no "copia". Por eso hace falta el Modelo B con etiquetas humanas.
* El TF-IDF está pensado para inglés. Las descripciones en otros idiomas se filtran de las etiquetas débiles.
* Pocas imágenes por juego: header y 3 capturas para los ~9 mil juegos de entrenamiento, y solo el header para el resto (con una sola imagen, `img_cos` sale algo más bajo). No se analizan videos ni jugabilidad.
* La señal más fuerte del Modelo A es la coincidencia de tags, que también separa géneros: el modelo puede sobrevalorar pares del mismo género.
* Solo Steam.

Lista completa en la [Guía técnica §11](docs/GUIA_TECNICA.md#11-limitaciones-conocidas).

---

## 🗺️ Estado del proyecto y próximos pasos

| Hito | Fecha | Estado |
|---|---|---|
| Catálogo de Steam limpio (137.976 juegos) e imágenes de 137.966 | nov 2026 | ✅ Listo |
| Señales por par, Modelo A y evaluación con validación por familias | nov 2026 | ✅ Listo |
| App con el modelo entrenado, explicación y registro de casos | nov 2026 | ✅ Listo |
| Demo pública (Colab + enlace de Gradio) | nov 2026 | ✅ Lista |
| App publicada 24/7 con HTTPS y contraseña (Oracle Cloud) | nov 2026 | ✅ Lista |
| Lote de 100 pares para etiquetar | nov 2026 | ✅ Generado · 🔄 etiquetado en curso |
| **Modelo base funcionando** | 24 nov | ✅ Modelo A |
| Modelo B y evaluación con etiquetas humanas | 27 nov | ⏳ Espera las etiquetas |
| **Demo y README** | 30 nov | 🔄 En revisión |
| **Presentación final (7 min)** | 3 dic | 🔄 En preparación |

**Trabajo futuro:** comparar videos y más capturas por juego; sumar otras tiendas (itch.io, Roblox); y, solo con acceso legítimo al código fuente, comparar código mediante grafos de flujo de control.

---

## 🧪 Antecedente: primer experimento con datos simulados

[`FairPlay_AI_DBSCAN.ipynb`](FairPlay_AI_DBSCAN.ipynb) probó la hipótesis central sobre un catálogo simulado de 28 juegos (clones de *Escape the Walls*, *Farm Tycoon* y *Racing Legends*, más señuelos del mismo género), agrupando con DBSCAN:

| Enfoque | F1 | Precisión |
|---|---|---|
| Solo texto (TF-IDF) | 0,636 | 47,9 % |
| Texto + imagen simulada | 0,912 | 100 % |

Mostró que **combinar señales ayuda si la imagen es informativa**, pero los "embeddings de imagen" eran simulados y los clones compartían un centro visual por construcción. Por eso el equipo pasó a datos reales de Steam con el notebook principal.

---

## ❓ Preguntas frecuentes

**¿FairPlay AI detecta plagio?**
No. Calcula qué pares conviene que una persona revise primero. Decidir si hay copia requiere criterio humano y, a veces, legal.

**¿Por qué una regresión logística y no un modelo más potente?**
Porque se puede explicar: el aporte de cada señal es una multiplicación, y la app lo muestra. El *gradient boosting* rinde algo mejor (PR-AUC 0,415 frente a 0,363), pero no permite justificar cada resultado con esa claridad. En un sistema que apoya decisiones delicadas, se priorizó entender por qué.

**¿Por qué el Modelo A no mira el texto?**
Sus etiquetas automáticas se crearon con una regla sobre el texto. Si el modelo viera el texto, solo aprendería esa regla. Al ocultárselo, tiene que aprender de imágenes, títulos y tags.

**¿Por qué hacen falta etiquetas humanas?**
Las automáticas miden "descripción casi idéntica", que no es lo mismo que "merece revisión". Solo personas pueden dar esa respuesta, y con ella se entrena y se evalúa el Modelo B.

**¿Por qué un 37 % aparece primero, si es una probabilidad baja?**
La lista ordena del más al menos recomendable. Si el primero tiene una probabilidad baja, el mensaje es que ese juego no tiene candidatos preocupantes.

**¿Qué pasa con un juego que salió después de armar el catálogo?**
No aparece en la búsqueda por nombre. Se puede pegar su descripción en la pestaña *Texto nuevo*. Revisar los lanzamientos nuevos de forma automática queda como trabajo futuro.

**¿Los datos de Steam están en este repositorio?**
No. El código es público; el catálogo, las imágenes y las etiquetas quedan en almacenamiento privado del equipo.

---

## 📖 Glosario

| Término | En simple |
|---|---|
| **Par** | Dos juegos que se comparan entre sí. |
| **Señal** | Una medida de parecido entre los dos juegos de un par, casi siempre entre 0 y 1. |
| **TF-IDF** | Forma de comparar textos por sus palabras, que da más peso a las poco comunes. |
| **Embedding** | Lista de números que resume el significado de un texto o una imagen; dos parecidos quedan cerca. |
| **CLIP** | Modelo de IA que convierte imágenes en embeddings. |
| **Hash perceptual** | "Huella" de una imagen que casi no cambia si se redimensiona o se recomprime. |
| **Jaccard** | Elementos en común ÷ elementos totales. |
| **Regresión logística** | Modelo que suma las señales con un peso cada una y entrega una probabilidad. |
| **Etiqueta débil** | Etiqueta creada por una regla automática: abundante, pero aproximada. |
| **Etiqueta humana** | Decisión de una persona del equipo sobre un par. |
| **PR-AUC** | Nota entre 0 y 1 que mide si los pares que valen la pena quedan arriba en la lista; sirve cuando hay pocos positivos. |
| **Precisión@20** | De los 20 primeros pares de la lista, qué fracción valía la pena. |
| **Validación cruzada por familias** | Evaluar con juegos que el modelo no vio al entrenar, ni ellos ni sus parecidos. |

Glosario completo en la [Guía técnica §12](docs/GUIA_TECNICA.md#12-glosario).

---

## 📚 Documentación

| Documento | Para quién |
|---|---|
| [Guía técnica](docs/GUIA_TECNICA.md) | Quien quiera entender o modificar el sistema: flujo de datos, cada señal, el modelo, las métricas, cómo correr todo y cómo trabajar con Git. |
| [Guía de etiquetado](docs/GUIA_ETIQUETADO.md) | Quien etiquete pares para el Modelo B. |
| [README de la app](Primera%20fase%20práctica/README.md) | Quien instale o publique la app. |
| [Guía del despliegue](despliegue/oci/README.md) | Quien mantenga el servidor o reentrene el modelo. |
| [Guía para probadores](Primera%20fase%20práctica/LEEME_PROBADORES.md) | Quien pruebe la app y reporte problemas. |
