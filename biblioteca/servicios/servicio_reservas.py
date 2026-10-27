"""Casos de uso de reservas de libros."""
from datetime import date

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import EjemplarDAO, LibroDAO, ReservaDAO, SedeDAO, SocioDAO
from biblioteca.excepciones import EntidadDuplicada, EntidadNoEncontrada, OperacionNoPermitida
from biblioteca.modelos import Reserva
from biblioteca.modelos.enumeraciones import EstadoReserva
from biblioteca.patrones.iterador_catalogo import CatalogoEjemplares
from biblioteca.servicios.asignacion_reservas import liberar_ejemplar
from biblioteca.servicios.reglas import validar_sede_activa, validar_socio_habilitado
from biblioteca.servicios.servicio_catalogo import obtener_libro_o_error
from biblioteca.servicios.servicio_prestamos import ServicioPrestamos
from biblioteca.servicios.servicio_sedes import obtener_sede_o_error
from biblioteca.servicios.servicio_socios import obtener_socio_o_error


def obtener_reserva_o_error(dao, id_reserva):
    reserva = dao.obtener_por_id(id_reserva)
    if reserva is None:
        raise EntidadNoEncontrada(f"No existe la reserva con id {id_reserva}.")
    return reserva


class ServicioReservas:
    def reservar(self, id_socio, id_libro, id_sede, fecha=None):
        """Registra una reserva del libro para retirar en la sede indicada.

        Solo tiene sentido reservar si la sede tiene ejemplares de ese libro y
        ninguno está disponible: si hay uno disponible se presta directamente,
        y si la sede no tiene ninguno corresponde un préstamo interbibliotecario.
        """
        fecha = fecha or date.today()
        with obtener_sesion() as sesion:
            socio = obtener_socio_o_error(SocioDAO(sesion), id_socio)
            libro = obtener_libro_o_error(LibroDAO(sesion), id_libro)
            sede = obtener_sede_o_error(SedeDAO(sesion), id_sede)
            validar_socio_habilitado(socio)
            validar_sede_activa(sede, "retiro")

            catalogo = CatalogoEjemplares(EjemplarDAO(sesion).listar(id_libro=libro.id, id_sede=sede.id))
            if not list(catalogo.en_circulacion()):
                raise OperacionNoPermitida(
                    f"La sede '{sede.nombre}' no tiene ejemplares de '{libro.titulo}'. "
                    "Solicite un préstamo interbibliotecario."
                )
            if list(catalogo.disponibles()):
                raise OperacionNoPermitida(
                    f"Hay ejemplares de '{libro.titulo}' disponibles en '{sede.nombre}'. Solicite el préstamo."
                )

            dao = ReservaDAO(sesion)
            if dao.obtener_activa(socio.id, libro.id) is not None:
                raise EntidadDuplicada(f"El socio ya tiene una reserva activa de '{libro.titulo}'.")
            reserva = Reserva(socio=socio, libro=libro, sede=sede, ejemplar=None, fecha_reserva=fecha)
            dao.crear(reserva)
        return reserva

    def cancelar_reserva(self, id_reserva, fecha=None):
        """Cancela una reserva activa. Si tenía un ejemplar apartado, pasa a la siguiente reserva."""
        fecha = fecha or date.today()
        with obtener_sesion() as sesion:
            reserva = obtener_reserva_o_error(ReservaDAO(sesion), id_reserva)
            if not reserva.esta_activa:
                raise OperacionNoPermitida(f"La reserva está {reserva.estado.value.lower()} y no se puede cancelar.")
            ejemplar = reserva.ejemplar
            reserva.estado = EstadoReserva.CANCELADA
            reserva.ejemplar = None
            if ejemplar is not None:
                liberar_ejemplar(sesion, ejemplar, fecha)
        return reserva

    def registrar_retiro(self, id_reserva, fecha=None):
        """El socio retira el ejemplar que tenía apartado: se registra el préstamo local
        y la reserva queda cumplida. Solo se retira una reserva disponible para retiro."""
        with obtener_sesion() as sesion:
            reserva = obtener_reserva_o_error(ReservaDAO(sesion), id_reserva)
            if reserva.estado != EstadoReserva.DISPONIBLE:
                raise OperacionNoPermitida(
                    f"La reserva está {reserva.estado.value.lower()}: solo se retiran reservas disponibles para retiro."
                )
            datos = (reserva.socio_id, reserva.ejemplar_id, reserva.sede_id)
        # El préstamo valida al socio (habilitado, sin vencidos ni multas) y marca la reserva como cumplida.
        return ServicioPrestamos().registrar_prestamo_local(*datos, fecha=fecha)

    def procesar_reservas_vencidas(self, fecha=None):
        """Vence las reservas cuyo plazo de retiro pasó y reasigna sus ejemplares.

        Devuelve la lista de reservas vencidas.
        """
        fecha = fecha or date.today()
        with obtener_sesion() as sesion:
            vencidas = ReservaDAO(sesion).listar_disponibles_vencidas(fecha)
            for reserva in vencidas:
                ejemplar = reserva.ejemplar
                reserva.estado = EstadoReserva.VENCIDA
                reserva.ejemplar = None
                sesion.flush()
                liberar_ejemplar(sesion, ejemplar, fecha)
        return vencidas

    def obtener_reserva(self, id_reserva):
        with obtener_sesion() as sesion:
            return obtener_reserva_o_error(ReservaDAO(sesion), id_reserva)

    def listar_reservas(self, solo_activas=False):
        with obtener_sesion() as sesion:
            return ReservaDAO(sesion).listar(solo_activas=solo_activas)
