"""Modelo de reserva de un libro."""
from datetime import date

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import EstadoReserva


class Reserva(Base):
    """Pedido de un socio para retirar un libro en una sede cuando haya un ejemplar libre.

    La reserva es sobre el libro, no sobre un ejemplar puntual: cuando un
    ejemplar queda libre se asigna a la reserva pendiente más antigua.
    """

    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"))
    fecha_reserva = Column(Date, nullable=False, default=date.today)
    fecha_limite_retiro = Column(Date)
    estado = Column(Enum(EstadoReserva, native_enum=False, length=20), nullable=False, default=EstadoReserva.PENDIENTE)

    socio = relationship("Socio", back_populates="reservas")
    libro = relationship("Libro", back_populates="reservas")
    sede = relationship("Sede")
    ejemplar = relationship("Ejemplar")

    def __repr__(self):
        return f"<Reserva {self.id}: libro {self.libro_id} ({self.estado.name})>"
