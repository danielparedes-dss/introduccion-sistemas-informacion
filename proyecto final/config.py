"""Configuración general de QuickMarket."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CARPETA_DATOS = BASE_DIR / "datos"

# Tasa simulada para mantener coherencia con el CSV académico entregado.
# No representa una regla tributaria oficial.
TASA_IMPUESTO = 0.05

CANTIDAD_REPOSICION_MINIMA = 20
CONSUMIDOR_FINAL_ID = "C000"
