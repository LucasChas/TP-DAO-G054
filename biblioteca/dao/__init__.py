"""Objetos de acceso a datos: una clase por entidad principal.

Los DAO reciben la sesión abierta por el servicio, de modo que todas las
operaciones de un caso de uso se confirman o se deshacen juntas.
"""
from biblioteca.dao.ejemplar_dao import EjemplarDAO
from biblioteca.dao.libro_dao import LibroDAO
from biblioteca.dao.prestamo_dao import PrestamoDAO
from biblioteca.dao.reserva_dao import ReservaDAO
from biblioteca.dao.sede_dao import SedeDAO
from biblioteca.dao.socio_dao import SocioDAO

__all__ = ["EjemplarDAO", "LibroDAO", "PrestamoDAO", "ReservaDAO", "SedeDAO", "SocioDAO"]
