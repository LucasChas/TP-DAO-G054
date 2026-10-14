"""Acceso a datos de reservas."""
from biblioteca.modelos import Reserva
from biblioteca.modelos.enumeraciones import EstadoReserva

ESTADOS_ACTIVOS = (EstadoReserva.PENDIENTE, EstadoReserva.DISPONIBLE)


class ReservaDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, reserva):
        self.sesion.add(reserva)
        self.sesion.flush()
        return reserva

    def actualizar(self, reserva):
        self.sesion.flush()
        return reserva

    def obtener_por_id(self, id_reserva):
        return self.sesion.get(Reserva, id_reserva)

    def listar(self, solo_activas=False):
        consulta = self.sesion.query(Reserva)
        if solo_activas:
            consulta = consulta.filter(Reserva.estado.in_(ESTADOS_ACTIVOS))
        return consulta.order_by(Reserva.fecha_reserva, Reserva.id).all()

    def obtener_activa(self, id_socio, id_libro):
        """Devuelve la reserva pendiente o disponible del socio para ese libro, si existe."""
        return (
            self.sesion.query(Reserva)
            .filter(Reserva.socio_id == id_socio, Reserva.libro_id == id_libro, Reserva.estado.in_(ESTADOS_ACTIVOS))
            .first()
        )

    def primera_pendiente(self, id_libro, id_sede):
        """La reserva pendiente más antigua de ese libro en esa sede (orden de llegada)."""
        return (
            self.sesion.query(Reserva)
            .filter_by(libro_id=id_libro, sede_id=id_sede, estado=EstadoReserva.PENDIENTE)
            .order_by(Reserva.fecha_reserva, Reserva.id)
            .first()
        )

    def obtener_disponible_para(self, id_socio, id_ejemplar):
        """La reserva del socio que tiene apartado ese ejemplar, si existe."""
        return (
            self.sesion.query(Reserva)
            .filter_by(socio_id=id_socio, ejemplar_id=id_ejemplar, estado=EstadoReserva.DISPONIBLE)
            .first()
        )

    def listar_disponibles_vencidas(self, fecha):
        """Reservas con ejemplar apartado cuyo plazo de retiro ya pasó."""
        return (
            self.sesion.query(Reserva)
            .filter(Reserva.estado == EstadoReserva.DISPONIBLE, Reserva.fecha_limite_retiro < fecha)
            .order_by(Reserva.id)
            .all()
        )
