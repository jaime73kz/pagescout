# Tutorial: cómo usar PageScout paso a paso

Este tutorial es para alguien que nunca ha usado la herramienta. En 10 minutos sacarás los datos de una web a un Excel.

## 1. Qué necesitas

- Un ordenador con Windows, Mac o Linux.
- **Python 3.11 o más nuevo.** Para comprobarlo, abre un terminal y escribe `python --version`.
- Conexión a internet.

## 2. Descargar el proyecto

Entra en la página del proyecto en GitHub y pulsa el botón verde **Code**, luego **Download ZIP**. Extrae el ZIP en una carpeta, por ejemplo en el Escritorio.

Si usas Git, también puedes hacer:

```bash
git clone https://github.com/jaime73kz/pagescout.git
```

## 3. Abrir el terminal dentro de la carpeta

En Windows:

1. Abre la carpeta `pagescout` en el Explorador de archivos. Dentro tienes que ver `README.md` y `requirements.txt`.
2. Haz clic en la barra de arriba donde sale la ruta.
3. Escribe `cmd` y pulsa **Enter**.

Se abre una ventana negra. Es el terminal, y ya está dentro de la carpeta correcta.

## 4. Instalar lo necesario

Escribe este comando y pulsa Enter:

```
pip install -r requirements.txt
```

Salen muchas líneas. Espera a que termine. Los avisos amarillos sobre PATH se pueden ignorar.

## 5. Comprobar que todo funciona

```
python -m pytest
```

Debe salir `passed` en verde. Eso significa que el programa funciona en tu ordenador.

## 6. Tu primera extracción

Vamos a usar `books.toscrape.com`, una web de práctica hecha a propósito para aprender scraping. Es un catálogo falso de libros.

Ejecuta:

```
python -m pagescout examples/books.toml -o libros.xlsx
```

Verás mensajes como `Guardadas 40 filas en libros.xlsx`. Abre `libros.xlsx` con Excel y tendrás el título, el precio, la disponibilidad y el enlace de cada libro.

Puedes cambiar la extensión para otro formato: `-o libros.csv` o `-o libros.json`.

## 7. Entender el archivo de configuración

Abre `examples/books.toml` con el Bloc de notas:

```toml
urls = ["https://books.toscrape.com/"]
item_selector = "article.product_pod"

[fields]
title = { selector = "h3 a", type = "attr", attr = "title" }
price = { selector = "p.price_color", type = "price" }
```

- `urls`: las páginas que quieres descargar.
- `item_selector`: qué elemento se repite en la página. Cada libro sale como una fila.
- `fields`: los datos que quieres sacar de cada elemento.
- `selector`: el selector CSS que apunta al dato.
- `type`: cómo convertir el dato.

### Tipos de campo

- `text`: el texto del elemento. Es el tipo por defecto.
- `price`: un precio como número. Entiende `1.299,50 €` y `$1,299.50`.
- `int`: un número entero sacado del texto.
- `link`: un enlace convertido a dirección completa.
- `attr`: cualquier atributo HTML. Se indica cuál con `attr`.

## 8. Cómo hacerlo con tu propia web

1. Copia `examples/tienda.toml` y ponle otro nombre, por ejemplo `mi_web.toml`.
2. Cambia las `urls` por las de tu web.
3. Abre la web en el navegador, haz clic derecho sobre un producto y elige **Inspeccionar**. Verás el HTML.
4. Busca el elemento que se repite para cada producto y su clase, por ejemplo `div class="product"`. Eso es tu `item_selector`, escrito como `.product`.
5. Haz lo mismo con el nombre, el precio y el resto de datos.
6. Ejecuta `python -m pagescout mi_web.toml -o resultado.xlsx`.

Si sale `No se extrajo ningún dato`, el selector no coincide con la página. Revísalo con Inspeccionar.

## 9. Problemas comunes

- **`python` no se reconoce:** reinstala Python y marca la casilla *Add Python to PATH*.
- **`No such file or directory`:** el terminal no está dentro de la carpeta del proyecto. Repite el paso 3.
- **`robots.txt no permite acceder`:** esa web prohíbe que programas accedan a esa página. Respétalo.
- **Error de conexión:** el programa reintenta hasta 3 veces. Comprueba tu internet.

## 10. Uso responsable

Revisa los términos de uso de cada web. No hagas peticiones demasiado rápidas: por defecto el programa espera 1 segundo entre peticiones y respeta `robots.txt`. No extraigas datos personales de otras personas.
