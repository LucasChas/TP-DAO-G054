"""Modelo de ejemplar físico de un libro."""
from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import EstadoEjemplar, EstadoFisico


class Ejemplar(Base):
    """Copia física de un libro. Pertenece siempre a la misma sede, aunque viaje a otra."""

    __tablename__ = "ejemplares"

    id = Column(Integer, primary_key=True)
    codigo_inventario = Column(String(30), nullable=False, unique=True)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    estado = Column(Enum(EstadoEjemplar, native_enum=False, length=20), nullable=False, default=EstadoEjemplar.DISPONIBLE)
    estado_fisico = Column(Enum(EstadoFisico, native_enum=False, length=20), nullable=False, default=EstadoFisico.BUENO)

    libro = relationship("Libro", back_populates="ejemplares")
    sede = relationship("Sede", back_populates="ejemplares")
    prestamos = relationship("Prestamo", back_populates="ejemplar")

    @property
    def esta_disponible(self):
        return self.estado == EstadoEjemplar.DISPONIBLE

    def __repr__(self):
        return f"<Ejemplar {self.id}: {self.codigo_inventario} ({self.estado.name})>"

    def __str__(self):
        return f"{self.codigo_inventario} - {self.libro.titulo}"
