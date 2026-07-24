"""Segmentación RFM de clientes sin librerías externas."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from config import CONSUMIDOR_FINAL_ID
from gestor_csv import GestorCSV


class AnalizadorRFM:
    def __init__(self, gestor: GestorCSV):
        self.gestor = gestor

    @staticmethod
    def _leer_fecha(valor: str) -> datetime:
        formatos = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d")
        for formato in formatos:
            try:
                return datetime.strptime(valor, formato)
            except ValueError:
                continue
        raise ValueError(f"Fecha inválida: {valor}")

    @staticmethod
    def _puntajes(valores: dict[str, float], inverso: bool = False) -> dict[str, int]:
        """Asigna puntajes de 1 a 5 según la posición relativa."""
        if not valores:
            return {}
        ordenados = sorted(valores.items(), key=lambda item: (item[1], item[0]))
        cantidad = len(ordenados)
        resultado: dict[str, int] = {}
        for posicion, (clave, _) in enumerate(ordenados):
            if cantidad == 1:
                puntaje = 3
            else:
                grupo = min(4, int(posicion * 5 / cantidad))
                puntaje = 5 - grupo if inverso else grupo + 1
            resultado[clave] = puntaje
        return resultado

    @staticmethod
    def _asignar_segmento(r: int, f: int, m: int) -> str:
        if r >= 4 and f >= 4 and m >= 4:
            return "VIP"
        if r >= 4 and f >= 3:
            return "Frecuente"
        if r >= 4 and f <= 2:
            return "Nuevo"
        if r <= 2 and f >= 3:
            return "En riesgo"
        if r <= 2:
            return "Recuperable"
        return "Regular"

    def calcular_rfm(self) -> list[dict[str, object]]:
        ventas = [
            fila for fila in self.gestor.leer("ventas")
            if fila.get("id_cliente") != CONSUMIDOR_FINAL_ID
        ]
        if not ventas:
            self.gestor.reemplazar("segmentos_rfm", [])
            return []

        datos: dict[str, dict[str, object]] = defaultdict(
            lambda: {"ultima_compra": None, "ventas": set(), "monetario": 0.0}
        )

        for venta in ventas:
            try:
                fecha = self._leer_fecha(venta["fecha"])
                total = float(venta.get("total", 0) or 0)
            except (ValueError, TypeError):
                continue
            cliente = venta["id_cliente"]
            registro = datos[cliente]
            ultima = registro["ultima_compra"]
            if ultima is None or fecha > ultima:
                registro["ultima_compra"] = fecha
            registro["ventas"].add(venta["id_venta"])
            registro["monetario"] = float(registro["monetario"]) + total

        fechas_validas = [d["ultima_compra"] for d in datos.values() if d["ultima_compra"]]
        if not fechas_validas:
            self.gestor.reemplazar("segmentos_rfm", [])
            return []
        fecha_referencia = max(fechas_validas) + timedelta(days=1)

        recencias: dict[str, float] = {}
        frecuencias: dict[str, float] = {}
        monetarios: dict[str, float] = {}
        for cliente, registro in datos.items():
            ultima = registro["ultima_compra"]
            recencias[cliente] = float((fecha_referencia.date() - ultima.date()).days)
            frecuencias[cliente] = float(len(registro["ventas"]))
            monetarios[cliente] = round(float(registro["monetario"]), 2)

        r_scores = self._puntajes(recencias, inverso=True)
        f_scores = self._puntajes(frecuencias)
        m_scores = self._puntajes(monetarios)

        resultados: list[dict[str, object]] = []
        for cliente in datos:
            r = r_scores[cliente]
            f = f_scores[cliente]
            m = m_scores[cliente]
            resultados.append({
                "id_cliente": cliente,
                "recencia": int(recencias[cliente]),
                "frecuencia": int(frecuencias[cliente]),
                "monetario": f"{monetarios[cliente]:.2f}",
                "r_score": r,
                "f_score": f,
                "m_score": m,
                "segmento": self._asignar_segmento(r, f, m),
            })

        resultados.sort(key=lambda fila: (str(fila["segmento"]), -float(fila["monetario"])))
        self.gestor.reemplazar("segmentos_rfm", resultados)
        return resultados

    def obtener_resumen(self) -> list[dict[str, object]]:
        conteo: dict[str, int] = defaultdict(int)
        for fila in self.calcular_rfm():
            conteo[str(fila["segmento"])] += 1
        return [
            {"segmento": segmento, "clientes": clientes}
            for segmento, clientes in sorted(conteo.items(), key=lambda item: (-item[1], item[0]))
        ]
