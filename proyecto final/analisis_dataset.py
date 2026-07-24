"""Resumen básico del histórico usando solo la biblioteca estándar."""

import csv
from pathlib import Path


def analizar(ruta: str | Path = "datos/historico_supermarket.csv") -> None:
    ruta = Path(ruta)
    with ruta.open("r", newline="", encoding="utf-8-sig") as archivo:
        filas = list(csv.DictReader(archivo))
    total_ventas = sum(float(fila.get("Sales", 0) or 0) for fila in filas)
    cantidad = sum(int(float(fila.get("Quantity", 0) or 0)) for fila in filas)
    categorias = sorted({fila.get("Product line", "") for fila in filas})
    print(f"Registros: {len(filas)}")
    print(f"Ventas históricas: ${total_ventas:,.2f}")
    print(f"Unidades: {cantidad}")
    print(f"Categorías: {len(categorias)}")


if __name__ == "__main__":
    analizar()
