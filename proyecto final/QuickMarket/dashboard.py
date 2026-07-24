"""Dashboard gerencial con Tkinter y biblioteca estándar."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from analisis_rfm import AnalizadorRFM
from gestor_csv import GestorCSV

# Paleta de colores usada en los gráficos del dashboard para que no se vean
# monocromáticos. Se recorre en orden y se repite si hay más barras que colores.
PALETA_BARRAS = [
    "#4f86c6", "#f2994a", "#27ae60", "#eb5757",
    "#9b51e0", "#2d9cdb", "#f2c94c", "#56ccf2",
]
# Color de fondo suave para cada uno de los cuatro paneles del dashboard.
COLORES_PANEL = ["#eaf2fd", "#f6edfb", "#eafaf1", "#fdeeee"]
# Colores fijos para el estado del inventario (con significado semántico).
COLORES_INVENTARIO = {"Normal": "#27ae60", "Stock bajo": "#f2994a", "Agotado": "#eb5757"}


class Dashboard:
    def __init__(self, gestor: GestorCSV):
        self.gestor = gestor
        self.analizador_rfm = AnalizadorRFM(gestor)

    @staticmethod
    def _fecha(valor: str) -> datetime | None:
        for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(valor, formato)
            except ValueError:
                continue
        return None

    def calcular_kpis(self) -> dict[str, float | int]:
        ventas = self.gestor.leer("ventas")
        productos = self.gestor.leer("productos")
        totales = []
        ids = set()
        for venta in ventas:
            try:
                totales.append(float(venta.get("total", 0) or 0))
                ids.add(venta.get("id_venta", ""))
            except ValueError:
                continue
        stock_bajo = 0
        for producto in productos:
            try:
                if int(float(producto["stock_actual"])) <= int(float(producto["stock_minimo"])):
                    stock_bajo += 1
            except (ValueError, KeyError):
                continue
        numero = len(ids)
        return {
            "ventas_totales": round(sum(totales), 2),
            "numero_ventas": numero,
            "ticket_promedio": round(sum(totales) / numero, 2) if numero else 0.0,
            "stock_bajo": stock_bajo,
        }

    def obtener_datos_graficos(self) -> dict[str, Any]:
        ventas_diarias: dict[str, float] = defaultdict(float)
        for venta in self.gestor.leer("ventas"):
            fecha = self._fecha(venta.get("fecha", ""))
            if fecha is None:
                continue
            try:
                ventas_diarias[fecha.strftime("%Y-%m-%d")] += float(venta.get("total", 0) or 0)
            except ValueError:
                continue
        ventas_ordenadas = sorted(ventas_diarias.items())[-30:]

        segmentos = [
            (str(fila["segmento"]), int(fila["clientes"]))
            for fila in self.analizador_rfm.obtener_resumen()
        ]

        nombres = {
            fila["id_producto"]: fila["nombre"] for fila in self.gestor.leer("productos")
        }
        cantidades: dict[str, int] = defaultdict(int)
        for detalle in self.gestor.leer("detalle_ventas"):
            try:
                cantidades[nombres.get(detalle["id_producto"], detalle["id_producto"])] += int(
                    float(detalle.get("cantidad", 0) or 0)
                )
            except ValueError:
                continue
        productos_top = sorted(cantidades.items(), key=lambda item: item[1], reverse=True)[:6]

        estados = {"Normal": 0, "Stock bajo": 0, "Agotado": 0}
        for producto in self.gestor.leer("productos"):
            try:
                actual = int(float(producto["stock_actual"]))
                minimo = int(float(producto["stock_minimo"]))
            except (ValueError, KeyError):
                continue
            if actual == 0:
                estados["Agotado"] += 1
            elif actual <= minimo:
                estados["Stock bajo"] += 1
            else:
                estados["Normal"] += 1

        return {
            "ventas_diarias": ventas_ordenadas,
            "segmentos": segmentos,
            "productos_top": productos_top,
            "inventario": list(estados.items()),
        }

    def dibujar_en_canvas(self, canvas) -> None:
        """Dibuja cuatro gráficos sencillos sobre un Canvas de Tkinter."""
        canvas.delete("all")
        canvas.update_idletasks()
        canvas.configure(background="#f4f6fa")
        ancho = max(canvas.winfo_width(), 900)
        alto = max(canvas.winfo_height(), 500)
        margen = 18
        separacion = 18
        ancho_panel = (ancho - 2 * margen - separacion) / 2
        alto_panel = (alto - 2 * margen - separacion) / 2
        datos = self.obtener_datos_graficos()

        paneles = [
            (margen, margen, margen + ancho_panel, margen + alto_panel),
            (margen + ancho_panel + separacion, margen, ancho - margen, margen + alto_panel),
            (margen, margen + alto_panel + separacion, margen + ancho_panel, alto - margen),
            (margen + ancho_panel + separacion, margen + alto_panel + separacion, ancho - margen, alto - margen),
        ]
        for caja, color_fondo in zip(paneles, COLORES_PANEL):
            x1, y1, x2, y2 = caja
            canvas.create_rectangle(x1, y1, x2, y2, fill=color_fondo, outline="")

        self._lineas(
            canvas, paneles[0], "Evolución de ventas (30 días)", datos["ventas_diarias"],
            color_titulo="#1d4ed8", color_linea="#2563eb",
        )
        self._barras(canvas, paneles[1], "Segmentación RFM", datos["segmentos"], color_titulo="#7c3aed")
        self._barras(canvas, paneles[2], "Productos más vendidos", datos["productos_top"], color_titulo="#15803d")
        self._barras(
            canvas, paneles[3], "Estado del inventario", datos["inventario"],
            color_titulo="#b91c1c", colores=COLORES_INVENTARIO,
        )

    @staticmethod
    def _marco(canvas, caja, titulo: str, color_titulo: str = "#333333"):
        x1, y1, x2, y2 = caja
        canvas.create_rectangle(x1, y1, x2, y2, outline="#c7cedb", width=1)
        canvas.create_text(
            (x1 + x2) / 2, y1 + 18, text=titulo, font=("Arial", 11, "bold"), fill=color_titulo
        )
        return x1 + 42, y1 + 42, x2 - 18, y2 - 42

    def _lineas(
        self, canvas, caja, titulo: str, datos: list[tuple[str, float]],
        color_titulo: str = "#333333", color_linea: str = "#2563eb",
    ) -> None:
        x1, y1, x2, y2 = self._marco(canvas, caja, titulo, color_titulo)
        if not datos:
            canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text="Sin datos")
            return
        maximo = max(valor for _, valor in datos) or 1
        canvas.create_line(x1, y2, x2, y2, fill="#8a93a3")
        canvas.create_line(x1, y1, x1, y2, fill="#8a93a3")
        puntos = []
        for indice, (_, valor) in enumerate(datos):
            px = x1 if len(datos) == 1 else x1 + indice * (x2 - x1) / (len(datos) - 1)
            py = y2 - (valor / maximo) * (y2 - y1)
            puntos.extend((px, py))
        if len(puntos) >= 4:
            area = [x1, y2, *puntos, x2, y2]
            canvas.create_polygon(*area, fill="#dbe8fb", outline="")
            canvas.create_line(*puntos, fill=color_linea, width=2, smooth=True)
        for px, py in zip(puntos[0::2], puntos[1::2]):
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill=color_linea, outline="white")
        canvas.create_text(x1, y1 - 8, text=f"${maximo:,.0f}", anchor="w", font=("Arial", 8))
        canvas.create_text(x1, y2 + 13, text=datos[0][0][5:], anchor="w", font=("Arial", 8))
        canvas.create_text(x2, y2 + 13, text=datos[-1][0][5:], anchor="e", font=("Arial", 8))

    def _barras(
        self, canvas, caja, titulo: str, datos: list[tuple[str, int]],
        color_titulo: str = "#333333", colores: dict[str, str] | None = None,
    ) -> None:
        x1, y1, x2, y2 = self._marco(canvas, caja, titulo, color_titulo)
        if not datos:
            canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text="Sin datos")
            return
        maximo = max(valor for _, valor in datos) or 1
        cantidad = len(datos)
        espacio = (x2 - x1) / max(cantidad, 1)
        ancho_barra = min(48, espacio * 0.62)
        for indice, (nombre, valor) in enumerate(datos):
            color = (colores or {}).get(nombre) or PALETA_BARRAS[indice % len(PALETA_BARRAS)]
            centro = x1 + espacio * (indice + 0.5)
            altura = (valor / maximo) * (y2 - y1)
            canvas.create_rectangle(
                centro - ancho_barra / 2,
                y2 - altura,
                centro + ancho_barra / 2,
                y2,
                fill=color,
                outline="",
            )
            canvas.create_text(centro, y2 - altura - 9, text=str(valor), font=("Arial", 8, "bold"))
            etiqueta = nombre if len(nombre) <= 14 else nombre[:12] + "…"
            canvas.create_text(centro, y2 + 15, text=etiqueta, font=("Arial", 8), angle=18)
