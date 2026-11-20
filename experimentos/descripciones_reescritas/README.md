# Descripciones reescritas

**Responsable:** Sergio · **Estado:** 🔄 En curso (falta la revisión a mano)

## Pregunta

¿Qué son los pares de estudios distintos cuyas descripciones dicen lo mismo con otras palabras? ¿Traducciones, reescrituras de una misma plantilla, el mismo autor con otro nombre?

## Por qué podría servir

El proyecto tiene dos señales de texto: **mismas palabras** (TF-IDF) y **mismo significado** (embeddings). Si alguien copia una descripción y la reescribe, la primera baja y la segunda no. Estos pares son la prueba de por qué hacen falta las dos.

## Datos

Los candidatos de [`casi_identicos/`](../casi_identicos/) que cumplen:

- estudios claramente distintos (`mismo_dev = 0` y nombres poco parecidos);
- mismo significado: `emb_cos` ≥ 0,9;
- pocas palabras en común: `tfidf_cos` < 0,5.

## Cómo correrlo

```bash
python experimentos/descripciones_reescritas/revisar.py
```

Deja `salidas/pares_para_revisar.xlsx`, con las dos descripciones completas, el idioma probable de cada una y una columna `que_es` para anotar a mano, y `salidas/resumen.json`. No se sube: tiene textos de Steam.

## Resultados

| | |
|---|---|
| Pares encontrados | 47 |
| En el mismo idioma | 47 (38 en inglés y 9 en chino) |
| En idiomas distintos (traducciones) | 0 |
| Probabilidad mediana del Modelo A | 0,39 |

**No hay traducciones, y en este catálogo no puede haberlas:** el 98,7 % de las descripciones está en inglés (muestra de 3.000 juegos). Steam entrega la descripción en inglés cuando existe. Para buscar traducciones habría que bajar las descripciones en otros idiomas.

**Lo que se ve en una primera mirada** a 14 de los pares en inglés (sin revisión completa):

| Patrón | Pares | Qué sugiere |
|---|---|---|
| Una familia de 5 juegos de terror de 4 estudios distintos, con avisos y descripciones casi iguales frase a frase | 7 | Plantilla compartida o un mismo grupo detrás. El candidato más interesante. |
| Descripción parafraseada: misma estructura con sinónimos | 3 | Reescritura a partir de otra descripción. |
| Remaster publicado por otro estudio | 1 | Caso legítimo: misma obra. |
| Dos juegos de una misma saga, con el estudio escrito distinto (uno suma al estudio que hizo el port) | 1 | Caso legítimo; `mismo_dev` no lo ve. |
| Mismo autor con dos nombres de estudio | 1 | Caso legítimo; `mismo_dev` no lo ve. |
| Línea de juegos de un mismo editor | 1 | Caso legítimo: misma serie. |

**Un detalle técnico:** en algunos pares las primeras frases son idénticas, pero `tfidf_cos` queda bajo 0,5 porque el resto de la descripción cambia. La señal de palabras compara la descripción completa, así que una copia parcial se diluye.

## Qué falta

- [ ] Revisar a mano los 47 pares y llenar `que_es` (traducción, reescritura, plantilla, mismo autor, misma obra, casualidad).
- [ ] Etiquetar en la app los que correspondan, con el criterio de la [Guía de etiquetado](../../docs/GUIA_ETIQUETADO.md).
- [ ] Con las etiquetas, ver si `emb_cos` alto con `tfidf_cos` bajo separa «Posible copia» de «Similar». Si es así, es un argumento para que el Modelo B use la señal de significado.

## Límites

- El idioma se adivina con una regla simple (alfabeto y palabras frecuentes), no con un detector entrenado.
- Solo mira los pares que ya eran candidatos por texto o por imagen en `casi_identicos/`.
- Los pares son candidatos sin revisar: no se nombran en el repositorio.
