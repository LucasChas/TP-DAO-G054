"""Acceso a datos de préstamos."""
from biblioteca.modelos import Prestamo
from biblioteca.modelos.enumeraciones import EstadoPrestamo


class PrestamoDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, prestamo):
        self.sesion.add(prestamo)
        self.sesion.flush()
        return prestamo

    def actualizar(self, prestamo):
        self.sesion.flush()
        return prestamo

    def obtener_por_id(self, id_prestamo):
        return self.sesion.get(Prestamo, id_prestamo)

    def listar(self, estados=None):
        """Lista préstamos, opcionalmente solo los que están en alguno de los estados indicados."""
        consulta = self.sesion.query(Prestamo)
        if estados:
            consulta = consulta.filter(Prestamo.estado.in_(estados))
        return consulta.order_by(Prestamo.id).all()

    def listar_por_socio(self, id_socio):
        return self.sesion.query(Prestamo).filter_by(socio_id=id_socio).order_by(Prestamo.id).all()

    def listar_vencidos_al(self, fecha):
        return (
            self.sesion.query(Prestamo)
            .filter(Prestamo.estado == EstadoPrestamo.ACTIVO, Prestamo.fecha_vencimiento < fecha)
            .order_by(Prestamo.fecha_vencimiento)
            .all()
        )

    def socio_tiene_vencidos(self, id_socio, fecha):
        return (
            self.sesion.query(Prestamo)
            .filter(
                Prestamo.socio_id == id_socio,
                Prestamo.estado == EstadoPrestamo.ACTIVO,
                Prestamo.fecha_vencimiento < fecha,
            )
            .count()
            > 0
        )
