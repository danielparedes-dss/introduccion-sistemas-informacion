"""Punto de entrada del sistema QuickMarket."""

from gestor_csv import GestorCSV
from inicializador import inicializar_datos
from interfaz import InterfazQuickMarket
from sistema_ventas import SistemaVentas


def iniciar_programa() -> None:
    gestor = GestorCSV()
    inicializar_datos(gestor)
    sistema = SistemaVentas(gestor)
    aplicacion = InterfazQuickMarket(gestor, sistema)
    aplicacion.iniciar()


if __name__ == "__main__":
    iniciar_programa()
