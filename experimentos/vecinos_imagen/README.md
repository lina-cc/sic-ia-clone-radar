# Candidatos también por imagen

**Responsable:** por definir · **Estado:** 💡 Idea

## Pregunta

¿Cuántos pares parecidos solo por imagen nunca llegan a ser candidatos, porque hoy los candidatos salen del texto?

## Por qué importa

Antes de calcular la probabilidad, el sistema elige qué juegos comparar. Esa elección usa **solo el texto**: los juegos más parecidos por palabras y por significado (`vecinos()` en `Primera fase práctica/modelo.py`, y lo mismo en el notebook).

Entonces un clon que reescribe la descripción pero reutiliza las capturas **nunca aparece como candidato**, aunque la señal de imagen lo detectaría. Es justo el caso que el README pone de ejemplo de por qué hay tantas señales.

La búsqueda de [`casi_identicos/`](../casi_identicos/) encontró 18 pares de estudios distintos con la **misma imagen y texto distinto**.

## Propuesta

1. Medir: para los pares con imagen casi idéntica, ¿cuántos aparecen entre los candidatos por texto de la app?
2. Sumar a los candidatos los juegos más parecidos por imagen (CLIP). Los vectores ya están en el paquete del modelo, y la búsqueda para todo el catálogo tardó unos 6 minutos sin GPU.
3. En la app: cambio acotado en `vecinos()`, sin reentrenar.
4. En el notebook: cambia los pares de entrenamiento, así que obliga a reentrenar y volver a evaluar. Va después de la presentación.

## Línea base

Los candidatos actuales (solo texto). Métrica: cuántos pares con imagen casi idéntica recupera cada versión.
