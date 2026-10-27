"""Modelo de parámetros de configuración del sistema."""
from sqlalchemy import Column, String

from biblioteca.configuracion.base_de_datos import Base


class Configuracion(Base):
    """Un parámetro que tiene que sobrevivir a un reinicio, por ejemplo la política de multas vigente."""

    __tablename__ = "configuracion"

    clave = Column(String(50), primary_key=True)
    valor = Column(String(200), nullable=False)

    def __repr__(self):
        return f"<Configuracion {self.clave}={self.valor}>"
