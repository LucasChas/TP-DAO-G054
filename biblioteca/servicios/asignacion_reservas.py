"""Asignación de ejemplares liberados a las reservas pendientes.

Está separado de servicio_reservas porque lo usan varios casos de uso
(cancelaciones, devoluciones, recepción de remitos, fin de reparación)
dentro de su propia sesión.
"""
from biblioteca.dao import ReservaDAO
from biblioteca.modelos.enumeraciones import EstadoEjemplar


def asignar_a_reserva_pendiente(sesion, ejemplar, fecha):
    """Si hay reservas pendientes del libro en la sede del ejemplar, aparta el
    ejemplar para la más antigua (orden de llegada).

    Devuelve la reserva asignada, o None si no había ninguna pendiente.
    """
    reserva = ReservaDAO(sesion).primera_pendiente(ejemplar.libro_id, ejemplar.sede_id)
    if reserva is None:
        return None
    reserva.asignar_ejemplar(ejemplar, fecha)
    ejemplar.estado = EstadoEjemplar.RESERVADO
    sesion.flush()
    return reserva


def liberar_ejemplar(sesion, ejemplar, fecha):
    """Deja el ejemplar disponible y, si corresponde, lo pasa a la siguiente reserva."""
    ejemplar.estado = EstadoEjemplar.DISPONIBLE
    return asignar_a_reserva_pendiente(sesion, ejemplar, fecha)
