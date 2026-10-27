"""Modelo de préstamo local o interbibliotecario."""
from datetime import date, timedelta

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import EstadoPrestamo, TipoPrestamo


class Prestamo(Base):
    """Préstamo de un ejemplar a un socio.

    En un préstamo local la sede de origen y la de destino coinciden. En uno
    interbibliotecario el ejemplar viaja desde su sede (origen) hasta la sede
    donde lo retira el socio (destino). El plazo se cuenta desde la entrega.
    """

    __tablename__ = "prestamos"

    PLAZO_DIAS = 14

    id = Column(Integer, primary_key=True)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"), nullable=False)
    sede_origen_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    sede_destino_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    tipo = Column(Enum(TipoPrestamo, native_enum=False, length=20), nullable=False)
    fecha_solicitud = Column(Date, nullable=False, default=date.today)
    fecha_entrega = Column(Date)
    fecha_vencimiento = Column(Date)
    estado = Column(Enum(EstadoPrestamo, native_enum=False, length=20), nullable=False, default=EstadoPrestamo.SOLICITADO)

    # Se cargan junto con el préstamo para poder mostrarlo después de cerrar la sesión.
    socio = relationship("Socio", back_populates="prestamos", lazy="joined")
    ejemplar = relationship("Ejemplar", back_populates="prestamos", lazy="joined")
    sede_origen = relationship("Sede", foreign_keys=[sede_origen_id], lazy="joined")
    sede_destino = relationship("Sede", foreign_keys=[sede_destino_id], lazy="joined")
    remitos = relationship("Remito", back_populates="prestamo", order_by="Remito.id")
    devolucion = relationship("Devolucion", back_populates="prestamo", uselist=False)

    @property
    def es_interbibliotecario(self):
        return self.tipo == TipoPrestamo.INTERBIBLIOTECARIO

    def registrar_entrega(self, fecha):
        """Entrega el ejemplar al socio: el préstamo queda activo y empieza a correr el plazo."""
        self.fecha_entrega = fecha
        self.fecha_vencimiento = fecha + timedelta(days=self.PLAZO_DIAS)
        self.estado = EstadoPrestamo.ACTIVO

    def esta_vencido_al(self, fecha):
        """Indica si el préstamo sigue activo después de su fecha de vencimiento."""
        return (
            self.estado == EstadoPrestamo.ACTIVO
            and self.fecha_vencimiento is not None
            and fecha > self.fecha_vencimiento
        )

    @property
    def esta_vencido(self):
        return self.esta_vencido_al(date.today())

    def dias_de_atraso_al(self, fecha):
        """Días transcurridos desde el vencimiento hasta la fecha indicada (0 si no hay atraso)."""
        if self.fecha_vencimiento is None or fecha <= self.fecha_vencimiento:
            return 0
        return (fecha - self.fecha_vencimiento).days

    def __repr__(self):
        return f"<Prestamo {self.id}: {self.tipo.name} {self.estado.name}>"
