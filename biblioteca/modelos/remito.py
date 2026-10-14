"""Modelos de remito y de su historial de movimientos."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import SentidoRemito


class Remito(Base):
    """Documento que acompaña a un ejemplar en un traslado entre sedes.

    En la base se guarda el nombre del estado actual; el comportamiento de
    cada estado se implementa con el patrón State.
    """

    __tablename__ = "remitos"

    id = Column(Integer, primary_key=True)
    numero = Column(String(20), nullable=False, unique=True)
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=False)
    sede_origen_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    sede_destino_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    sentido = Column(Enum(SentidoRemito, native_enum=False, length=20), nullable=False)
    nombre_estado = Column(String(20), nullable=False, default="Generado")
    fecha_generacion = Column(DateTime, nullable=False, default=datetime.now)

    prestamo = relationship("Prestamo", back_populates="remitos")
    sede_origen = relationship("Sede", foreign_keys=[sede_origen_id])
    sede_destino = relationship("Sede", foreign_keys=[sede_destino_id])
    movimientos = relationship(
        "MovimientoRemito",
        back_populates="remito",
        cascade="all, delete-orphan",
        order_by="MovimientoRemito.id",
    )

    def __repr__(self):
        return f"<Remito {self.numero} ({self.nombre_estado})>"


class MovimientoRemito(Base):
    """Registro de un cambio de estado de un remito. Permite reconstruir todo el trayecto."""

    __tablename__ = "movimientos_remito"

    id = Column(Integer, primary_key=True)
    remito_id = Column(Integer, ForeignKey("remitos.id"), nullable=False)
    estado_anterior = Column(String(20))
    estado_nuevo = Column(String(20), nullable=False)
    fecha_hora = Column(DateTime, nullable=False, default=datetime.now)
    observacion = Column(String(200))

    remito = relationship("Remito", back_populates="movimientos")

    def __repr__(self):
        return f"<MovimientoRemito {self.estado_anterior} -> {self.estado_nuevo}>"
