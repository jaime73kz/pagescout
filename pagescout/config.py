"""Carga y valida la configuración de un trabajo de extracción.

Un trabajo se describe en un archivo TOML:

    urls = ["https://example.com/p1", "https://example.com/p2"]
    item_selector = ".product"       # opcional: una fila por cada elemento que coincida

    [fields]
    title = "h2.name"
    price = { selector = ".price", type = "price" }   # text (por defecto), price, int, link, attr
    image = { selector = "img", type = "attr", attr = "src" }
"""
from dataclasses import dataclass, field
from pathlib import Path

import tomllib

VALID_TYPES = {"text", "price", "int", "link", "attr"}


class ConfigError(ValueError):
    """La configuración es inválida."""


@dataclass
class Field:
    name: str
    selector: str
    type: str = "text"
    attr: str | None = None


@dataclass
class Job:
    urls: list[str]
    fields: list[Field]
    item_selector: str | None = None
    delay: float = 1.0
    retries: int = 3
    timeout: float = 15.0
    respect_robots: bool = True
    user_agent: str = "PageScout/1.0 (+educational use)"
    extra: dict = field(default_factory=dict)


def _parse_field(name: str, raw) -> Field:
    if isinstance(raw, str):
        return Field(name=name, selector=raw)
    if not isinstance(raw, dict) or "selector" not in raw:
        raise ConfigError(f"El campo '{name}' necesita un 'selector'.")
    ftype = raw.get("type", "text")
    if ftype not in VALID_TYPES:
        raise ConfigError(
            f"Tipo '{ftype}' no válido en '{name}'. Usa uno de: {sorted(VALID_TYPES)}"
        )
    if ftype == "attr" and not raw.get("attr"):
        raise ConfigError(f"El campo '{name}' es de tipo 'attr' y necesita 'attr'.")
    return Field(name=name, selector=raw["selector"], type=ftype, attr=raw.get("attr"))


def parse_job(data: dict) -> Job:
    if not isinstance(data, dict):
        raise ConfigError("El archivo de configuración debe ser una tabla TOML.")
    urls = data.get("urls")
    if not urls or not isinstance(urls, list):
        raise ConfigError("Falta la lista 'urls'.")
    fields_raw = data.get("fields")
    if not fields_raw or not isinstance(fields_raw, dict):
        raise ConfigError("Falta el diccionario 'fields'.")
    fields = [_parse_field(n, r) for n, r in fields_raw.items()]
    return Job(
        urls=urls,
        fields=fields,
        item_selector=data.get("item_selector"),
        delay=float(data.get("delay", 1.0)),
        retries=int(data.get("retries", 3)),
        timeout=float(data.get("timeout", 15.0)),
        respect_robots=bool(data.get("respect_robots", True)),
        user_agent=data.get("user_agent", "PageScout/1.0 (+educational use)"),
    )


def load_job(path: str | Path) -> Job:
    try:
        with open(path, "rb") as fh:
            return parse_job(tomllib.load(fh))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"El archivo TOML tiene un error de sintaxis: {exc}") from exc
