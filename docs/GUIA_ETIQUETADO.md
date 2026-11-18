# Guía de etiquetado de pares

El **Modelo B** y la evaluación que vale para el informe (sección 7 del notebook) necesitan pares de juegos revisados por personas. Esta guía explica cómo etiquetarlos.

## En un minuto

* **La pregunta:** *¿un especialista debería mirar este par?* No es "¿es plagio?".
* **Meta:** unos 30 pares por persona, y que el equipo junte al menos **10 «Posible copia»** y **10 «Similar» o «No similar»**. Con eso se activa el Modelo B.
* **Dónde:** lo más rápido es la app, pestaña **Etiquetar pares** ([sección 6](#6-otra-forma-la-cola-de-revisión-de-la-app)). El lote en Excel (secciones 1 a 5) es la base de la evaluación del informe.
* **Decide antes de mirar los puntajes del modelo**, y con tu propio criterio: nadie etiqueta a nombre de otra persona.

| En la app | En el Excel | Para el modelo |
|---|---|---|
| Posible copia | Coincidencia relevante | Positivo (1) |
| Similar | Caso legítimo | Negativo (0) |
| No similar | Descartado | Negativo (0) |
| Saltar este par | No concluyente | No se usa |

## 1. Dónde está el lote

Cada corrida del notebook deja en Google Drive:

```
MyDrive/fairplay/salidas/lote_para_etiquetar.xlsx
```

Tiene tres hojas:

| Hoja | Para qué |
|---|---|
| **Pares** | La que se llena. Una fila por par de juegos, con enlaces a Steam. |
| **Instrucciones** | Resumen de esta guía. |
| **Señales** | Puntajes del modelo. **No la miren antes de etiquetar**: los puntajes sesgan la decisión. |

## 2. Cómo trabajar en equipo

1. Hagan una copia del archivo en `MyDrive/fairplay/data/` con el nombre **`lote_etiquetado.xlsx`**.
2. Ábranlo en Google Sheets (doble clic en Drive) para trabajar todos a la vez.
3. Repártanse las filas: por ejemplo, 25 por persona (L-001 a L-025, L-026 a L-050, etc.).
4. Al terminar, si lo editaron en Google Sheets: *Archivo → Descargar → Microsoft Excel (.xlsx)* y súbanlo de nuevo a `MyDrive/fairplay/data/lote_etiquetado.xlsx`, reemplazando el anterior. El notebook lee el `.xlsx`, no la hoja de Google.

No cambien los nombres de las columnas ni borren `appid_a` y `appid_b`: el notebook usa esas columnas para saber qué par es.

## 3. Qué hacer en cada fila

1. Abran los dos enlaces (`url_a` y `url_b`).
2. Comparen **descripción, imágenes y capturas, mecánicas, desarrollador y fechas**.
3. Elijan `Etiqueta_humana` en la lista desplegable.
4. Escriban su nombre en `Responsable` y, si sirve, el motivo en `Observaciones` (por ejemplo, "mismas capturas con otro logo").

Calculen unos 2 minutos por par. Si un par toma más de 5 minutos, márquenlo *No concluyente* y sigan.

## 4. Qué etiqueta poner

| Etiqueta | Cuándo | Ejemplos |
|---|---|---|
| **Coincidencia relevante** | El par **merece revisión de un especialista**: parece copia, reskin o reutilización de material de otro. | Mismas capturas o arte con otro nombre; descripción copiada o traducida; mismo juego publicado por otro desarrollador. |
| **Caso legítimo** | Se parecen, pero **hay una explicación normal**. | Misma saga o franquicia; remaster, edición especial o DLC; mismo desarrollador; mismo género con convenciones comunes (todos los *survivors-like* se parecen). |
| **Descartado** | **No se parecen** de verdad; el sistema los juntó por error. | Comparten palabras genéricas ("survive", "upgrade") pero son juegos distintos. |
| **No concluyente** | **No se puede decidir** con lo que hay. No se usa para entrenar. | Página sin imágenes, juego retirado de Steam, información en un idioma que nadie del equipo lee. |

**Regla para dudas:** la pregunta no es "¿es plagio?" (eso no lo decide este proyecto), sino **"¿un especialista debería mirar este par?"**. Si la respuesta es sí y no hay una explicación legítima evidente, es *Coincidencia relevante*.

## 5. Por qué el lote viene mezclado

El lote junta cuatro tipos de pares (los detalles están en la sección 10 del notebook):

* **modelo:** los que el Modelo A considera más probables.
* **dudoso:** los que el modelo no sabe clasificar.
* **texto:** los que encontraría la línea base TF-IDF.
* **azar:** pares cualquiera.

Así la evaluación compara los métodos en igualdad de condiciones. Si solo etiquetáramos lo que encuentra el modelo, el modelo saldría mejor de lo que es. Por eso las filas van desordenadas y sin puntajes.

## 6. Otra forma: la cola de revisión de la app

La pestaña **Etiquetar pares** de la app muestra los pares uno a uno, con las imágenes y las descripciones lado a lado:

1. Escribe tu nombre arriba (el navegador lo recuerda). El primer par aparece solo.
2. Compara los dos juegos (el enlace *Abrir en Steam* muestra capturas y videos).
3. Pulsa **Posible copia**, **Similar** o **No similar**. El par se guarda y aparece el siguiente.
4. Si no se puede decidir, pulsa **Saltar este par**: no se guarda nada.
5. Si te equivocaste, **Deshacer el último** borra tu última etiqueta y vuelve a mostrar ese par.

Las equivalencias con el Excel están en la tabla del inicio. Cómo entrar a la app: [LEEME_PROBADORES.md](../Primera%20fase%20pr%C3%A1ctica/LEEME_PROBADORES.md).

La cola no muestra la probabilidad del modelo antes de decidir, por la misma razón que no se mira la hoja «Señales». Mezcla tres tipos de pares: el que el modelo pone primero, el más parecido por palabras y uno que el modelo considera poco probable. Arriba se ve cuántos pares llevas y cuántos le faltan al equipo.

El lote en Excel sigue siendo la base de la evaluación del informe; la cola sirve para sumar etiquetas rápido.

## 7. Dónde encontrar más «Posible copia»: las reseñas

Revisando pares al azar aparecen pocas copias. El notebook `FairPlay_AI_Resenas.ipynb` busca juegos cuyas reseñas dicen cosas como *"a clone of X"* y deja la lista en `MyDrive/fairplay/salidas/sospechosos_resenas.xlsx`.

1. Abre la hoja **Pares**: cada fila es un juego y el juego que nombran sus reseñas, con un ejemplo. La columna `mismo_estudio` marca los pares de un mismo desarrollador (secuelas, prólogos): casi siempre son *Similar*.
2. Compara los dos juegos en Steam.
3. Etiqueta el par en la app: pestaña **Comparar dos juegos**, escribe los dos nombres, pulsa *Comparar* y elige la etiqueta.

Ojo: que una reseña diga *clone* **no** significa copia; muchas veces describe el género (*"un clon de Vampire Survivors"*). Decide con el criterio de la sección 4, no con la reseña. Algunas filas son errores de la búsqueda (otro juego con el mismo nombre, una frase común): esas no se etiquetan.

Si la lista trae una sugerencia automática, es solo una orientación para repartir el trabajo: no reemplaza mirar los dos juegos.

## 8. Después de etiquetar

Si etiquetaron en la app publicada, primero hay que llevar los casos del servidor a Drive (`bajar_casos.ps1`, ver [despliegue/oci](../despliegue/oci/README.md#ciclo-para-reentrenar-desde-windows-en-esta-carpeta)).

Vuelvan a correr el notebook completo (*Entorno de ejecución → Desconectar y borrar el entorno*, luego *Ejecutar todo*). La sección 3 imprime cuántos pares humanos leyó. Con al menos **10 pares de cada clase** (positivos = *Coincidencia relevante*; negativos = *Caso legítimo* + *Descartado*):

* se entrena el **Modelo B**,
* la sección 7 compara la línea base TF-IDF, los embeddings, el Modelo A y el Modelo B **con etiquetas humanas**. Esa tabla es la que va al informe.

Cada corrida arma un lote nuevo con pares que todavía no tienen etiqueta. Si quieren más pares, etiqueten el lote nuevo y **agreguen sus filas** a `lote_etiquetado.xlsx` (no lo reemplacen, o se pierden las etiquetas anteriores).

## 9. Datos y privacidad

`lote_etiquetado.xlsx` contiene datos de Steam y decisiones del equipo: queda en Drive y **no se sube al repositorio público**. Lo mismo vale para las reseñas descargadas (`data/resenas_cache.jsonl`) y la lista de sospechosos.
