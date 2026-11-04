# App de similitud entre videojuegos (línea base TF-IDF)

Explorador en Gradio para probar casos con el grupo. Compara descripciones con
TF-IDF y similitud coseno, y muestra las palabras que explican cada parecido.

Es la **línea base** del proyecto: el notebook principal (`FairPlay_AI_Clasificador_Pares.ipynb`)
compara su modelo contra lo que hace esta app. Los casos que se etiquetan aquí son las
**etiquetas humanas** con que se entrena y evalúa ese modelo.

## Archivos

- `similitud.py`: la lógica (carga de datos, TF-IDF, búsqueda, comparación). No depende de Gradio.
- `app.py`: la interfaz, con tres pestañas (buscar similares, comparar dos juegos y texto nuevo) y el registro de casos.
- `requirements.txt`: dependencias con versiones fijas, probadas con Python 3.12.
- `environment.yml`: el mismo entorno para Conda.

## Requisitos

Python 3.12 (también funciona con 3.11):

```bash
pip install -r requirements.txt
```

## Uso

Pon el parquet en `data/juegos_texto_en.parquet` (dentro de esta carpeta). Debe tener, como
mínimo, las columnas `name` (título) y `text` (descripción ya limpia). Si existen, también usa
`genres`, `release date`, `appid` y `n_resenas`. Los nombres van en minúscula.

```bash
python app.py                        # abre en http://127.0.0.1:7860
python app.py --share                # además crea un enlace público temporal
python app.py --datos otra/ruta.parquet
```

La primera ejecución ajusta el TF-IDF y guarda una caché junto al parquet
(`juegos_texto_en.tfidf.joblib`). Las siguientes arrancan casi al instante.
Si cambias el parquet, la caché se regenera sola.

### Variables de entorno (opcionales)

Permiten configurar la app sin cambiar el código. Son las que usa Hugging Face Spaces.

| Variable | Para qué |
|---|---|
| `FAIRPLAY_DATOS` | Ruta del parquet (reemplaza a `--datos`). |
| `FAIRPLAY_HF_DATASET` | Si el parquet no está en disco, se descarga de este dataset de Hugging Face (por ejemplo `usuario/fairplay-datos`). Puede ser privado. |
| `HF_TOKEN` | Token de lectura de Hugging Face, necesario si el dataset es privado. |
| `GRADIO_SERVER_NAME` | Dirección donde escucha la app. Por defecto `127.0.0.1` (solo tu computador). Spaces usa `0.0.0.0`. |
| `GRADIO_SERVER_PORT` | Puerto. Por defecto `7860`. |

## Publicar en Hugging Face Spaces

Resumen (los pasos completos están en la [Guía técnica](../docs/GUIA_TECNICA.md#8-publicar-la-app-en-hugging-face-spaces)):

1. Subir `juegos_texto_en.parquet` a un **dataset privado** de Hugging Face.
2. Crear un **Space** con SDK Gradio y subir `app.py`, `similitud.py` y `requirements.txt`.
3. En *Settings → Variables and secrets* del Space: la variable `FAIRPLAY_HF_DATASET` con el nombre del dataset y el secreto `HF_TOKEN`.

En Spaces gratuitos el disco se borra al reiniciar: los casos guardados ahí se pierden.

## Casos guardados

Cada caso marcado en la app se agrega a `casos/casos_guardados.csv`, con fecha, anotador,
tipo, consulta, juego comparado, puntaje, etiqueta (Similar, No similar o Posible copia) y comentario.
Se abre bien en Excel y en pandas (`encoding="utf-8-sig"`).

Para usarlos en el notebook principal, copia ese archivo a `data/casos_guardados.csv` en la carpeta
del notebook (o en `MyDrive/fairplay/data/` si usas Google Drive). Ahí se traducen así:
*Posible copia* → 1, *Similar* y *No similar* → 0.

## Tests

Desde la raíz del repositorio:

```bash
pip install -r requirements-dev.txt
pytest
```

## Importante

- Los datos de Steam no se deben publicar: no subas `data/` ni `casos/` a un repositorio abierto.
- Con `--share` cualquiera que tenga el enlace puede usar la app mientras esté corriendo.
- La similitud no es plagio: la app solo sugiere candidatos para revisión humana.
