"""Exportación de filas a CSV, JSON o Excel."""
import csv
import json
from pathlib import Path

from openpyxl import Workbook


def _columns(rows: list[dict]) -> list[str]:
    cols: list[str] = []
    for row in rows:
        for key in row:
            if key not in cols:
                cols.append(key)
    return cols


def write_csv(rows, path):
    cols = _columns(rows)
    with open(path, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=2)


def write_xlsx(rows, path):
    cols = _columns(rows)
    wb = Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.append(cols)
    for row in rows:
        ws.append([row.get(c) for c in cols])
    for i, col in enumerate(cols, start=1):
        width = max(len(str(col)), *(len(str(r.get(col, ""))) for r in rows)) if rows else len(col)
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(width + 2, 60)
    wb.save(path)


WRITERS = {".csv": write_csv, ".json": write_json, ".xlsx": write_xlsx}


def export(rows: list[dict], path: str | Path) -> Path:
    path = Path(path)
    writer = WRITERS.get(path.suffix.lower())
    if writer is None:
        raise ValueError(f"Formato no soportado: '{path.suffix}'. Usa .csv, .json o .xlsx")
    writer(rows, path)
    return path
