"""Acceso a datos de préstamos."""
from sqlalchemy import case, func, or_

from biblioteca.modelos import Ejemplar, Libro, Prestamo
from biblioteca.modelos.enumeraciones import EstadoPrestamo, TipoPrestamo

# Préstamos interbibliotecarios cuyo ejemplar ya salió de su sede o está por salir y todavía no volvió.
ESTADOS_FUERA_DE_SEDE = (EstadoPrestamo.EN_ENVIO, EstadoPrestamo.LISTO_PARA_RETIRO, EstadoPrestamo.ACTIVO)


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
            .order_by(Prestamo.fecha_vencimiento, Prestamo.id)
            .all()
        )

    def listar_por_vencimiento(self, estados):
        """Préstamos en alguno de los estados indicados, ordenados por fecha de vencimiento."""
        return (
            self.sesion.query(Prestamo)
            .filter(Prestamo.estado.in_(estados))
            .order_by(Prestamo.fecha_vencimiento, Prestamo.id)
            .all()
        )

    def hay_interbibliotecarios_fuera_de_sede(self, id_sede):
        """Indica si algún préstamo interbibliotecario con origen o destino en la sede tiene el
        ejemplar en viaje o en manos del socio, de modo que todavía le falta volver."""
        return (
            self.sesion.query(Prestamo)
            .filter(
                Prestamo.tipo == TipoPrestamo.INTERBIBLIOTECARIO,
                Prestamo.estado.in_(ESTADOS_FUERA_DE_SEDE),
                or_(Prestamo.sede_origen_id == id_sede, Prestamo.sede_destino_id == id_sede),
            )
            .count()
            > 0
        )

    def ranking_interbibliotecarios(self, estados_concretados, desde=None, hasta=None, limite=10):
        """Por libro: (título, autor, solicitudes interbibliotecarias, concretadas, sedes de destino distintas),
        de mayor a menor cantidad de solicitudes y, ante un empate, por título."""
        consulta = (
            self.sesion.query(
                Libro.titulo,
                Libro.autor,
                func.count(Prestamo.id).label("solicitudes"),
                func.sum(case((Prestamo.estado.in_(estados_concretados), 1), else_=0)).label("concretadas"),
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
        return (
            consulta.group_by(Libro.id)
            .order_by(func.count(Prestamo.id).desc(), Libro.titulo)
            .limit(limite)
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
