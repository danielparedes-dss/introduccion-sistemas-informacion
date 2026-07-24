"""Prueba automática del flujo POS -> SCM -> ERP usando una carpeta temporal."""

from pathlib import Path
from tempfile import TemporaryDirectory

from gestor_csv import GestorCSV
from modelos import Cliente, Producto, Proveedor
from sistema_ventas import SistemaVentas


def ejecutar_prueba() -> None:
    with TemporaryDirectory() as temporal:
        gestor = GestorCSV(Path(temporal))
        gestor.crear_archivos()
        gestor.agregar("clientes", Cliente("C001", "Cliente prueba", "No especificado", "Normal", "2026-07-23").to_dict())
        gestor.agregar("proveedores", Proveedor("PR001", "Proveedor prueba", "0990000000", "prueba@email.com").to_dict())
        gestor.agregar("productos", Producto("P001", "Producto prueba", "Pruebas", 10.0, 6.0, 6, 5, "PR001").to_dict())

        sistema = SistemaVentas(gestor)
        venta, ordenes = sistema.registrar_venta("C001", "Efectivo", [("P001", 2)])

        producto = gestor.buscar("productos", "id_producto", "P001")
        assert venta.total == 21.0, venta.total
        assert producto and int(producto["stock_actual"]) == 4
        assert len(gestor.leer("movimientos_financieros")) == 1
        assert len(ordenes) == 1
        assert len(gestor.leer("ordenes_compra")) == 1
        print("PRUEBA SUPERADA")
        print(f"Venta: {venta.id_venta} | Total: ${venta.total:.2f}")
        print("ERP: ingreso registrado")
        print("SCM: stock actualizado y orden generada")


if __name__ == "__main__":
    ejecutar_prueba()
