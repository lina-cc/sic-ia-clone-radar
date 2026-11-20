# Candidatos también por imagen

**Responsable:** Sergio · **Estado:** ✅ Aplicado en la app (noviembre de 2026)

## Pregunta

¿Cuántos pares con la misma imagen no llegan a mostrarse en «Buscar un juego», porque los candidatos salen solo del texto?

## Por qué importa

Antes de calcular la probabilidad, el sistema elige qué juegos comparar. Esa elección usa **solo el texto**: los 10 más parecidos por palabras y los 10 más parecidos por significado (`vecinos()` en `Primera fase práctica/modelo.py`, y lo mismo en el notebook). Después muestra los 10 de mayor probabilidad.

Si un clon reescribe la descripción pero reutiliza las capturas, puede no estar entre esos candidatos, aunque la señal de imagen lo detectaría.

## Datos

Los 844 pares con **imagen casi idéntica** (hash perceptual ≥ 0,9) que encontró [`casi_identicos/`](../casi_identicos/). Cada par se busca desde los dos juegos: 1.688 búsquedas. Además, 300 juegos al azar para ver cuánto cambia una búsqueda cualquiera.

## Cómo correrlo

```bash
python experimentos/vecinos_imagen/medir.py      # unos 7 minutos sin GPU
```

Necesita `../casi_identicos/salidas/candidatos.parquet`. Deja `salidas/resultados.json`.

## Las tres formas de elegir candidatos

| Variante | Candidatos |
|---|---|
| **Actual** (línea base) | 10 por palabras + 10 por significado |
| **Con imagen** | Lo actual + los 10 juegos con la imagen más parecida (CLIP) |
| **Con imagen casi idéntica** | Lo actual + los juegos con una imagen casi idéntica (coseno CLIP ≥ 0,96, máximo 10) |

## Resultados

**Porcentaje de búsquedas en que el otro juego aparece entre los 10 que se muestran:**

| Pares con imagen casi idéntica | Búsquedas | Actual | Con imagen | Con imagen casi idéntica |
|---|---|---|---|---|
| Todos | 1.688 | 87 % | 90 % | 91 % |
| Con texto distinto (TF-IDF < 0,5) | 168 | **71 %** | 100 % | **100 %** |
| De estudios distintos | 198 | **82 %** | 100 % | **100 %** |

**Cuánto cambia una búsqueda cualquiera** (300 juegos al azar):

| | Con imagen | Con imagen casi idéntica |
|---|---|---|
| Juegos nuevos entre los 10 que se muestran (promedio) | 5,7 | **0** |
| Búsquedas que no cambian | 1 % | **100 %** |
| Tiempo extra por búsqueda | 0,02 s | 0,02 s |

## Qué aprendimos

- **Hoy la app no muestra 3 de cada 10 pares con la misma imagen y texto distinto**, ni casi 2 de cada 10 de estudios distintos. Son justo los clones que reescriben la descripción.
- **Sumar todos los vecinos por imagen cambia demasiado:** reemplaza casi 6 de los 10 resultados de cualquier búsqueda, con juegos de estilo parecido. Sin etiquetas no se sabe si eso es mejor o peor, y cambiaría lo que el equipo ya conoce de la app.
- **Sumar solo las imágenes casi idénticas recupera esos pares sin tocar el resto:** en los 300 juegos al azar la lista quedó igual. Las imágenes casi idénticas son raras, así que solo aparecen cuando importan.
- **Es barato:** 0,02 s más por búsqueda, con los vectores que ya tiene el paquete del modelo.

**Aplicado en la app:** `vecinos()` en `Primera fase práctica/modelo.py` usa la variante «con imagen casi idéntica» (`vecinos_imagen()`, umbral `UMBRAL_IMAGEN_IDENTICA = 0.96`). No obliga a reentrenar, porque el modelo y las señales no cambian; solo cambia qué pares se le pasan. Con el paquete real: los 20 primeros pares con imagen casi idéntica y texto distinto aparecen entre los 10 que se muestran, una búsqueda tarda 0,3 s y el índice de imágenes ocupa 0,34 GB de RAM. Lo cubren dos tests en `tests/test_modelo.py`.

## Límites

- **El 100 % es optimista por construcción:** los pares de prueba los encontró `casi_identicos/` usando vecinos por imagen con el mismo umbral, así que la variante por imagen los encuentra seguro. La cifra que vale es la de la línea base: **71 % y 82 %**.
- Solo mide si el par **aparece**, no si es una copia. Para eso hacen falta etiquetas humanas.
- En el notebook también se arman los pares de entrenamiento solo con texto. Cambiarlo ahí obliga a reentrenar y volver a evaluar: va después de la presentación.
