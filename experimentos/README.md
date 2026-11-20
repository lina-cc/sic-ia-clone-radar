# Experimentos

Ideas que **todavía no son parte del modelo ni de la app**. Cada una vive en su carpeta, con su propio README, y se puede probar sin tocar lo que ya funciona.

> **Por qué una carpeta aparte.** Cada señal nueva obliga a reentrenar, a calcularla igual en el notebook y en `senales.py`, y a explicarla en la presentación. Un experimento entra al modelo solo si demuestra que mejora algo, comparado con una línea base, con etiquetas humanas.

## Lista

| Carpeta | Pregunta | Quién | Estado |
|---|---|---|---|
| [`casi_identicos/`](casi_identicos/) | ¿Qué pares del catálogo comparten texto o imágenes casi idénticos entre estudios distintos? | Sergio | ✅ Primera corrida |
| [`ram_plus/`](ram_plus/) | ¿Las etiquetas de objetos de RAM++ ayudan a explicar por qué dos portadas se parecen? | [nombre] | 🔄 Prototipo |
| [`codigo_godot/`](codigo_godot/) | ¿CodeBERT distingue un juego copiado de uno con el mismo tema pero otra jugabilidad? | [nombre] | 🔄 En curso |
| [`trailers/`](trailers/) | ¿Comparar cuadros de los trailers encuentra escenas reutilizadas que no están en las capturas? | Por definir | 💡 Idea |
| [`vecinos_imagen/`](vecinos_imagen/) | ¿Cuántos pares parecidos solo por imagen no llegan a ser candidatos porque los candidatos salen del texto? | Por definir | 💡 Idea |

## Reglas para un experimento

1. **Una carpeta por idea**, con un `README.md` que siga la [plantilla](PLANTILLA.md).
2. **No modifica la app, el modelo ni los notebooks principales.** Si funciona, se propone después en un PR aparte.
3. **Siempre contra una línea base** simple: si algo sencillo da lo mismo, no vale la complejidad.
4. **Se evalúa con pares que no armó la misma persona que hizo el método**, para que la prueba no sea circular.
5. **Solo datos que se pueden usar** ([Guía técnica, sección 9](../docs/GUIA_TECNICA.md#9-datos-qué-se-puede-usar-y-qué-no)): nada de SteamDB, ni código sacado de juegos ajenos.
6. **Los resultados con datos de Steam van en `salidas/`**, que no se sube al repositorio. En el README van solo números agregados.
7. **No se nombran pares como «posible copia» en el repositorio.** Son candidatos sin revisar y el repositorio es público.

## Cómo se pasa al modelo

Un experimento está listo para proponerse cuando su README responde:

- qué mejora (por ejemplo, PR-AUC o precisión@20 con etiquetas humanas) y cuánto, frente a la línea base;
- cuánto cuesta calcularlo para todo el catálogo (tiempo, disco, GPU) y si corre en el servidor sin GPU;
- cómo se explica en una frase a quien revisa un par.
