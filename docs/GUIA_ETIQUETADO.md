# Guía de etiquetado de pares

El **Modelo B** y la evaluación que vale para el informe (sección 7 del notebook) necesitan pares de juegos revisados por personas. Esta guía explica cómo etiquetar el lote que arma el notebook.

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

## 6. Después de etiquetar

Vuelvan a correr el notebook completo (*Entorno de ejecución → Desconectar y borrar el entorno*, luego *Ejecutar todo*). La sección 3 imprime cuántos pares humanos leyó. Con al menos **10 pares de cada clase** (positivos = *Coincidencia relevante*; negativos = *Caso legítimo* + *Descartado*):

* se entrena el **Modelo B**,
* la sección 7 compara la línea base TF-IDF, los embeddings, el Modelo A y el Modelo B **con etiquetas humanas**. Esa tabla es la que va al informe.

Cada corrida arma un lote nuevo con pares que todavía no tienen etiqueta. Si quieren más pares, etiqueten el lote nuevo y **agreguen sus filas** a `lote_etiquetado.xlsx` (no lo reemplacen, o se pierden las etiquetas anteriores).

## 7. Datos y privacidad

`lote_etiquetado.xlsx` contiene datos de Steam y decisiones del equipo: queda en Drive y **no se sube al repositorio público**.
