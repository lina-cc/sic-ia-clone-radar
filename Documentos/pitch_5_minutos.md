# Pitch de 5 minutos: Sistema de detección de similitudes entre videojuegos

## [0:00 – 0:40] Gancho

Imaginen que son un desarrollador indie. Llevan meses trabajando en su juego. Un día publican unas imágenes de la jugabilidad para generar expectativa. Una semana después, hay al menos siete versiones casi idénticas en Roblox, y algunas salieron antes que su juego original.

Esto no es hipotético. Le pasó al estudio Pandorio Games con *Escape the Walls* este mismo mes de octubre.

## [0:40 – 1:30] El problema

Desarrollar un videojuego exige tiempo, conocimiento técnico y recursos. Pero las herramientas de inteligencia artificial están bajando esas barreras. Nuestra hipótesis es que la IA puede acelerar la replicación de juegos, permitiendo copiar o adaptar una idea en plazos cada vez más cortos.

Hay más casos. En julio, *Meccha Chameleon* vio aparecer clones en Steam, Roblox y Fortnite, y según Kotaku, algunas imitaciones tenían más jugadores que el original. Y en octubre, el desarrollador de *Needle In A Haystack* acusó públicamente a otro estudio de reutilizar su código: trece clases con nombres idénticos y hasta mensajes de error copiados literalmente.

## [1:30 – 2:20] El verdadero desafío: ¿dónde está el límite?

Aquí viene lo importante. No toda similitud es plagio. Compartir géneros, reglas o mecánicas generales es parte normal de la evolución de la industria. De hecho, el caso de *Meccha Chameleon* generó debate: algunos decían que compartir una mecánica no es copiar un juego.

Además, la ingeniería inversa no es mala en sí misma. Sirve para investigar, preservar, crear mods y detectar vulnerabilidades.

Entonces el problema no es "¿hay parecido?", sino otro: ¿cuándo las coincidencias, por su cantidad, su especificidad o su combinación, justifican una revisión especializada? Hoy no existe un método objetivo ni reproducible para responder eso.

## [2:20 – 3:00] Nuestra propuesta

Proponemos investigar un sistema experimental asistido por IA que identifique y documente similitudes entre videojuegos usando información pública y análisis estadístico.

El sistema analizaría metadatos y fechas de publicación, descripciones y mecánicas documentadas, recursos gráficos y, cuando exista acceso legítimo, el código fuente. Y algo clave: sabría distinguir coincidencias que vienen de usar el mismo motor, como Godot, de las que son propias de una implementación concreta.

## [3:00 – 4:00] Cómo lo hacemos: las técnicas

Usaremos métodos conocidos y modelos pre-entrenados, con transfer learning, siguiendo la guía del proyecto SIC 2026. Cada técnica cubre un tipo distinto de información:

- **TF-IDF y similitud coseno**, para comparar descripciones y textos.
- **Embeddings de texto** de Hugging Face, para detectar similitud conceptual aunque se usen palabras diferentes.
- **CNN con transfer learning**, con modelos como ResNet o MobileNet, para comparar capturas de pantalla e interfaces.
- Y como ampliación, **grafos de flujo de control**, para comparar la estructura lógica del código cuando esté disponible.

Se aplican de forma complementaria: ninguna técnica sola cuenta la historia completa.

## [4:00 – 4:40] Qué entrega el sistema, y qué no

La salida es un informe que documenta las similitudes detectadas, indica las fuentes examinadas y expone las limitaciones del análisis.

Y quiero ser muy claro: el sistema **no acusa** ni emite juicios legales. Una similitud alta no demuestra plagio. Su función es ser evidencia técnica preliminar que oriente a un especialista humano.

## [4:40 – 5:00] Cierre

Nuestro aporte es un método reproducible para estudiar patrones de replicación de software, y a la vez evaluar qué tan útil es la IA como herramienta de análisis en un problema muy concreto de la industria.

Porque si la IA hace más fácil copiar, también puede ayudarnos a documentar mejor lo que se copia. Gracias.
