# Etiquetas de objetos en las portadas (RAM++)

**Responsable:** [nombre] · **Estado:** 🔄 Prototipo (comparador en Gradio que recibe dos portadas)

## Pregunta

¿Las etiquetas de objetos de RAM++ («espada», «dragón», «armadura») ayudan a quien revisa a entender por qué dos portadas se parecen?

## Por qué podría servir

CLIP entrega un número de parecido entre imágenes, difícil de explicar. RAM++ entrega palabras: qué objetos tiene cada portada, cuáles comparten y cuáles son exclusivos de cada una.

## Lo que mostró el prototipo

| Par de portadas | Etiquetas en común |
|---|---|
| Skyrim · Zelda: Ocarina of Time | cinema, poster, sword |
| RuneQuest · Zelda: Ocarina of Time | poster, sword |

- **Los objetos en común describen el género.** Tres juegos sin relación comparten «espada». El proyecto dice que parecerse por género **no** es copia, así que estas etiquetas sirven para describir, no para decidir.
- **Algunas etiquetas son del formato, no del contenido:** «poster», «movie poster», «cinema» y «video game». Hay que filtrarlas.
- **Se le escapan objetos:** en la portada de Zelda no detectó el escudo, quizás porque lo tapa la «Z» del logo.

## Preguntas abiertas

- [ ] **Uso propuesto:** solo como texto de apoyo en «Comparar dos juegos» («objetos en ambas portadas»), no como señal del modelo.
- [ ] **Lista de etiquetas a ignorar** (formato de la imagen y palabras genéricas).
- [ ] **Costo:** el servidor no tiene GPU, así que habría que calcular las etiquetas en Colab para todo el catálogo, como se hizo con CLIP, y sumarlas al paquete. ¿Cuánto tarda y cuánto pesa?
- [ ] **Línea base:** comparar contra los géneros y tags de Steam. Si dicen lo mismo, RAM++ no agrega información.
- [ ] **Evaluación:** con pares etiquetados por el equipo, ¿la cantidad de objetos en común separa «Posible copia» de «Similar»?

## Por qué no entra todavía al modelo

El Modelo B se entrena con pocas etiquetas humanas (unas 20–40). Sumarle otra variable con tan pocos datos es arriesgar sobreajuste, y obliga a reentrenar y volver a evaluar.

## Cómo correrlo

[Completar: dependencias, pesos del modelo, si necesita GPU y el comando.]
