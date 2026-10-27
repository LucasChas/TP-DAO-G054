"""Modelo de sede de la red de bibliotecas."""
from sqlalchemy import Column, Date, Enum, Integer, String
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import EstadoSede


class Sede(Base):
    """Biblioteca que forma parte de la red. La baja es lógica para conservar su historial."""

    __tablename__ = "sedes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    direccion = Column(String(150), nullable=False)
    telefono = Column(String(30))
    email = Column(String(100))
    horario_atencion = Column(String(100))
    estado = Column(Enum(EstadoSede, native_enum=False, length=20), nullable=False, default=EstadoSede.ACTIVA)
    fecha_baja = Column(Date)

    ejemplares = relationship("Ejemplar", back_populates="sede")

    @property
    def esta_activa(self):
        return self.estado == EstadoSede.ACTIVA

    def __repr__(self):
        return f"<Sede {self.id}: {self.nombre} ({self.estado.name})>"

    def __str__(self):
        return self.nombre
