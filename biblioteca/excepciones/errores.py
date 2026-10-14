"""Excepciones propias del dominio.

Todas heredan de ErrorDeNegocio, así la interfaz puede capturarlas juntas y
mostrarle el mensaje al usuario sin cortar la ejecución.
"""


class ErrorDeNegocio(Exception):
    """Error base para cualquier regla de negocio que no se cumple."""


class DatoInvalido(ErrorDeNegocio):
    """Un dato ingresado no tiene el formato o el valor esperado."""


class EntidadNoEncontrada(ErrorDeNegocio):
    """No existe la entidad buscada."""


class EntidadDuplicada(ErrorDeNegocio):
    """Ya existe una entidad con el mismo identificador de negocio (DNI, ISBN, código)."""


class SedeDadaDeBaja(ErrorDeNegocio):
    """Se intentó operar con una sede que está dada de baja."""


class OperacionNoPermitida(ErrorDeNegocio):
    """La operación no se puede realizar en el estado actual de la entidad."""


class SocioInhabilitado(ErrorDeNegocio):
    """El socio está inhabilitado y no puede recibir préstamos ni hacer reservas."""


class SocioConPrestamosVencidos(ErrorDeNegocio):
    """El socio tiene préstamos vencidos sin devolver."""


class EjemplarNoDisponible(ErrorDeNegocio):
    """El ejemplar no está disponible para prestarse."""


class EjemplarDeOtraSede(ErrorDeNegocio):
    """El ejemplar no pertenece a la sede de origen del préstamo."""


class TransicionRemitoInvalida(ErrorDeNegocio):
    """La acción pedida no está permitida en el estado actual del remito; el estado no cambia."""


class SocioConMultasImpagas(ErrorDeNegocio):
    """El socio tiene multas sin pagar."""
