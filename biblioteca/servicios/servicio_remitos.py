"""Casos de uso de remitos: empaquetar, despachar, seguir y recibir ejemplares entre sedes.

Las reglas de qué acción se permite en cada estado están en las clases del
patrón State (biblioteca/patrones/estados_remito.py). Este servicio abre la
sesión, busca el remito, le pide la acción y resuelve las consecuencias que
necesitan la base: reasignar reservas y generar el remito de retorno.
"""
from datetime import datetime

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import RemitoDAO
from biblioteca.excepciones import EntidadNoEncontrada
from biblioteca.modelos import Remito
from biblioteca.modelos.enumeraciones import EstadoEjemplar, SentidoRemito
from biblioteca.servicios.asignacion_reservas import asignar_a_reserva_pendiente, liberar_ejemplar


def generar_remito(sesion, prestamo, sentido, fecha_hora, observacion=None):
    """Emite un remito para el préstamo. El de ida va de la sede propietaria a la de retiro;
    el de retorno hace el camino inverso."""
    if sentido == SentidoRemito.IDA:
        origen, destino = prestamo.sede_origen, prestamo.sede_destino
    else:
        origen, destino = prestamo.sede_destino, prestamo.sede_origen
    dao = RemitoDAO(sesion)
    remito = Remito.generar(dao.siguiente_numero(), prestamo, origen, destino, sentido, fecha_hora, observacion)
    return dao.crear(remito)


def remito_de_ida(prestamo):
    for remito in prestamo.remitos:
        if remito.sentido == SentidoRemito.IDA:
            return remito
    return None


def anular_remito(sesion, remito, motivo, fecha_hora):
    """Anula el remito de ida (cancela el préstamo) y libera el ejemplar."""
    remito.anular(fecha_hora, motivo)
    liberar_ejemplar(sesion, remito.ejemplar, fecha_hora.date())


def _resolver_consecuencias(sesion, remito, fecha_hora):
    """Consecuencias de una transición que necesitan consultar la base."""
    if remito.sentido == SentidoRemito.IDA and remito.nombre_estado == "Daniado":
        # Opción aprobada: el ejemplar dañado vuelve a su sede con un remito de retorno.
        retorno = generar_remito(
            sesion, remito.prestamo, SentidoRemito.RETORNO, fecha_hora, f"Retorno por daño en {remito.numero}"
        )
        remito.cerrar(fecha_hora, f"Se generó el remito de retorno {retorno.numero}")
    elif remito.nombre_estado == "Daniado":
        remito.cerrar(fecha_hora, "Ejemplar enviado a reparación en su sede")
    elif (
        remito.sentido == SentidoRemito.RETORNO
        and remito.nombre_estado == "Cerrado"
        and remito.ejemplar.estado == EstadoEjemplar.DISPONIBLE
    ):
        # El ejemplar volvió sano a su sede: si alguien lo esperaba, se aparta para esa reserva.
        asignar_a_reserva_pendiente(sesion, remito.ejemplar, fecha_hora.date())
    sesion.flush()


def obtener_remito_o_error(dao, id_remito):
    remito = dao.obtener_por_id(id_remito)
    if remito is None:
        raise EntidadNoEncontrada(f"No existe el remito con id {id_remito}.")
    return remito


class ServicioRemitos:
    def _ejecutar(self, id_remito, accion, fecha_hora):
        """Abre la sesión, aplica la acción al remito y resuelve sus consecuencias."""
        fecha_hora = fecha_hora or datetime.now()
        with obtener_sesion() as sesion:
            remito = obtener_remito_o_error(RemitoDAO(sesion), id_remito)
            accion(remito, fecha_hora)
            _resolver_consecuencias(sesion, remito, fecha_hora)
        return remito

    def empaquetar(self, id_remito, observacion=None, fecha_hora=None):
        return self._ejecutar(id_remito, lambda r, f: r.empaquetar(f, observacion), fecha_hora)

    def despachar(self, id_remito, observacion=None, fecha_hora=None):
        return self._ejecutar(id_remito, lambda r, f: r.despachar(f, observacion), fecha_hora)

    def registrar_punto_de_control(self, id_remito, ubicacion, fecha_hora=None):
        return self._ejecutar(id_remito, lambda r, f: r.registrar_punto_de_control(f, ubicacion), fecha_hora)

    def recibir(self, id_remito, estado_fisico, observacion=None, fecha_hora=None):
        return self._ejecutar(id_remito, lambda r, f: r.recibir(f, estado_fisico, observacion), fecha_hora)

    def registrar_danio(self, id_remito, observacion=None, fecha_hora=None):
        return self._ejecutar(id_remito, lambda r, f: r.registrar_danio(f, observacion), fecha_hora)

    def reportar_extravio(self, id_remito, observacion=None, fecha_hora=None):
        return self._ejecutar(id_remito, lambda r, f: r.reportar_extravio(f, observacion), fecha_hora)

    def anular(self, id_remito, motivo, fecha_hora=None):
        fecha_hora = fecha_hora or datetime.now()
        with obtener_sesion() as sesion:
            remito = obtener_remito_o_error(RemitoDAO(sesion), id_remito)
            anular_remito(sesion, remito, motivo, fecha_hora)
        return remito

    def obtener_remito(self, id_remito):
        with obtener_sesion() as sesion:
            return obtener_remito_o_error(RemitoDAO(sesion), id_remito)

    def listar_remitos(self, solo_en_curso=False):
        """Lista los remitos; en curso son los que todavía no se cerraron ni anularon."""
        with obtener_sesion() as sesion:
            dao = RemitoDAO(sesion)
            remitos = dao.listar()
        if solo_en_curso:
            remitos = [r for r in remitos if not r.esta_finalizado]
        return remitos

    def listar_remitos_de_prestamo(self, id_prestamo):
        with obtener_sesion() as sesion:
            return RemitoDAO(sesion).listar_por_prestamo(id_prestamo)
