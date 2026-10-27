"""Modelos del dominio. Importarlos acá registra todas las tablas en Base."""
from biblioteca.modelos.configuracion import Configuracion
from biblioteca.modelos.devolucion import Devolucion
from biblioteca.modelos.ejemplar import Ejemplar
from biblioteca.modelos.libro import Libro
from biblioteca.modelos.prestamo import Prestamo
from biblioteca.modelos.remito import MovimientoRemito, Remito
from biblioteca.modelos.reserva import Reserva
from biblioteca.modelos.sede import Sede
from biblioteca.modelos.socio import Socio

__all__ = [
    "Configuracion",
    "Devolucion",
    "Ejemplar",
    "Libro",
    "MovimientoRemito",
    "Prestamo",
    "Remito",
    "Reserva",
    "Sede",
    "Socio",
]
