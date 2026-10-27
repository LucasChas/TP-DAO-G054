"""Acceso a datos de socios."""
from biblioteca.modelos import Socio


class SocioDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, socio):
        self.sesion.add(socio)
        self.sesion.flush()
        return socio

    def actualizar(self, socio):
        self.sesion.flush()
        return socio

    def obtener_por_id(self, id_socio):
        return self.sesion.get(Socio, id_socio)

    def obtener_por_dni(self, dni):
        return self.sesion.query(Socio).filter_by(dni=dni).first()

    def listar(self):
        return self.sesion.query(Socio).order_by(Socio.apellido, Socio.nombre).all()
