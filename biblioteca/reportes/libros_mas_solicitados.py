"""Reporte 3: libros más solicitados para préstamos inter-sedes.

Cuenta todas las solicitudes interbibliotecarias (también las que después se
cancelaron, porque igual reflejan demanda) e informa cuántas se concretaron
con la entrega al socio. Empates: alfabéticamente por título.
"""
from dataclasses import dataclass
from datetime import date

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import PrestamoDAO
from biblioteca.modelos.enumeraciones import EstadoPrestamo

ESTADOS_CONCRETADOS = [EstadoPrestamo.ACTIVO, EstadoPrestamo.DEVUELTO]


@dataclass
class FilaLibroSolicitado:
    posicion: int
    titulo: str
    autor: str
    solicitudes: int
    concretadas: int
    sedes_destino: int


def generar(desde=None, hasta=None, limite=10):
    """desde y hasta (inclusive) filtran por fecha de solicitud; ambos son opcionales."""
    with obtener_sesion() as sesion:
        filas = PrestamoDAO(sesion).ranking_interbibliotecarios(ESTADOS_CONCRETADOS, desde, hasta, limite)
    return [
        FilaLibroSolicitado(posicion, titulo, autor, solicitudes, concretadas or 0, sedes)
        for posicion, (titulo, autor, solicitudes, concretadas, sedes) in enumerate(filas, start=1)
    ]
