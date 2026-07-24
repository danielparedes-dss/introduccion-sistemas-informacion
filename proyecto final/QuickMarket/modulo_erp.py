"""Módulo ERP financiero simplificado."""

from __future__ import annotations

from gestor_csv import GestorCSV
from modelos import MovimientoFinanciero, Venta


class ModuloERP:
    def __init__(self, gestor: GestorCSV):
        self.gestor = gestor

    def registrar_ingreso(self, venta: Venta) -> MovimientoFinanciero:
        movimiento = MovimientoFinanciero(
            id_movimiento=self.gestor.generar_id(
                "movimientos_financieros", "id_movimiento", "M"
            ),
            fecha=venta.fecha,
            tipo="Ingreso",
            concepto=f"Venta {venta.id_venta}",
            monto=venta.total,
            id_venta=venta.id_venta,
        )
        self.gestor.agregar("movimientos_financieros", movimiento.to_dict())
        return movimiento

    def consultar_movimientos(self) -> list[dict[str, str]]:
        return self.gestor.leer("movimientos_financieros")

    def calcular_ingresos_totales(self) -> float:
        return round(
            sum(
                float(fila["monto"])
                for fila in self.consultar_movimientos()
                if fila["tipo"] == "Ingreso"
            ),
            2,
        )
