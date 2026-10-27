"""Acceso a datos de devoluciones y multas."""
from biblioteca.modelos import Devolucion, Prestamo


class DevolucionDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, devolucion):
        self.sesion.add(devolucion)
        self.sesion.flush()
        return devolucion

    def actualizar(self, devolucion):
        self.sesion.flush()
        return devolucion

    def obtener_por_id(self, id_devolucion):
        return self.sesion.get(Devolucion, id_devolucion)

    def listar(self):
        return self.sesion.query(Devolucion).order_by(Devolucion.fecha, Devolucion.id).all()

    def listar_con_multa(self):
        """Devoluciones que generaron una multa, pagada o no."""
        return self.sesion.query(Devolucion).filter(Devolucion.monto_multa > 0).order_by(Devolucion.id).all()

    def listar_multas_impagas(self, id_socio=None):
        consulta = (
            self.sesion.query(Devolucion)
            .join(Devolucion.prestamo)
            .filter(Devolucion.monto_multa > 0, Devolucion.multa_pagada.is_(False))
        )
        if id_socio is not None:
            consulta = consulta.filter(Prestamo.socio_id == id_socio)
        return consulta.order_by(Devolucion.fecha, Devolucion.id).all()

    def socio_tiene_multas_impagas(self, id_socio):
        return len(self.listar_multas_impagas(id_socio)) > 0
