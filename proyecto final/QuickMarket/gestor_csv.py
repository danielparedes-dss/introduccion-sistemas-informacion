"""Persistencia de QuickMarket mediante archivos CSV."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Iterable

from config import CARPETA_DATOS


class GestorCSV:
    ENCABEZADOS = {
        "clientes": [
            "id_cliente", "nombre", "genero", "tipo_cliente", "fecha_registro"
        ],
        "proveedores": [
            "id_proveedor", "nombre", "telefono", "correo", "estado"
        ],
        "productos": [
            "id_producto", "nombre", "categoria", "precio_venta",
            "costo_unitario", "stock_actual", "stock_minimo", "id_proveedor"
        ],
        "ventas": [
            "id_venta", "fecha", "id_cliente", "metodo_pago",
            "subtotal", "impuesto", "total"
        ],
        "detalle_ventas": [
            "id_detalle", "id_venta", "id_producto", "cantidad",
            "precio_unitario", "subtotal"
        ],
        "movimientos_financieros": [
            "id_movimiento", "fecha", "tipo", "concepto", "monto", "id_venta"
        ],
        "ordenes_compra": [
            "id_orden", "fecha", "id_proveedor", "estado", "total_estimado"
        ],
        "detalle_ordenes_compra": [
            "id_detalle_orden", "id_orden", "id_producto", "cantidad",
            "costo_unitario", "subtotal"
        ],
        "segmentos_rfm": [
            "id_cliente", "recencia", "frecuencia", "monetario",
            "r_score", "f_score", "m_score", "segmento"
        ],
    }

    def __init__(self, carpeta_datos: str | Path = CARPETA_DATOS):
        self.carpeta_datos = Path(carpeta_datos)
        self.rutas = {
            nombre: self.carpeta_datos / f"{nombre}.csv"
            for nombre in self.ENCABEZADOS
        }

    def crear_archivos(self) -> None:
        self.carpeta_datos.mkdir(parents=True, exist_ok=True)
        for nombre, encabezados in self.ENCABEZADOS.items():
            ruta = self.rutas[nombre]
            if not ruta.exists():
                with ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
                    csv.DictWriter(archivo, fieldnames=encabezados).writeheader()

    def leer(self, nombre: str) -> list[dict[str, str]]:
        self._validar_nombre(nombre)
        ruta = self.rutas[nombre]
        if not ruta.exists():
            self.crear_archivos()
        with ruta.open("r", newline="", encoding="utf-8-sig") as archivo:
            return list(csv.DictReader(archivo))

    def agregar(self, nombre: str, fila: dict[str, Any]) -> None:
        self._validar_nombre(nombre)
        encabezados = self.ENCABEZADOS[nombre]
        faltantes = [campo for campo in encabezados if campo not in fila]
        if faltantes:
            raise ValueError(f"Faltan campos en {nombre}: {', '.join(faltantes)}")
        with self.rutas[nombre].open("a", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=encabezados)
            escritor.writerow({campo: fila[campo] for campo in encabezados})

    def agregar_varias(self, nombre: str, filas: Iterable[dict[str, Any]]) -> None:
        for fila in filas:
            self.agregar(nombre, fila)

    def reemplazar(self, nombre: str, filas: Iterable[dict[str, Any]]) -> None:
        self._validar_nombre(nombre)
        encabezados = self.ENCABEZADOS[nombre]
        ruta_temporal = self.rutas[nombre].with_suffix(".tmp")
        with ruta_temporal.open("w", newline="", encoding="utf-8-sig") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=encabezados)
            escritor.writeheader()
            for fila in filas:
                escritor.writerow({campo: fila.get(campo, "") for campo in encabezados})
        ruta_temporal.replace(self.rutas[nombre])

    def esta_vacio(self, nombre: str) -> bool:
        return len(self.leer(nombre)) == 0

    def generar_id(
        self,
        nombre: str,
        campo_id: str,
        prefijo: str,
        ancho: int = 6,
    ) -> str:
        mayor = 0
        for fila in self.leer(nombre):
            valor = fila.get(campo_id, "")
            coincidencia = re.search(r"(\d+)$", valor)
            if coincidencia:
                mayor = max(mayor, int(coincidencia.group(1)))
        return f"{prefijo}{mayor + 1:0{ancho}d}"

    def buscar(self, nombre: str, campo: str, valor: str) -> dict[str, str] | None:
        for fila in self.leer(nombre):
            if fila.get(campo) == valor:
                return fila
        return None

    def actualizar_fila(
        self,
        nombre: str,
        campo_clave: str,
        valor_clave: str,
        cambios: dict[str, Any],
    ) -> bool:
        filas = self.leer(nombre)
        encontrado = False
        for fila in filas:
            if fila.get(campo_clave) == valor_clave:
                fila.update({k: str(v) for k, v in cambios.items()})
                encontrado = True
                break
        if encontrado:
            self.reemplazar(nombre, filas)
        return encontrado

    def _validar_nombre(self, nombre: str) -> None:
        if nombre not in self.ENCABEZADOS:
            raise KeyError(f"No existe la colección CSV: {nombre}")
