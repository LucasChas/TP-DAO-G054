"""Reporte 3: libros más solicitados para préstamos inter-sedes.

Cuenta todas las solicitudes interbibliotecarias (también las que después se
cancelaron, porque igual reflejan demanda) e informa cuántas se concretaron
con la entrega al socio. Empates: alfabéticamente por título.
"""
from dataclasses import dataclass
from datetime import date

from sqlalchemy import case, func

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.modelos import Ejemplar, Libro, Prestamo
from biblioteca.modelos.enumeraciones import EstadoPrestamo, TipoPrestamo

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
        consulta = (
            sesion.query(
                Libro.titulo,
                Libro.autor,
                func.count(Prestamo.id).label("solicitudes"),
                func.sum(case((Prestamo.estado.in_(ESTADOS_CONCRETADOS), 1), else_=0)).label("concretadas"),
                func.count(func.distinct(Prestamo.sede_destino_id)).label("sedes_destino"),
            )
            .join(Ejemplar, Ejemplar.libro_id == Libro.id)
            .join(Prestamo, Prestamo.ejemplar_id == Ejemplar.id)
            .filter(Prestamo.tipo == TipoPrestamo.INTERBIBLIOTECARIO)
        )
        if desde is not None:
            consulta = consulta.filter(Prestamo.fecha_solicitud >= desde)
        if hasta is not None:
            consulta = consulta.filter(Prestamo.fecha_solicitud <= hasta)
        filas = (
            consulta.group_by(Libro.id)
            .order_by(func.count(Prestamo.id).desc(), Libro.titulo)
            .limit(limite)
            .all()
        )
    return [
        FilaLibroSolicitado(posicion, titulo, autor, solicitudes, concretadas or 0, sedes)
        for posicion, (titulo, autor, solicitudes, concretadas, sedes) in enumerate(filas, start=1)
    ]
