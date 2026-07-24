"""Carga de datos iniciales e importación del histórico académico.

Esta versión usa únicamente la biblioteca estándar de Python.
"""

from __future__ import annotations

import csv
from datetime import datetime, timedelta
from pathlib import Path

from config import CONSUMIDOR_FINAL_ID
from gestor_csv import GestorCSV
from modelos import Cliente, Producto, Proveedor


MAPA_CATEGORIAS = {
    "Health and beauty": "Salud y belleza",
    "Electronic accessories": "Accesorios electrónicos",
    "Home and lifestyle": "Hogar y estilo de vida",
    "Sports and travel": "Deportes y viajes",
    "Food and beverages": "Alimentos y bebidas",
    "Fashion accessories": "Accesorios de moda",
}

MAPA_PAGOS = {
    "Cash": "Efectivo",
    "Credit card": "Tarjeta",
    "Ewallet": "Billetera electrónica",
}


def inicializar_datos(gestor: GestorCSV) -> None:
    gestor.crear_archivos()
    _crear_proveedores(gestor)
    _crear_productos(gestor)
    _crear_consumidor_final(gestor)

    historico = gestor.carpeta_datos / "historico_supermarket.csv"
    if gestor.esta_vacio("ventas") and historico.exists():
        importar_historico(gestor, historico)


def _crear_proveedores(gestor: GestorCSV) -> None:
    if not gestor.esta_vacio("proveedores"):
        return
    proveedores = [
        Proveedor("PR001", "Distribuidora Andina", "0991111111", "ventas@andina.ec"),
        Proveedor("PR002", "Comercial Nova", "0992222222", "pedidos@nova.ec"),
        Proveedor("PR003", "Abastecimientos Centro", "0993333333", "contacto@centro.ec"),
    ]
    gestor.agregar_varias("proveedores", [p.to_dict() for p in proveedores])


def _crear_productos(gestor: GestorCSV) -> None:
    if not gestor.esta_vacio("productos"):
        return
    productos = [
        Producto("P001", "Cuidado personal", "Salud y belleza", 18.50, 13.20, 45, 12, "PR001"),
        Producto("P002", "Audífonos básicos", "Accesorios electrónicos", 24.90, 18.00, 38, 10, "PR002"),
        Producto("P003", "Organizador para hogar", "Hogar y estilo de vida", 16.75, 11.60, 42, 12, "PR003"),
        Producto("P004", "Botella deportiva", "Deportes y viajes", 12.50, 8.50, 35, 10, "PR001"),
        Producto("P005", "Bebida y snack", "Alimentos y bebidas", 6.25, 4.10, 60, 15, "PR002"),
        Producto("P006", "Accesorio de moda", "Accesorios de moda", 14.80, 9.90, 40, 10, "PR003"),
    ]
    gestor.agregar_varias("productos", [p.to_dict() for p in productos])


def _crear_consumidor_final(gestor: GestorCSV) -> None:
    if gestor.buscar("clientes", "id_cliente", CONSUMIDOR_FINAL_ID):
        return
    cliente = Cliente(
        CONSUMIDOR_FINAL_ID,
        "Consumidor final",
        "No especificado",
        "Normal",
        datetime.now().strftime("%Y-%m-%d"),
    )
    gestor.agregar("clientes", cliente.to_dict())


def _convertir_fecha(fecha: str, hora: str) -> datetime:
    texto = f"{fecha.strip()} {hora.strip()}"
    formatos = (
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %I:%M %p",
    )
    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    raise ValueError(f"Fecha u hora inválida en el histórico: {texto}")


def importar_historico(gestor: GestorCSV, ruta: str | Path, cantidad_clientes: int = 120) -> None:
    """Transforma el CSV entregado en datos de simulación para QuickMarket.

    Los IDs de clientes son simulados porque el archivo original no los incluye.
    Las fechas se desplazan conservando los intervalos del histórico.
    """
    ruta = Path(ruta)
    with ruta.open("r", newline="", encoding="utf-8-sig") as archivo:
        filas = list(csv.DictReader(archivo))

    if not filas:
        return

    columnas_requeridas = {
        "Invoice ID", "Customer type", "Gender", "Product line", "Unit price",
        "Quantity", "Tax 5%", "Sales", "Date", "Time", "Payment", "cogs"
    }
    faltantes = columnas_requeridas.difference(filas[0].keys())
    if faltantes:
        raise ValueError(f"El histórico no contiene: {sorted(faltantes)}")

    fechas_originales = [_convertir_fecha(fila["Date"], fila["Time"]) for fila in filas]
    fecha_maxima = max(fechas_originales)
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    desplazamiento = hoy - fecha_maxima.replace(hour=0, minute=0, second=0, microsecond=0)
    fechas_simuladas = [fecha + desplazamiento for fecha in fechas_originales]

    clientes_existentes = {fila["id_cliente"] for fila in gestor.leer("clientes")}
    perfiles: dict[str, tuple[str, str]] = {}
    for indice, fila in enumerate(filas):
        id_cliente = f"C{(indice % cantidad_clientes) + 1:03d}"
        perfiles.setdefault(
            id_cliente,
            (
                "Miembro" if fila["Customer type"].strip().lower() == "member" else "Normal",
                "Femenino" if fila["Gender"].strip().lower() == "female" else "Masculino",
            ),
        )

    primera_fecha = min(fechas_simuladas).strftime("%Y-%m-%d")
    for id_cliente, (tipo, genero) in perfiles.items():
        if id_cliente not in clientes_existentes:
            gestor.agregar(
                "clientes",
                Cliente(id_cliente, f"Cliente {id_cliente[1:]}", genero, tipo, primera_fecha).to_dict(),
            )

    productos_por_categoria = {
        fila["categoria"]: fila["id_producto"] for fila in gestor.leer("productos")
    }

    ventas: list[dict[str, object]] = []
    detalles: list[dict[str, object]] = []
    movimientos: list[dict[str, object]] = []

    for indice, fila in enumerate(filas):
        consecutivo = indice + 1
        id_venta = f"V{consecutivo:06d}"
        id_detalle = f"DV{consecutivo:06d}"
        id_movimiento = f"M{consecutivo:06d}"
        id_cliente = f"C{(indice % cantidad_clientes) + 1:03d}"
        categoria = MAPA_CATEGORIAS.get(fila["Product line"], fila["Product line"])
        id_producto = productos_por_categoria.get(categoria, "P001")
        fecha = fechas_simuladas[indice].strftime("%Y-%m-%d %H:%M:%S")
        subtotal = round(float(fila["cogs"]), 2)
        impuesto = round(float(fila["Tax 5%"]), 2)
        total = round(float(fila["Sales"]), 2)
        metodo = MAPA_PAGOS.get(fila["Payment"], fila["Payment"])

        ventas.append({
            "id_venta": id_venta,
            "fecha": fecha,
            "id_cliente": id_cliente,
            "metodo_pago": metodo,
            "subtotal": f"{subtotal:.2f}",
            "impuesto": f"{impuesto:.2f}",
            "total": f"{total:.2f}",
        })
        detalles.append({
            "id_detalle": id_detalle,
            "id_venta": id_venta,
            "id_producto": id_producto,
            "cantidad": int(float(fila["Quantity"])),
            "precio_unitario": f"{float(fila['Unit price']):.2f}",
            "subtotal": f"{subtotal:.2f}",
        })
        movimientos.append({
            "id_movimiento": id_movimiento,
            "fecha": fecha,
            "tipo": "Ingreso",
            "concepto": f"Venta histórica {id_venta}",
            "monto": f"{total:.2f}",
            "id_venta": id_venta,
        })

    gestor.agregar_varias("ventas", ventas)
    gestor.agregar_varias("detalle_ventas", detalles)
    gestor.agregar_varias("movimientos_financieros", movimientos)
