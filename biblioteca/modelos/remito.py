"""Modelos de remito y de su historial de movimientos."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import reconstructor, relationship

from biblioteca.configuracion.base_de_datos import Base
from biblioteca.modelos.enumeraciones import SentidoRemito
from biblioteca.patrones.estados_remito import Generado, crear_estado, texto_estado


class Remito(Base):
    """Documento que acompaña a un ejemplar en un traslado entre sedes.

    Es el contexto del patrón State: guarda un objeto estado y le delega cada
    acción. En la base se guarda solo el nombre del estado, y el objeto se
    reconstruye al cargar el remito. Cada cambio de estado deja un
    MovimientoRemito, que es lo que permite seguir todo el trayecto.
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

    # Se cargan junto con el remito para poder mostrarlo después de cerrar la sesión.
    prestamo = relationship("Prestamo", back_populates="remitos", lazy="joined")
    sede_origen = relationship("Sede", foreign_keys=[sede_origen_id], lazy="joined")
    sede_destino = relationship("Sede", foreign_keys=[sede_destino_id], lazy="joined")
    movimientos = relationship(
        "MovimientoRemito",
        back_populates="remito",
        cascade="all, delete-orphan",
        order_by="MovimientoRemito.id",
        lazy="selectin",
    )

    def __init__(self, **datos):
        super().__init__(**datos)
        self._estado = Generado()
        self.nombre_estado = self._estado.nombre

    @reconstructor
    def _cargar_estado(self):
        """SQLAlchemy llama a este método al traer el remito de la base."""
        self._estado = crear_estado(self.nombre_estado)

    @classmethod
    def generar(cls, numero, prestamo, sede_origen, sede_destino, sentido, fecha_hora, observacion=None):
        """Crea un remito en estado Generado y registra el primer movimiento."""
        remito = cls(
            numero=numero,
            prestamo=prestamo,
            sede_origen=sede_origen,
            sede_destino=sede_destino,
            sentido=sentido,
            fecha_generacion=fecha_hora,
        )
        remito.movimientos.append(
            MovimientoRemito(estado_anterior=None, estado_nuevo=remito.nombre_estado, fecha_hora=fecha_hora, observacion=observacion)
        )
        return remito

    @property
    def estado(self):
        return self._estado

    @property
    def estado_visible(self):
        return texto_estado(self.nombre_estado)

    @property
    def ejemplar(self):
        return self.prestamo.ejemplar

    @property
    def esta_finalizado(self):
        return self._estado.es_final

    def fecha_de(self, nombre_estado):
        """Fecha y hora en que el remito pasó por primera vez al estado indicado, o None."""
        for movimiento in self.movimientos:
            if movimiento.estado_nuevo == nombre_estado:
                return movimiento.fecha_hora
        return None

    def paso_por(self, nombre_estado):
        return self.fecha_de(nombre_estado) is not None

    @property
    def ultima_ubicacion(self):
        """Observación del último punto de control registrado, si hubo alguno."""
        for movimiento in reversed(self.movimientos):
            if movimiento.estado_nuevo == "EnTransito":
                return movimiento.observacion
        return None

    def cambiar_estado(self, nuevo_estado, fecha_hora, observacion=None):
        """Lo usan los estados para pasar al siguiente. Registra el movimiento para la trazabilidad."""
        self.movimientos.append(
            MovimientoRemito(
                estado_anterior=self.nombre_estado,
                estado_nuevo=nuevo_estado.nombre,
                fecha_hora=fecha_hora,
                observacion=observacion,
            )
        )
        self._estado = nuevo_estado
        self.nombre_estado = nuevo_estado.nombre

    # Acciones del remito: cada una se delega en el estado actual.

    def empaquetar(self, fecha_hora, observacion=None):
        self._estado.empaquetar(self, fecha_hora, observacion)

    def despachar(self, fecha_hora, observacion=None):
        self._estado.despachar(self, fecha_hora, observacion)

    def registrar_punto_de_control(self, fecha_hora, ubicacion):
        self._estado.registrar_punto_de_control(self, fecha_hora, ubicacion)

    def recibir(self, fecha_hora, estado_fisico, observacion=None):
        self._estado.recibir(self, fecha_hora, estado_fisico, observacion)

    def registrar_danio(self, fecha_hora, observacion=None):
        self._estado.registrar_danio(self, fecha_hora, observacion)

    def reportar_extravio(self, fecha_hora, observacion=None):
        self._estado.reportar_extravio(self, fecha_hora, observacion)

    def anular(self, fecha_hora, motivo):
        self._estado.anular(self, fecha_hora, motivo)

    def cerrar(self, fecha_hora, observacion=None):
        self._estado.cerrar(self, fecha_hora, observacion)

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

    @property
    def estado_anterior_visible(self):
        return texto_estado(self.estado_anterior)

    @property
    def estado_nuevo_visible(self):
        return texto_estado(self.estado_nuevo)

    def __repr__(self):
        return f"<MovimientoRemito {self.estado_anterior} -> {self.estado_nuevo}>"
