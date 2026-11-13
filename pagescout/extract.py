"""Extracción de datos de HTML con selectores CSS."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import Field

_PRICE_RE = re.compile(r"-?\d[\d.,]*")


def parse_price(text: str) -> float | None:
    """Convierte '1.299,50 €' o '$1,299.50' en 1299.5. Devuelve None si no hay número."""
    match = _PRICE_RE.search(text or "")
    if not match:
        return None
    num = match.group(0).rstrip(".,")
    if "," in num and "." in num:
        # El último separador es el decimal.
        if num.rfind(",") > num.rfind("."):
            num = num.replace(".", "").replace(",", ".")
        else:
            num = num.replace(",", "")
    elif "," in num:
        head, _, tail = num.rpartition(",")
        num = head.replace(",", "") + "." + tail if len(tail) <= 2 else num.replace(",", "")
    elif num.count(".") > 1 or (num.count(".") == 1 and len(num.split(".")[1]) == 3):
        num = num.replace(".", "")
    try:
        return float(num)
    except ValueError:
        return None


def parse_int(text: str) -> int | None:
    digits = re.sub(r"[^\d-]", "", text or "")
    try:
        return int(digits)
    except ValueError:
        return None


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_value(node, fld: Field, base_url: str = ""):
    """Extrae el valor de un campo desde un nodo BeautifulSoup."""
    el = node.select_one(fld.selector)
    if el is None:
        return None
    if fld.type == "attr":
        return el.get(fld.attr)
    if fld.type == "link":
        href = el.get("href")
        return urljoin(base_url, href) if href else None
    text = clean_text(el.get_text(" "))
    if fld.type == "price":
        return parse_price(text)
    if fld.type == "int":
        return parse_int(text)
    return text


def extract_rows(html: str, fields: list[Field], item_selector: str | None = None,
                 base_url: str = "") -> list[dict]:
    """Devuelve una lista de filas (diccionarios) a partir de un HTML."""
    soup = BeautifulSoup(html, "html.parser")
    nodes = soup.select(item_selector) if item_selector else [soup]
    rows = []
    for node in nodes:
        row = {f.name: extract_value(node, f, base_url) for f in fields}
        if any(v not in (None, "") for v in row.values()):
            row["source_url"] = base_url
            rows.append(row)
    return rows
