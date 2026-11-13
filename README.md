# PageScout

Herramienta de línea de comandos en Python que **extrae datos estructurados de páginas web** y los exporta a **CSV, JSON o Excel**. Tú describes qué quieres sacar en un archivo TOML con selectores CSS, sin tocar código.

## Qué hace

- Extrae varios campos por página, o **una fila por elemento** (por ejemplo, cada producto de un catálogo).
- Convierte los valores: precios (`1.299,50 €` pasa a `1299.5`), números enteros, enlaces absolutos y atributos HTML.
- Descarga con **reintentos automáticos**, espera entre peticiones y respeto a **robots.txt**.
- Detecta bien la codificación para que las tildes y la ñ no se rompan.
- Exporta a `.csv`, `.json` o `.xlsx` según la extensión del archivo de salida.
- Incluye **tests automáticos** con pytest.

## Instalación

```bash
git clone https://github.com/jaime73kz/pagescout.git
cd pagescout
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

¿Primera vez? Sigue el [tutorial paso a paso](docs/TUTORIAL.md).

Prueba rápida con una web de práctica:

```bash
python -m pagescout examples/books.toml -o libros.xlsx
```

1. Copia `examples/tienda.toml` y cámbialo por las URLs y selectores de la web que quieras.
2. Ejecuta:

```bash
python -m pagescout mi_trabajo.toml -o resultado.xlsx
```

Opciones: `-o` archivo de salida (`.csv`, `.json`, `.xlsx`), `-v` más detalle, `--version`.

### Ejemplo de configuración

```toml
urls = ["https://example.com/catalogo?page=1"]
item_selector = ".product"   # una fila por cada elemento que coincida
delay = 1.5                  # segundos entre peticiones

[fields]
title = "h2.name"
price = { selector = ".price", type = "price" }   # text (por defecto), price, int, link, attr
url = { selector = "a", type = "link" }
image = { selector = "img", type = "attr", attr = "src" }
```

### Tipos de campo

- `text`: el texto limpio del elemento, sin espacios sobrantes.
- `price`: un número decimal, entiende formato español y anglosajón.
- `int`: un número entero sacado del texto.
- `link`: el `href` convertido a URL absoluta.
- `attr`: cualquier atributo HTML, indicado en `attr`.

## Estructura

```
pagescout/
  config.py    lectura y validación del archivo TOML
  fetch.py     descarga con reintentos, pausas y robots.txt
  extract.py   selectores CSS y conversión de valores
  export.py    escritura a CSV, JSON y Excel
  cli.py       interfaz de línea de comandos
tests/         tests con pytest
examples/      configuraciones de ejemplo
docs/          tutorial paso a paso
```

## Tests

```bash
python -m pytest
```

## Uso responsable

Respeta los términos de uso de cada web, su `robots.txt` y no hagas peticiones demasiado rápidas. Por defecto el programa espera 1 segundo entre peticiones y respeta `robots.txt`.

## Ideas para ampliar

- Seguir automáticamente la paginación ("siguiente página").
- Caché en disco para no repetir descargas.
- Soporte para páginas que cargan datos con JavaScript.
- Descargar las imágenes encontradas.

## Licencia

MIT
