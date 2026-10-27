"""Acceso a datos de libros del catálogo."""
from sqlalchemy import or_

from biblioteca.modelos import Libro


class LibroDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, libro):
        self.sesion.add(libro)
        self.sesion.flush()
        return libro

    def actualizar(self, libro):
        self.sesion.flush()
        return libro

    def obtener_por_id(self, id_libro):
        return self.sesion.get(Libro, id_libro)

    def obtener_por_isbn(self, isbn):
        return self.sesion.query(Libro).filter_by(isbn=isbn).first()

    def listar(self):
        return self.sesion.query(Libro).order_by(Libro.titulo).all()

    def buscar(self, texto):
        """Busca libros cuyo título o autor contengan el texto indicado."""
        patron = f"%{texto}%"
        return (
            self.sesion.query(Libro)
            .filter(or_(Libro.titulo.ilike(patron), Libro.autor.ilike(patron)))
            .order_by(Libro.titulo)
            .all()
        )
