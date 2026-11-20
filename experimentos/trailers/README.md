# Comparar cuadros de los trailers

**Responsable:** por definir · **Estado:** 💡 Idea

## Pregunta

¿Comparar cuadros de los trailers de Steam encuentra escenas reutilizadas que no aparecen en la portada ni en las capturas?

## Por qué podría servir

El modelo usa la portada y hasta 3 capturas por juego. Un trailer muestra muchas más escenas, y es lo más cerca que tiene Steam de mostrar la jugabilidad.

## Propuesta acotada

1. Tomar **5 a 10 pares** de la lista de [`casi_identicos/`](../casi_identicos/) y otros tantos al azar.
2. Bajar un trailer por juego y sacar un cuadro cada 2 segundos.
3. Comparar los cuadros con CLIP y con hash perceptual, igual que las capturas.
4. Ver si los pares de la lista se separan de los pares al azar mejor que con las capturas.

## Límites conocidos

- **Tamaño:** un trailer pesa decenas de MB. Para todo el catálogo serían terabytes, así que solo sirve para un grupo chico de pares.
- **No mide la mecánica:** comparar cuadros detecta escenas reutilizadas, no cómo se juega. Para eso habría que analizar el movimiento, que es otro proyecto.
- **Datos:** los videos se usan solo para el análisis y no se suben al repositorio, igual que las imágenes.

## Línea base

Las capturas que ya usa el modelo (`img_cos` y `phash_sim`).
