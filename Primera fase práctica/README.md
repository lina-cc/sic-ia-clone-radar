# App de similitud entre videojuegos (línea base TF-IDF)

Explorador en Gradio para probar casos con el grupo. Compara descripciones con
TF-IDF y similitud coseno, y muestra las palabras que explican cada parecido.

## Archivos

- `similitud.py`: la lógica (carga de datos, TF-IDF, búsqueda, comparación). No depende de Gradio.
- `app.py`: la interfaz, con tres pestañas: buscar similares, comparar dos juegos y texto nuevo.

## Requisitos

Python 3.11 o superior, con `pandas`, `pyarrow`, `scikit-learn`, `joblib` y `gradio`:

```bash
pip install gradio
```

## Uso

Pon el parquet del notebook 01 en `data/juegos_texto_en.parquet`. Debe tener, como mínimo,
las columnas `Name` y `texto`. Si existen, también usa `Genres`, `Release date`, `AppID` y `n_resenas`.

```bash
python app.py                        # abre en http://127.0.0.1:7860
python app.py --share                # además crea un enlace público temporal
python app.py --datos otra/ruta.parquet
```

La primera ejecución ajusta el TF-IDF y guarda un caché junto al parquet
(`juegos_texto_en.tfidf.joblib`). Las siguientes arrancan casi al instante.
Si cambias el parquet, el caché se regenera solo.

## Casos guardados

Cada caso marcado en la app se agrega a `casos/casos_guardados.csv`, con fecha, anotador,
consulta, juego comparado, puntaje, etiqueta (Similar, No similar o Posible copia) y comentario.
Se abre bien en Excel y en pandas (`encoding="utf-8-sig"`).

## Importante

- Los datos de Steam no se deben publicar: no subas `data/` ni `casos/` a un repositorio abierto.
- Con `--share` cualquiera que tenga el enlace puede usar la app mientras esté corriendo.
- La similitud no es plagio: la app solo sugiere candidatos para revisión humana.
