"""Acceso a datos de sedes."""
from sqlalchemy import func

from biblioteca.modelos import Sede
from biblioteca.modelos.enumeraciones import EstadoSede


class SedeDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, sede):
        self.sesion.add(sede)
        self.sesion.flush()
        return sede

    def actualizar(self, sede):
        self.sesion.flush()
        return sede

    def obtener_por_id(self, id_sede):
        return self.sesion.get(Sede, id_sede)

    def obtener_por_nombre(self, nombre):
        """Busca una sede por nombre sin distinguir mayúsculas de minúsculas."""
        return self.sesion.query(Sede).filter(func.lower(Sede.nombre) == nombre.lower()).first()

    def listar(self):
        return self.sesion.query(Sede).order_by(Sede.nombre).all()

    def listar_activas(self):
        return self.sesion.query(Sede).filter_by(estado=EstadoSede.ACTIVA).order_by(Sede.nombre).all()
