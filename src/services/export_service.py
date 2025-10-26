"""Servicio para exportación de gastos a CSV."""
import csv
import os
from typing import List
from src.schemas import Gasto
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

EXPORT_PATH = "data/import_actual.csv"


def export_to_csv(gastos: List[Gasto]) -> int:
    """
    Exporta gastos a CSV compatible con Actual Budget.

    Args:
        gastos: Lista de gastos a exportar

    Returns:
        Número de gastos exportados
    """
    rows = []

    for gasto in gastos:
        # Extraer solo la fecha (YYYY-MM-DD)
        date_str = gasto.date_iso.split(" ")[0] if " " in gasto.date_iso else gasto.date_iso

        rows.append({
            "Date": date_str,
            "Payee": gasto.payee,
            "Category": gasto.category,
            "Notes": gasto.description,
            "Amount": str(gasto.amount)
        })

    # Crear directorio si no existe
    os.makedirs(os.path.dirname(EXPORT_PATH), exist_ok=True)

    # Escribir CSV
    with open(EXPORT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Payee", "Category", "Notes", "Amount"])
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Exportados {len(rows)} gastos a {EXPORT_PATH}")
    return len(rows)
