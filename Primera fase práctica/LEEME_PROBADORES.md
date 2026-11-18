# Probar la app de FairPlay AI

Guía corta para quien va a **probar la app o etiquetar pares** por primera vez. No hay que instalar nada: la app ya está publicada.

> **Similitud no es plagio.** La app ordena pares de juegos para que una persona los revise. No acusa a nadie.

## Qué necesitas

- Un navegador (computador o celular).
- El **enlace** de la app y el **usuario y la contraseña** del equipo. Pídelos por el canal privado del grupo; no se publican en el repositorio.

## Primeros pasos (1 minuto)

1. Abre el enlace e ingresa con el usuario y la contraseña del equipo.
2. Escribe **tu nombre** en el cuadro de arriba. El navegador lo recuerda, así que solo se hace una vez.
3. Quédate en la pestaña **Etiquetar pares**: el primer par aparece solo.

Sin nombre la app no guarda etiquetas: así sabemos quién revisó cada par.

## Qué probar

| Pestaña | Qué hace | Qué probar |
|---|---|---|
| **Etiquetar pares** | Muestra dos juegos lado a lado y pide una decisión. | Etiqueta unos 30 pares. Es lo que más ayuda al proyecto. |
| **Buscar un juego** | Dado un juego, lista los candidatos más parecidos según el modelo. | Escribe un juego que conozcas bien y mira si los candidatos tienen sentido. |
| **Comparar dos juegos** | Compara un par concreto y explica qué señales pesaron. | Prueba dos juegos que creas muy parecidos y dos que no. |
| **Línea base (solo palabras)** | La versión simple, que solo compara descripciones. | Compara sus resultados con los del modelo. |
| **Ayuda** | Resumen de cómo funciona todo. | Léela si te pierdes. |

Si un título no aparece, la app sugiere nombres parecidos. Solo están los juegos del catálogo con descripción en inglés.

## Cómo etiquetar un par

1. Mira las imágenes y las descripciones de los dos juegos. Si dudas, abre *Abrir en Steam* para ver capturas y videos.
2. Pulsa uno de los tres botones:

   | Botón | Cuándo |
   |---|---|
   | **Posible copia** | Un especialista debería mirarlo: mismas capturas o arte, descripción copiada o traducida, el mismo juego con otro nombre. |
   | **Similar** | Se parecen, pero hay una explicación normal: misma saga, mismo estudio, mismo género. |
   | **No similar** | No se parecen de verdad. |

3. El par se guarda y aparece el siguiente.

- **Saltar este par:** si no puedes decidir. No se guarda nada.
- **Deshacer el último:** si te equivocaste. Borra tu última etiqueta y vuelve a mostrar ese par.

La app no muestra la probabilidad del modelo antes de que decidas, para no influir en tu respuesta. La barra de arriba indica cuántos pares llevas y cuántos le faltan al equipo.

Los criterios completos, con ejemplos, están en la [Guía de etiquetado](../docs/GUIA_ETIQUETADO.md).

## Si algo falla

| Problema | Qué hacer |
|---|---|
| El navegador pide usuario y contraseña una y otra vez | Revisa mayúsculas y espacios. Si sigue, pide la contraseña de nuevo por el canal del equipo. |
| «Escribe tu nombre» al pulsar un botón | Falta el nombre en el cuadro de arriba. |
| La página no carga | Espera un minuto y recarga: la app se reinicia cuando se actualiza. Si sigue caída, avisa al equipo. |
| Un resultado se ve mal o raro | Anota los dos juegos y lo que esperabas, y mándalo al equipo. Los resultados equivocados también sirven. |

## ¿Quieres correrla en tu computador?

No hace falta para probar. Si igual quieres hacerlo, los pasos están en el [README de esta carpeta](README.md#requisitos).
