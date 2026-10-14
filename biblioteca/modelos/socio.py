"""Modelo de socio de la red de bibliotecas."""
from datetime import date

from sqlalchemy import Column, Date, Enum, Integer, String
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import EstadoSocio


class Socio(Base):
    """Persona que puede retirar material. El DNI no se puede repetir."""

    __tablename__ = "socios"

    id = Column(Integer, primary_key=True)
    dni = Column(String(15), nullable=False, unique=True)
    nombre = Column(String(60), nullable=False)
    apellido = Column(String(60), nullable=False)
    email = Column(String(100))
    telefono = Column(String(30))
    fecha_alta = Column(Date, nullable=False, default=date.today)
    estado = Column(Enum(EstadoSocio, native_enum=False, length=20), nullable=False, default=EstadoSocio.HABILITADO)
    motivo_inhabilitacion = Column(String(200))

    prestamos = relationship("Prestamo", back_populates="socio")
    reservas = relationship("Reserva", back_populates="socio")

    @property
    def esta_habilitado(self):
        return self.estado == EstadoSocio.HABILITADO

    @property
    def nombre_completo(self):
        return f"{self.apellido}, {self.nombre}"

    def __repr__(self):
        return f"<Socio {self.id}: {self.dni} {self.nombre_completo}>"

    def __str__(self):
        return f"{self.nombre_completo} (DNI {self.dni})"
