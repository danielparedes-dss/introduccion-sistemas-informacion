"""Sistema POS y coordinación de la integración empresarial."""

from __future__ import annotations

from datetime import datetime

from config import TASA_IMPUESTO
from gestor_csv import GestorCSV
from modelos import Cliente, DetalleVenta, Producto, Proveedor, Venta
from modulo_erp import ModuloERP
from modulo_scm import ModuloSCM


class SistemaVentas:
    METODOS_PAGO = ["Efectivo", "Tarjeta", "Transferencia", "Billetera electrónica"]

    def __init__(self, gestor: GestorCSV):
        self.gestor = gestor
        self.modulo_erp = ModuloERP(gestor)
        self.modulo_scm = ModuloSCM(gestor)

    def listar_clientes(self) -> list[Cliente]:
        return [Cliente.from_dict(fila) for fila in self.gestor.leer("clientes")]

    def listar_productos(self) -> list[Producto]:
        return [Producto.from_dict(fila) for fila in self.gestor.leer("productos")]

    def listar_proveedores(self) -> list[Proveedor]:
        return [Proveedor.from_dict(fila) for fila in self.gestor.leer("proveedores")]

    def registrar_cliente(
        self, nombre: str, genero: str, tipo_cliente: str
    ) -> Cliente:
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("El nombre del cliente es obligatorio.")
        if any(c.nombre.lower() == nombre.lower() for c in self.listar_clientes()):
            raise ValueError("Ya existe un cliente con ese nombre.")
        cliente = Cliente(
            id_cliente=self.gestor.generar_id("clientes", "id_cliente", "C", 3),
            nombre=nombre,
            genero=genero,
            tipo_cliente=tipo_cliente,
            fecha_registro=datetime.now().strftime("%Y-%m-%d"),
        )
        self.gestor.agregar("clientes", cliente.to_dict())
        return cliente

    def registrar_producto(
        self,
        nombre: str,
        categoria: str,
        precio_venta: float,
        costo_unitario: float,
        stock_actual: int,
        stock_minimo: int,
        id_proveedor: str,
    ) -> Producto:
        if not nombre.strip():
            raise ValueError("El nombre del producto es obligatorio.")
        if precio_venta <= 0 or costo_unitario < 0:
            raise ValueError("Los precios ingresados no son válidos.")
        if stock_actual < 0 or stock_minimo < 0:
            raise ValueError("El stock no puede ser negativo.")
        if not self.gestor.buscar("proveedores", "id_proveedor", id_proveedor):
            raise ValueError("El proveedor seleccionado no existe.")
        producto = Producto(
            id_producto=self.gestor.generar_id("productos", "id_producto", "P", 3),
            nombre=nombre.strip(),
            categoria=categoria.strip(),
            precio_venta=precio_venta,
            costo_unitario=costo_unitario,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            id_proveedor=id_proveedor,
        )
        self.gestor.agregar("productos", producto.to_dict())
        return producto

    def registrar_venta(
        self,
        id_cliente: str,
        metodo_pago: str,
        items: list[tuple[str, int]],
    ) -> tuple[Venta, list]:
        if metodo_pago not in self.METODOS_PAGO:
            raise ValueError("El método de pago no es válido.")
        if not items:
            raise ValueError("Debe agregar al menos un producto.")

        fila_cliente = self.gestor.buscar("clientes", "id_cliente", id_cliente)
        if not fila_cliente:
            raise ValueError("El cliente seleccionado no existe.")
        cliente = Cliente.from_dict(fila_cliente)

        productos = {p.id_producto: p for p in self.listar_productos()}
        cantidades_acumuladas: dict[str, int] = {}
        for id_producto, cantidad in items:
            if cantidad <= 0:
                raise ValueError("Todas las cantidades deben ser mayores que cero.")
            cantidades_acumuladas[id_producto] = (
                cantidades_acumuladas.get(id_producto, 0) + cantidad
            )

        for id_producto, cantidad in cantidades_acumuladas.items():
            producto = productos.get(id_producto)
            if not producto:
                raise ValueError(f"No existe el producto {id_producto}.")
            if cantidad > producto.stock_actual:
                raise ValueError(
                    f"Stock insuficiente para {producto.nombre}. "
                    f"Disponible: {producto.stock_actual}."
                )

        id_venta = self.gestor.generar_id("ventas", "id_venta", "V")
        venta = Venta(
            id_venta=id_venta,
            fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cliente=cliente,
            metodo_pago=metodo_pago,
        )
        for id_producto, cantidad in cantidades_acumuladas.items():
            producto = productos[id_producto]
            detalle = DetalleVenta(
                id_detalle=self.gestor.generar_id(
                    "detalle_ventas", "id_detalle", "DV"
                ),
                id_venta=id_venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio_venta,
            )
            # Evita repetir el mismo ID antes de guardar los detalles.
            numero = int(detalle.id_detalle[2:]) + len(venta.detalles)
            detalle.id_detalle = f"DV{numero:06d}"
            detalle.calcular_subtotal()
            venta.agregar_detalle(detalle)

        venta.calcular_subtotal()
        venta.calcular_impuesto(TASA_IMPUESTO)
        venta.calcular_total()

        # Una sola acción del POS actualiza todos los archivos relacionados.
        self.gestor.agregar("ventas", venta.to_dict())
        self.gestor.agregar_varias(
            "detalle_ventas", [detalle.to_dict() for detalle in venta.detalles]
        )
        ordenes = self.modulo_scm.procesar_venta(venta.detalles)
        self.modulo_erp.registrar_ingreso(venta)
        return venta, ordenes

    def consultar_historial(self) -> list[dict[str, str]]:
        return self.gestor.leer("ventas")
