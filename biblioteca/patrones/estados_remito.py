"""Patrón State para el ciclo de vida del remito.

El Remito es el contexto: guarda un objeto estado y le delega cada acción.
Cada estado implementa solo las acciones que tienen sentido en él; las demás
heredan el comportamiento por defecto, que lanza TransicionRemitoInvalida sin
modificar nada. Así las reglas de qué se puede hacer en cada momento quedan
en una clase por estado y no en una cadena de if.

Además de cambiar de estado, cada transición aplica sus consecuencias sobre
el ejemplar y el préstamo, que dependen de si el remito es de ida (hacia la
sede donde retira el socio) o de retorno (de vuelta a la sede propietaria).
Las consecuencias que necesitan consultar la base (reasignar reservas,
generar el remito de retorno) las resuelve el servicio de remitos.

Este módulo no importa los modelos para evitar una importación circular:
trabaja sobre los atributos del remito que recibe.
"""
from abc import ABC, abstractmethod

from biblioteca.excepciones import DatoInvalido, SedeDadaDeBaja, TransicionRemitoInvalida
from biblioteca.modelos.enumeraciones import EstadoEjemplar, EstadoFisico, EstadoPrestamo, SentidoRemito


class EstadoRemito(ABC):
    """Estado abstracto. Por defecto ninguna acción está permitida."""

    @property
    @abstractmethod
    def nombre(self):
        """Nombre con el que el estado se guarda en la base."""

    @property
    def es_final(self):
        return False

    def _no_permitida(self, accion):
        raise TransicionRemitoInvalida(f"No se puede {accion} un remito en estado {texto_estado(self.nombre)}.")

    def empaquetar(self, remito, fecha_hora, observacion):
        self._no_permitida("empaquetar")

    def despachar(self, remito, fecha_hora, observacion):
        self._no_permitida("despachar")

    def registrar_punto_de_control(self, remito, fecha_hora, ubicacion):
        self._no_permitida("registrar un punto de control en")

    def recibir(self, remito, fecha_hora, estado_fisico, observacion):
        self._no_permitida("recibir")

    def registrar_danio(self, remito, fecha_hora, observacion):
        self._no_permitida("registrar daño en")

    def reportar_extravio(self, remito, fecha_hora, observacion):
        self._no_permitida("reportar como extraviado")

    def anular(self, remito, fecha_hora, motivo):
        self._no_permitida("anular")

    def cerrar(self, remito, fecha_hora, observacion):
        self._no_permitida("cerrar")


class Generado(EstadoRemito):
    """El remito se emitió pero el ejemplar todavía no se preparó."""

    nombre = "Generado"

    def empaquetar(self, remito, fecha_hora, observacion):
        remito.cambiar_estado(Empaquetado(), fecha_hora, observacion)

    def anular(self, remito, fecha_hora, motivo):
        _anular(remito, fecha_hora, motivo)


class Empaquetado(EstadoRemito):
    """El ejemplar está embalado en la sede de origen esperando salir."""

    nombre = "Empaquetado"

    def despachar(self, remito, fecha_hora, observacion):
        # La consigna prohíbe iniciar envíos hacia o desde una sede dada de baja.
        for rol, sede in (("origen", remito.sede_origen), ("destino", remito.sede_destino)):
            if not sede.esta_activa:
                raise SedeDadaDeBaja(f"No se puede despachar: la sede de {rol} '{sede.nombre}' está dada de baja.")
        remito.ejemplar.estado = EstadoEjemplar.EN_TRANSITO
        if remito.sentido == SentidoRemito.IDA:
            remito.prestamo.estado = EstadoPrestamo.EN_ENVIO
        remito.cambiar_estado(Despachado(), fecha_hora, observacion)

    def anular(self, remito, fecha_hora, motivo):
        _anular(remito, fecha_hora, motivo)


class EnViaje(EstadoRemito):
    """Comportamiento común de Despachado y EnTransito: el paquete ya salió y todavía no llegó."""

    def registrar_punto_de_control(self, remito, fecha_hora, ubicacion):
        if not (ubicacion or "").strip():
            raise DatoInvalido("Hay que indicar la ubicación del punto de control.")
        remito.cambiar_estado(EnTransito(), fecha_hora, ubicacion.strip())

    def recibir(self, remito, fecha_hora, estado_fisico, observacion):
        ejemplar = remito.ejemplar
        # Un daño que ya estaba registrado antes del envío (por ejemplo, el socio lo
        # devolvió dañado) no es un incidente del traslado.
        danio_nuevo = estado_fisico == EstadoFisico.DANIADO and ejemplar.estado_fisico != EstadoFisico.DANIADO
        ejemplar.estado_fisico = estado_fisico
        remito.cambiar_estado(Recibido(), fecha_hora, observacion)
        if danio_nuevo:
            remito.registrar_danio(fecha_hora, observacion or "Daño constatado en la recepción")
        elif remito.sentido == SentidoRemito.IDA:
            ejemplar.estado = EstadoEjemplar.PRESTADO
            remito.prestamo.estado = EstadoPrestamo.LISTO_PARA_RETIRO
        else:
            # Volvió a su sede y el remito termina su recorrido. Si ya venía dañado, queda en reparación.
            if estado_fisico == EstadoFisico.DANIADO:
                ejemplar.estado = EstadoEjemplar.EN_REPARACION
            else:
                ejemplar.estado = EstadoEjemplar.DISPONIBLE
            remito.cerrar(fecha_hora, "Ejemplar reintegrado a su sede")

    def reportar_extravio(self, remito, fecha_hora, observacion):
        remito.ejemplar.estado = EstadoEjemplar.EXTRAVIADO
        if remito.sentido == SentidoRemito.IDA:
            remito.prestamo.estado = EstadoPrestamo.CANCELADO
        remito.cambiar_estado(Extraviado(), fecha_hora, observacion)
        remito.cerrar(fecha_hora, "Envío cerrado por extravío")


class Despachado(EnViaje):
    """El paquete salió de la sede de origen."""

    nombre = "Despachado"


class EnTransito(EnViaje):
    """El paquete pasó por al menos un punto de control. Admite registrar más puntos."""

    nombre = "EnTransito"


class Recibido(EstadoRemito):
    """La sede de destino recibió el paquete y revisó su estado físico."""

    nombre = "Recibido"

    def registrar_danio(self, remito, fecha_hora, observacion):
        # Solo se llega acá antes de la entrega al socio: al entregar, el remito de ida se cierra.
        remito.ejemplar.estado_fisico = EstadoFisico.DANIADO
        if remito.sentido == SentidoRemito.IDA:
            # No se entrega al socio: el ejemplar vuelve a su sede con un remito de retorno.
            remito.prestamo.estado = EstadoPrestamo.CANCELADO
            remito.ejemplar.estado = EstadoEjemplar.EN_TRANSITO
        else:
            # Llegó dañado a su propia sede: queda fuera de préstamo hasta que se repare o se dé de baja.
            remito.ejemplar.estado = EstadoEjemplar.EN_REPARACION
        remito.cambiar_estado(Daniado(), fecha_hora, observacion)

    def cerrar(self, remito, fecha_hora, observacion):
        remito.cambiar_estado(Cerrado(), fecha_hora, observacion)


class Daniado(EstadoRemito):
    """Se constató daño en la recepción."""

    nombre = "Daniado"

    def cerrar(self, remito, fecha_hora, observacion):
        remito.cambiar_estado(Cerrado(), fecha_hora, observacion)


class Extraviado(EstadoRemito):
    """El paquete no llegó a destino."""

    nombre = "Extraviado"

    def cerrar(self, remito, fecha_hora, observacion):
        remito.cambiar_estado(Cerrado(), fecha_hora, observacion)


class Anulado(EstadoRemito):
    """El envío se canceló antes de salir de la sede de origen. Es un estado final."""

    nombre = "Anulado"

    @property
    def es_final(self):
        return True


class Cerrado(EstadoRemito):
    """El remito terminó su recorrido y quedó archivado. Es un estado final."""

    nombre = "Cerrado"

    @property
    def es_final(self):
        return True


def _anular(remito, fecha_hora, motivo):
    """Anulación común a Generado y Empaquetado. Solo los remitos de ida se pueden anular:
    un remito de retorno lleva el ejemplar a su sede y no tiene alternativa."""
    if remito.sentido == SentidoRemito.RETORNO:
        raise TransicionRemitoInvalida("Un remito de retorno no se puede anular: el ejemplar debe volver a su sede.")
    if not (motivo or "").strip():
        raise DatoInvalido("Hay que indicar el motivo de la anulación.")
    remito.prestamo.estado = EstadoPrestamo.CANCELADO
    remito.cambiar_estado(Anulado(), fecha_hora, motivo.strip())


ESTADOS = {
    clase.nombre: clase
    for clase in (Generado, Empaquetado, Despachado, EnTransito, Recibido, Daniado, Extraviado, Anulado, Cerrado)
}


def crear_estado(nombre):
    """Reconstruye el objeto estado a partir del nombre guardado en la base."""
    return ESTADOS[nombre]()


# El nombre de la clase es el que se guarda en la base; al usuario se le muestra este texto.
TEXTOS = {"EnTransito": "En tránsito", "Daniado": "Dañado"}


def texto_estado(nombre):
    """Texto para mostrar de un estado guardado (None si no hay estado, como el anterior al primero)."""
    return TEXTOS.get(nombre, nombre)
