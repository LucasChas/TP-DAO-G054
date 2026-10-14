"""Consulta de disponibilidad de un libro en la red."""
from dataclasses import dataclass

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import EjemplarDAO, LibroDAO
from biblioteca.modelos.enumeraciones import EstadoEjemplar
from biblioteca.patrones.iterador_catalogo import CatalogoEjemplares
from biblioteca.servicios.servicio_catalogo import obtener_libro_o_error


@dataclass
class DisponibilidadEnSede:
    """Resumen de los ejemplares de un libro que tiene una sede."""

    id_sede: int
    sede: str
    sede_activa: bool
    total: int = 0
    disponibles: int = 0
    reservados: int = 0
    prestados: int = 0
    en_transito: int = 0


class ServicioDisponibilidad:
    def consultar_disponibilidad(self, id_libro):
        """Devuelve, para cada sede que tiene ejemplares del libro, cuántos hay en cada estado.

        Los ejemplares dados de baja o extraviados no cuentan, porque ya no
        forman parte del inventario.
        """
        with obtener_sesion() as sesion:
            libro = obtener_libro_o_error(LibroDAO(sesion), id_libro)
            catalogo = CatalogoEjemplares(EjemplarDAO(sesion).listar(id_libro=libro.id))

        por_sede = {}
        for ejemplar in catalogo.en_circulacion():
            if ejemplar.sede_id not in por_sede:
                por_sede[ejemplar.sede_id] = DisponibilidadEnSede(
                    ejemplar.sede_id, ejemplar.sede.nombre, ejemplar.sede.esta_activa
                )
            resumen = por_sede[ejemplar.sede_id]
            resumen.total += 1
            if ejemplar.estado == EstadoEjemplar.DISPONIBLE:
                resumen.disponibles += 1
            elif ejemplar.estado == EstadoEjemplar.RESERVADO:
                resumen.reservados += 1
            elif ejemplar.estado == EstadoEjemplar.PRESTADO:
                resumen.prestados += 1
            elif ejemplar.estado == EstadoEjemplar.EN_TRANSITO:
                resumen.en_transito += 1
        return sorted(por_sede.values(), key=lambda r: r.sede)

    def ejemplares_disponibles(self, id_libro=None, id_sede=None):
        """Lista los ejemplares que se pueden prestar ahora, filtrados por libro y/o sede."""
        with obtener_sesion() as sesion:
            catalogo = CatalogoEjemplares(EjemplarDAO(sesion).listar(id_libro=id_libro))
        return list(catalogo.disponibles(id_sede))
