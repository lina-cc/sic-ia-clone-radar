# Comparar el código de proyectos Godot (CodeBERT)

**Responsable:** [nombre] · **Estado:** 🔄 En curso

## Pregunta

¿Comparar el código con CodeBERT distingue un juego copiado de uno que solo comparte el tema?

## Por qué podría servir

El modelo actual ve el material reutilizado (texto e imágenes) pero no la **mecánica**. El código sí la refleja. Ejemplo con tres juegos ficticios:

| Juego | Qué es | Código frente a *Mahjong with golf* |
|---|---|---|
| *Mahjong with golf* | Mahjong con temática de golf | — |
| *Golf with mahjong* | Golf con temática de mahjong: otro género, otra jugabilidad | Distinto |
| *Mahjong 2* | El mismo juego que *Mahjong with golf* con otros gráficos y música | Igual |

Las imágenes y el texto confundirían a *Golf with mahjong* con el original; el código no.

## De dónde sale el código (importante)

Los juegos de Steam **no publican su código**, y sacarlo del archivo exportado de un juego ajeno es ingeniería inversa de un producto de otra persona. La [Guía técnica](../../docs/GUIA_TECNICA.md) dice que el código solo se compara **con acceso legítimo**. Por eso este experimento usa:

- proyectos Godot hechos por el equipo para la prueba;
- proyectos Godot de código abierto con licencia que lo permita (anotar la licencia de cada uno).

**No se aplica al catálogo de Steam.** Es un prototipo del método.

## Preguntas abiertas

- [ ] **La mini app que extrae el código:** ¿lee los `.gd` de la carpeta del proyecto, o abre archivos exportados? Solo lo primero cabe en las reglas de arriba.
- [ ] **CodeBERT no se entrenó con GDScript** (sí con Python, Java, JavaScript, PHP, Ruby y Go). GDScript se parece a Python: hay que comprobar que funciona.
- [ ] **Escala de la similitud:** los embeddings sin ajustar suelen dar similitudes altas a casi cualquier par de código. Medir también pares al azar para saber qué valor es «alto».
- [ ] **Línea base:** comparar contra un método simple (diff de texto o huellas de tokens tipo MOSS). En *Mahjong 2* el código es idéntico y ambos lo detectan; CodeBERT tiene que ganar cuando se renombran variables o se reordenan funciones.
- [ ] **Pares de prueba armados por otra persona**, para que la evaluación no sea circular.

## Resultados

| Método | Pares de prueba | Separa copias de temas parecidos |
|---|---|---|
| Línea base (diff o MOSS) | [__] | [__] |
| CodeBERT | [__] | [__] |

## Cómo correrlo

[Completar: dependencias, de dónde salen los proyectos de prueba y el comando.]
