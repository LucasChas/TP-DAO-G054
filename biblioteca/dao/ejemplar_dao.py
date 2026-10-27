"""Acceso a datos de ejemplares físicos."""
from biblioteca.modelos import Ejemplar


class EjemplarDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, ejemplar):
        self.sesion.add(ejemplar)
        self.sesion.flush()
        return ejemplar

    def actualizar(self, ejemplar):
        self.sesion.flush()
        return ejemplar

    def obtener_por_id(self, id_ejemplar):
        return self.sesion.get(Ejemplar, id_ejemplar)

    def obtener_por_codigo(self, codigo_inventario):
        return self.sesion.query(Ejemplar).filter_by(codigo_inventario=codigo_inventario).first()

    def listar(self, id_libro=None, id_sede=None):
        """Lista ejemplares, opcionalmente filtrados por libro y/o sede."""
        consulta = self.sesion.query(Ejemplar)
        if id_libro is not None:
            consulta = consulta.filter_by(libro_id=id_libro)
        if id_sede is not None:
            consulta = consulta.filter_by(sede_id=id_sede)
        return consulta.order_by(Ejemplar.codigo_inventario).all()
