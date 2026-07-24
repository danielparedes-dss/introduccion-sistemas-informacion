"""Módulo SCM: inventario, proveedores y órdenes de compra."""

from __future__ import annotations

from config import CANTIDAD_REPOSICION_MINIMA
from gestor_csv import GestorCSV
from modelos import (
    DetalleOrdenCompra,
    DetalleVenta,
    OrdenCompra,
    Producto,
    fecha_actual,
)


class ModuloSCM:
    def __init__(self, gestor: GestorCSV):
        self.gestor = gestor

    def procesar_venta(self, detalles: list[DetalleVenta]) -> list[OrdenCompra]:
        ordenes_generadas: list[OrdenCompra] = []
        for detalle in detalles:
            producto = detalle.producto
            if not producto.descontar_stock(detalle.cantidad):
                raise ValueError(f"Stock insuficiente para {producto.nombre}.")
            self.gestor.actualizar_fila(
                "productos",
                "id_producto",
                producto.id_producto,
                {"stock_actual": producto.stock_actual},
            )
            if producto.verificar_stock_bajo():
                orden = self.generar_orden_compra(producto)
                if orden:
                    ordenes_generadas.append(orden)
        return ordenes_generadas

    def generar_orden_compra(self, producto: Producto) -> OrdenCompra | None:
        if self._existe_orden_pendiente(producto.id_producto):
            return None

        cantidad = max(
            CANTIDAD_REPOSICION_MINIMA,
            producto.stock_minimo * 3 - producto.stock_actual,
        )
        id_orden = self.gestor.generar_id("ordenes_compra", "id_orden", "OC")
        id_detalle = self.gestor.generar_id(
            "detalle_ordenes_compra", "id_detalle_orden", "DO"
        )
        orden = OrdenCompra(
            id_orden=id_orden,
            fecha=fecha_actual(),
            id_proveedor=producto.id_proveedor,
        )
        detalle = DetalleOrdenCompra(
            id_detalle_orden=id_detalle,
            id_orden=id_orden,
            producto=producto,
            cantidad=cantidad,
            costo_unitario=producto.costo_unitario,
        )
        detalle.calcular_subtotal()
        orden.agregar_detalle(detalle)
        orden.calcular_total()
        self.gestor.agregar("ordenes_compra", orden.to_dict())
        self.gestor.agregar("detalle_ordenes_compra", detalle.to_dict())
        return orden

    def consultar_ordenes(self) -> list[dict[str, str]]:
        return self.gestor.leer("ordenes_compra")

    def consultar_ordenes_detalladas(self) -> list[dict[str, str]]:
        """Igual que consultar_ordenes, pero agrega el nombre del producto
        agotado que originó cada orden en la clave "productos"."""
        nombres_producto = {
            fila["id_producto"]: fila["nombre"] for fila in self.gestor.leer("productos")
        }
        productos_por_orden: dict[str, list[str]] = {}
        for fila in self.gestor.leer("detalle_ordenes_compra"):
            nombre = nombres_producto.get(fila["id_producto"], fila["id_producto"])
            productos_por_orden.setdefault(fila["id_orden"], []).append(nombre)

        ordenes = []
        for orden in self.consultar_ordenes():
            orden = dict(orden)
            orden["productos"] = ", ".join(productos_por_orden.get(orden["id_orden"], [])) or "-"
            ordenes.append(orden)
        return ordenes

    def marcar_orden_recibida(self, id_orden: str) -> None:
        orden = self.gestor.buscar("ordenes_compra", "id_orden", id_orden)
        if not orden:
            raise ValueError("La orden seleccionada no existe.")
        if orden["estado"] == "Recibida":
            raise ValueError("La orden ya fue recibida anteriormente.")

        detalles = [
            fila for fila in self.gestor.leer("detalle_ordenes_compra")
            if fila["id_orden"] == id_orden
        ]
        for detalle in detalles:
            fila_producto = self.gestor.buscar(
                "productos", "id_producto", detalle["id_producto"]
            )
            if not fila_producto:
                continue
            producto = Producto.from_dict(fila_producto)
            producto.aumentar_stock(int(detalle["cantidad"]))
            self.gestor.actualizar_fila(
                "productos", "id_producto", producto.id_producto,
                {"stock_actual": producto.stock_actual}
            )
        self.gestor.actualizar_fila(
            "ordenes_compra", "id_orden", id_orden, {"estado": "Recibida"}
        )

    def _existe_orden_pendiente(self, id_producto: str) -> bool:
        detalles = {
            fila["id_orden"] for fila in self.gestor.leer("detalle_ordenes_compra")
            if fila["id_producto"] == id_producto
        }
        return any(
            fila["id_orden"] in detalles and fila["estado"] in {"Pendiente", "Enviada"}
            for fila in self.gestor.leer("ordenes_compra")
        )
