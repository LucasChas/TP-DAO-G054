"""Modelo de reserva de un libro."""
from datetime import date, timedelta

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

    PLAZO_RETIRO_DIAS = 3

    id = Column(Integer, primary_key=True)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"))
    fecha_reserva = Column(Date, nullable=False, default=date.today)
    fecha_limite_retiro = Column(Date)
    estado = Column(Enum(EstadoReserva, native_enum=False, length=20), nullable=False, default=EstadoReserva.PENDIENTE)

    # Se cargan junto con la reserva para poder mostrarla después de cerrar la sesión.
    socio = relationship("Socio", back_populates="reservas", lazy="joined")
    libro = relationship("Libro", back_populates="reservas", lazy="joined")
    sede = relationship("Sede", lazy="joined")
    ejemplar = relationship("Ejemplar", lazy="joined")

    @property
    def esta_activa(self):
        return self.estado in (EstadoReserva.PENDIENTE, EstadoReserva.DISPONIBLE)

    def asignar_ejemplar(self, ejemplar, fecha):
        """Aparta el ejemplar para el socio, que tiene PLAZO_RETIRO_DIAS días para retirarlo."""
        self.ejemplar = ejemplar
        self.estado = EstadoReserva.DISPONIBLE
        self.fecha_limite_retiro = fecha + timedelta(days=self.PLAZO_RETIRO_DIAS)

    def __repr__(self):
        return f"<Reserva {self.id}: libro {self.libro_id} ({self.estado.name})>"
