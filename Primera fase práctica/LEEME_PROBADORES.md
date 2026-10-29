# Probar la app de similitud entre videojuegos

Toma unos 10 minutos la primera vez, y menos de 1 minuto las siguientes.
Lo que pruebas: dado un juego (o una descripción), la app muestra los juegos más
parecidos según su descripción y las palabras que explican el parecido.

## Qué necesitas

- La carpeta de la app (esta).
- El archivo de datos `juegos_texto_en.parquet` dentro de la carpeta `data/`.
  Si ya está ahí, no hagas nada. Si no, pídeselo a [NOMBRE] y ponlo en esa carpeta
  (créala si no existe).
- Los datos son solo para el grupo: no los subas a ningún sitio público ni a un
  repositorio abierto.

## Instalación (una sola vez)

Abre una terminal en esta carpeta (en Windows, el «Anaconda Prompt») y elige UNA opción.

**Con Anaconda o Miniconda**

```
conda env create -f environment.yml
conda activate similitud-juegos
```

**Sin conda (solo Python 3.11 o superior)**

```
python -m venv .venv
.venv\Scripts\activate          (en Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Ejecutar

```
python app.py
```

La primera vez tarda un poco en preparar los datos. Cuando diga `Running on local URL`,
abre esa dirección (normalmente http://127.0.0.1:7860) en el navegador.
Para cerrar la app, vuelve a la terminal y presiona Ctrl+C.

## Qué probar

1. **Buscar similares:** escribe un juego que conozcas bien (por ejemplo, un juego de una saga)
   y mira si los resultados tienen sentido.
2. **Comparar dos juegos:** pon dos juegos que creas muy parecidos y dos que no.
3. **Texto nuevo:** pega la descripción de un juego (en inglés) y mira cuál sale primero.

Solo hay juegos con descripción en inglés. Si un título no aparece, la app te sugiere nombres parecidos.

## Guardar casos

Cuando un resultado te parezca interesante (acertado o equivocado), abre «Guardar un caso»,
elige el resultado y márcalo como Similar, No similar o Posible copia. Escribe tu nombre
arriba de todo para que sepamos quién lo marcó. No hace falta marcar muchos.

Al terminar, envía a [NOMBRE] el archivo `casos/casos_guardados.csv`.

## Si algo falla

- *«No encuentro el archivo de datos»*: falta poner el `.parquet` en `data/`.
- *Error al instalar o ejecutar*: copia el mensaje completo y mándalo a [NOMBRE].
- Recuerda: la similitud no es plagio. La app solo sugiere candidatos para revisión humana.
