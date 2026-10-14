"""Modelo de libro del catálogo."""
from sqlalchemy import Column, Enum, Integer, String
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import TipoMaterial


class Libro(Base):
    """Obra del catálogo, independiente de sus copias físicas. El ISBN no se puede repetir."""

    __tablename__ = "libros"

    id = Column(Integer, primary_key=True)
    isbn = Column(String(20), nullable=False, unique=True)
    titulo = Column(String(200), nullable=False)
    autor = Column(String(150), nullable=False)
    editorial = Column(String(100))
    anio_publicacion = Column(Integer)
    tipo_material = Column(Enum(TipoMaterial, native_enum=False, length=20), nullable=False, default=TipoMaterial.LIBRO)

    ejemplares = relationship("Ejemplar", back_populates="libro")
    reservas = relationship("Reserva", back_populates="libro")

    def __repr__(self):
        return f"<Libro {self.id}: {self.isbn} {self.titulo}>"

    def __str__(self):
        return f"{self.titulo} - {self.autor}"
