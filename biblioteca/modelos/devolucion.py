"""Modelo de devolución de un préstamo."""
from datetime import date

from sqlalchemy import Boolean, Column, Date, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import EstadoFisico


class Devolucion(Base):
    """Cierre de un préstamo: estado físico del material devuelto, atraso y multa."""

    __tablename__ = "devoluciones"

    id = Column(Integer, primary_key=True)
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=False, unique=True)
    fecha = Column(Date, nullable=False, default=date.today)
    estado_fisico = Column(Enum(EstadoFisico, native_enum=False, length=20), nullable=False)
    dias_atraso = Column(Integer, nullable=False, default=0)
    monto_multa = Column(Float, nullable=False, default=0.0)
    multa_pagada = Column(Boolean, nullable=False, default=False)
    observaciones = Column(Text)

    # Se carga junto con la devolución para poder mostrarla después de cerrar la sesión.
    prestamo = relationship("Prestamo", back_populates="devolucion", lazy="joined")

    @property
    def tiene_multa_impaga(self):
        return self.monto_multa > 0 and not self.multa_pagada

    def __repr__(self):
        return f"<Devolucion {self.id}: préstamo {self.prestamo_id}, multa {self.monto_multa}>"
