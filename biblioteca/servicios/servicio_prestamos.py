"""Casos de uso de préstamos locales e interbibliotecarios."""
from datetime import date, datetime

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import EjemplarDAO, PrestamoDAO, ReservaDAO, SedeDAO, SocioDAO
from biblioteca.excepciones import (
    DatoInvalido,
    EjemplarDeOtraSede,
    EjemplarNoDisponible,
    EntidadNoEncontrada,
    OperacionNoPermitida,
    SocioConPrestamosVencidos,
)
from biblioteca.modelos import Prestamo
from biblioteca.modelos.enumeraciones import EstadoEjemplar, EstadoPrestamo, EstadoReserva, SentidoRemito, TipoPrestamo
from biblioteca.servicios.reglas import validar_sede_activa, validar_socio_habilitado
from biblioteca.servicios.servicio_catalogo import obtener_ejemplar_o_error
from biblioteca.servicios.servicio_remitos import anular_remito, generar_remito, remito_de_ida
from biblioteca.servicios.servicio_sedes import obtener_sede_o_error
from biblioteca.servicios.servicio_socios import obtener_socio_o_error


def obtener_prestamo_o_error(dao, id_prestamo):
    prestamo = dao.obtener_por_id(id_prestamo)
    if prestamo is None:
        raise EntidadNoEncontrada(f"No existe el préstamo con id {id_prestamo}.")
    return prestamo


class ServicioPrestamos:
    def _validar_solicitud(self, sesion, socio, ejemplar, sede_origen, sede_destino, fecha):
        """Validaciones de la consigna comunes a los dos tipos de préstamo.

        Devuelve la reserva del socio que tenía apartado el ejemplar, o None.
        """
        validar_socio_habilitado(socio)
        if PrestamoDAO(sesion).socio_tiene_vencidos(socio.id, fecha):
            raise SocioConPrestamosVencidos(
                f"El socio {socio.nombre_completo} tiene préstamos vencidos sin devolver."
            )
        validar_sede_activa(sede_origen, "origen")
        validar_sede_activa(sede_destino, "destino")
        if ejemplar.sede_id != sede_origen.id:
            raise EjemplarDeOtraSede(
                f"El ejemplar {ejemplar.codigo_inventario} pertenece a '{ejemplar.sede.nombre}', "
                f"no a la sede de origen '{sede_origen.nombre}'."
            )
        if ejemplar.estado == EstadoEjemplar.DISPONIBLE:
            return None
        if ejemplar.estado == EstadoEjemplar.RESERVADO:
            reserva = ReservaDAO(sesion).obtener_disponible_para(socio.id, ejemplar.id)
            if reserva is not None:
                return reserva
            raise EjemplarNoDisponible(
                f"El ejemplar {ejemplar.codigo_inventario} está apartado para la reserva de otro socio."
            )
        raise EjemplarNoDisponible(
            f"El ejemplar {ejemplar.codigo_inventario} no está disponible ({ejemplar.estado.value.lower()})."
        )

    def registrar_prestamo_local(self, id_socio, id_ejemplar, id_sede, fecha=None):
        """El socio retira en la misma sede a la que pertenece el ejemplar.

        El préstamo queda activo en el momento y vence a los 14 días.
        """
        fecha = fecha or date.today()
        with obtener_sesion() as sesion:
            socio = obtener_socio_o_error(SocioDAO(sesion), id_socio)
            ejemplar = obtener_ejemplar_o_error(EjemplarDAO(sesion), id_ejemplar)
            sede = obtener_sede_o_error(SedeDAO(sesion), id_sede)
            reserva = self._validar_solicitud(sesion, socio, ejemplar, sede, sede, fecha)

            prestamo = Prestamo(
                socio=socio,
                ejemplar=ejemplar,
                sede_origen=sede,
                sede_destino=sede,
                tipo=TipoPrestamo.LOCAL,
                fecha_solicitud=fecha,
            )
            prestamo.registrar_entrega(fecha)
            ejemplar.estado = EstadoEjemplar.PRESTADO
            if reserva is not None:
                reserva.estado = EstadoReserva.CUMPLIDA
            PrestamoDAO(sesion).crear(prestamo)
        return prestamo

    def solicitar_prestamo_interbibliotecario(self, id_socio, id_ejemplar, id_sede_origen, id_sede_destino, fecha=None):
        """El socio pide en la sede de destino un ejemplar que pertenece a la sede de origen.

        El préstamo queda SOLICITADO, el ejemplar comprometido y se genera el
        remito de ida. El plazo empieza a correr recién cuando el socio lo
        retira en la sede de destino.
        """
        fecha = fecha or date.today()
        if id_sede_origen == id_sede_destino:
            raise DatoInvalido("En un préstamo interbibliotecario la sede de origen y la de destino deben ser distintas.")
        with obtener_sesion() as sesion:
            socio = obtener_socio_o_error(SocioDAO(sesion), id_socio)
            ejemplar = obtener_ejemplar_o_error(EjemplarDAO(sesion), id_ejemplar)
            sede_origen = obtener_sede_o_error(SedeDAO(sesion), id_sede_origen)
            sede_destino = obtener_sede_o_error(SedeDAO(sesion), id_sede_destino)
            reserva = self._validar_solicitud(sesion, socio, ejemplar, sede_origen, sede_destino, fecha)

            prestamo = Prestamo(
                socio=socio,
                ejemplar=ejemplar,
                sede_origen=sede_origen,
                sede_destino=sede_destino,
                tipo=TipoPrestamo.INTERBIBLIOTECARIO,
                fecha_solicitud=fecha,
                estado=EstadoPrestamo.SOLICITADO,
            )
            ejemplar.estado = EstadoEjemplar.PRESTADO
            if reserva is not None:
                reserva.estado = EstadoReserva.CUMPLIDA
            PrestamoDAO(sesion).crear(prestamo)
            generar_remito(sesion, prestamo, SentidoRemito.IDA, datetime.combine(fecha, datetime.now().time()))
        return prestamo

    def entregar_prestamo(self, id_prestamo, fecha=None):
        """El socio retira en la sede de destino el ejemplar que llegó con el remito de ida.

        Desde este momento corre el plazo de 14 días y el remito de ida se cierra.
        """
        fecha = fecha or date.today()
        with obtener_sesion() as sesion:
            prestamo = obtener_prestamo_o_error(PrestamoDAO(sesion), id_prestamo)
            if prestamo.estado != EstadoPrestamo.LISTO_PARA_RETIRO:
                raise OperacionNoPermitida(
                    f"El préstamo está {prestamo.estado.value.lower()}: solo se entregan préstamos listos para retiro."
                )
            validar_socio_habilitado(prestamo.socio)
            prestamo.registrar_entrega(fecha)
            remito_de_ida(prestamo).cerrar(datetime.combine(fecha, datetime.now().time()), "Entregado al socio")
        return prestamo

    def cancelar_prestamo(self, id_prestamo, motivo="Cancelado por el socio", fecha=None):
        """Cancela una solicitud interbibliotecaria que todavía no salió de la sede de origen.

        Anula el remito de ida (el patrón State rechaza la anulación si ya se
        despachó) y el ejemplar vuelve a estar disponible o pasa a la siguiente reserva.
        """
        fecha_hora = datetime.combine(fecha or date.today(), datetime.now().time())
        with obtener_sesion() as sesion:
            prestamo = obtener_prestamo_o_error(PrestamoDAO(sesion), id_prestamo)
            if prestamo.estado != EstadoPrestamo.SOLICITADO:
                raise OperacionNoPermitida(
                    f"El préstamo está {prestamo.estado.value.lower()}: solo se cancelan solicitudes no despachadas."
                )
            anular_remito(sesion, remito_de_ida(prestamo), motivo, fecha_hora)
        return prestamo

    def obtener_prestamo(self, id_prestamo):
        with obtener_sesion() as sesion:
            return obtener_prestamo_o_error(PrestamoDAO(sesion), id_prestamo)

    def listar_prestamos(self, estados=None):
        with obtener_sesion() as sesion:
            return PrestamoDAO(sesion).listar(estados)

    def listar_prestamos_de_socio(self, id_socio):
        with obtener_sesion() as sesion:
            obtener_socio_o_error(SocioDAO(sesion), id_socio)
            return PrestamoDAO(sesion).listar_por_socio(id_socio)

    def listar_vencidos(self, fecha=None):
        with obtener_sesion() as sesion:
            return PrestamoDAO(sesion).listar_vencidos_al(fecha or date.today())
