"""Clases de dominio del sistema QuickMarket."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Cliente:
    id_cliente: str
    nombre: str
    genero: str
    tipo_cliente: str
    fecha_registro: str

    def mostrar_informacion(self) -> str:
        return f"{self.id_cliente} - {self.nombre} ({self.tipo_cliente})"

    def actualizar_tipo(self, nuevo_tipo: str) -> None:
        self.tipo_cliente = nuevo_tipo

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_cliente": self.id_cliente,
            "nombre": self.nombre,
            "genero": self.genero,
            "tipo_cliente": self.tipo_cliente,
            "fecha_registro": self.fecha_registro,
        }

    @classmethod
    def from_dict(cls, fila: dict[str, str]) -> "Cliente":
        return cls(**fila)


@dataclass
class Proveedor:
    id_proveedor: str
    nombre: str
    telefono: str
    correo: str
    estado: str = "Activo"

    def mostrar_informacion(self) -> str:
        return f"{self.id_proveedor} - {self.nombre}"

    def cambiar_estado(self, nuevo_estado: str) -> None:
        self.estado = nuevo_estado

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_proveedor": self.id_proveedor,
            "nombre": self.nombre,
            "telefono": self.telefono,
            "correo": self.correo,
            "estado": self.estado,
        }

    @classmethod
    def from_dict(cls, fila: dict[str, str]) -> "Proveedor":
        return cls(**fila)


@dataclass
class Producto:
    id_producto: str
    nombre: str
    categoria: str
    precio_venta: float
    costo_unitario: float
    stock_actual: int
    stock_minimo: int
    id_proveedor: str

    def descontar_stock(self, cantidad: int) -> bool:
        if cantidad <= 0 or cantidad > self.stock_actual:
            return False
        self.stock_actual -= cantidad
        return True

    def aumentar_stock(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad recibida debe ser mayor que cero.")
        self.stock_actual += cantidad

    def verificar_stock_bajo(self) -> bool:
        return self.stock_actual <= self.stock_minimo

    def calcular_utilidad(self) -> float:
        return round(self.precio_venta - self.costo_unitario, 2)

    def mostrar_informacion(self) -> str:
        return (
            f"{self.id_producto} - {self.nombre} | "
            f"Precio: ${self.precio_venta:.2f} | Stock: {self.stock_actual}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_producto": self.id_producto,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "precio_venta": f"{self.precio_venta:.2f}",
            "costo_unitario": f"{self.costo_unitario:.2f}",
            "stock_actual": self.stock_actual,
            "stock_minimo": self.stock_minimo,
            "id_proveedor": self.id_proveedor,
        }

    @classmethod
    def from_dict(cls, fila: dict[str, str]) -> "Producto":
        return cls(
            id_producto=fila["id_producto"],
            nombre=fila["nombre"],
            categoria=fila["categoria"],
            precio_venta=float(fila["precio_venta"]),
            costo_unitario=float(fila["costo_unitario"]),
            stock_actual=int(float(fila["stock_actual"])),
            stock_minimo=int(float(fila["stock_minimo"])),
            id_proveedor=fila["id_proveedor"],
        )


@dataclass
class DetalleVenta:
    id_detalle: str
    id_venta: str
    producto: Producto
    cantidad: int
    precio_unitario: float
    subtotal: float = 0.0

    def calcular_subtotal(self) -> float:
        self.subtotal = round(self.cantidad * self.precio_unitario, 2)
        return self.subtotal

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_detalle": self.id_detalle,
            "id_venta": self.id_venta,
            "id_producto": self.producto.id_producto,
            "cantidad": self.cantidad,
            "precio_unitario": f"{self.precio_unitario:.2f}",
            "subtotal": f"{self.subtotal:.2f}",
        }


@dataclass
class Venta:
    id_venta: str
    fecha: str
    cliente: Cliente
    metodo_pago: str
    detalles: list[DetalleVenta] = field(default_factory=list)
    subtotal: float = 0.0
    impuesto: float = 0.0
    total: float = 0.0

    def agregar_detalle(self, detalle: DetalleVenta) -> None:
        self.detalles.append(detalle)

    def calcular_subtotal(self) -> float:
        self.subtotal = round(sum(d.calcular_subtotal() for d in self.detalles), 2)
        return self.subtotal

    def calcular_impuesto(self, tasa: float) -> float:
        self.impuesto = round(self.subtotal * tasa, 2)
        return self.impuesto

    def calcular_total(self) -> float:
        self.total = round(self.subtotal + self.impuesto, 2)
        return self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_venta": self.id_venta,
            "fecha": self.fecha,
            "id_cliente": self.cliente.id_cliente,
            "metodo_pago": self.metodo_pago,
            "subtotal": f"{self.subtotal:.2f}",
            "impuesto": f"{self.impuesto:.2f}",
            "total": f"{self.total:.2f}",
        }


@dataclass
class MovimientoFinanciero:
    id_movimiento: str
    fecha: str
    tipo: str
    concepto: str
    monto: float
    id_venta: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_movimiento": self.id_movimiento,
            "fecha": self.fecha,
            "tipo": self.tipo,
            "concepto": self.concepto,
            "monto": f"{self.monto:.2f}",
            "id_venta": self.id_venta,
        }


@dataclass
class DetalleOrdenCompra:
    id_detalle_orden: str
    id_orden: str
    producto: Producto
    cantidad: int
    costo_unitario: float
    subtotal: float = 0.0

    def calcular_subtotal(self) -> float:
        self.subtotal = round(self.cantidad * self.costo_unitario, 2)
        return self.subtotal

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_detalle_orden": self.id_detalle_orden,
            "id_orden": self.id_orden,
            "id_producto": self.producto.id_producto,
            "cantidad": self.cantidad,
            "costo_unitario": f"{self.costo_unitario:.2f}",
            "subtotal": f"{self.subtotal:.2f}",
        }


@dataclass
class OrdenCompra:
    id_orden: str
    fecha: str
    id_proveedor: str
    estado: str = "Pendiente"
    detalles: list[DetalleOrdenCompra] = field(default_factory=list)
    total_estimado: float = 0.0

    def agregar_detalle(self, detalle: DetalleOrdenCompra) -> None:
        self.detalles.append(detalle)

    def calcular_total(self) -> float:
        self.total_estimado = round(
            sum(detalle.calcular_subtotal() for detalle in self.detalles), 2
        )
        return self.total_estimado

    def cambiar_estado(self, nuevo_estado: str) -> None:
        self.estado = nuevo_estado

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_orden": self.id_orden,
            "fecha": self.fecha,
            "id_proveedor": self.id_proveedor,
            "estado": self.estado,
            "total_estimado": f"{self.total_estimado:.2f}",
        }


def fecha_actual() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
