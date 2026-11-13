"""Interfaz de línea de comandos."""
import argparse
import logging
import sys

from . import __version__
from .config import ConfigError, load_job
from .export import export
from .extract import extract_rows
from .fetch import FetchError, Fetcher


def run(config_path: str, output: str) -> int:
    job = load_job(config_path)
    fetcher = Fetcher(job.user_agent, job.delay, job.retries, job.timeout, job.respect_robots)
    rows: list[dict] = []
    failed = 0
    for url in job.urls:
        try:
            html = fetcher.get(url)
        except FetchError as exc:
            logging.error("%s", exc)
            failed += 1
            continue
        found = extract_rows(html, job.fields, job.item_selector, base_url=url)
        logging.info("%s -> %d filas", url, len(found))
        rows.extend(found)
    if not rows:
        logging.error("No se extrajo ningún dato.")
        return 1
    path = export(rows, output)
    logging.info("Guardadas %d filas en %s (%d URLs fallidas)", len(rows), path, failed)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="pagescout",
        description="Extrae datos de páginas web con selectores CSS y los exporta a CSV, JSON o Excel.",
    )
    parser.add_argument("config", help="archivo TOML con el trabajo de extracción")
    parser.add_argument("-o", "--output", default="resultado.csv",
                        help="archivo de salida (.csv, .json o .xlsx)")
    parser.add_argument("-v", "--verbose", action="store_true", help="mostrar más detalle")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s: %(message)s")
    try:
        return run(args.config, args.output)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        logging.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
