"""Casos de uso de administración de sedes."""
from datetime import date

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import PrestamoDAO, RemitoDAO, SedeDAO
from biblioteca.excepciones import EntidadDuplicada, EntidadNoEncontrada, OperacionNoPermitida
from biblioteca.modelos import Sede
from biblioteca.modelos.enumeraciones import EstadoSede
from biblioteca.servicios.validaciones import email_opcional, texto_obligatorio, texto_opcional


def obtener_sede_o_error(dao, id_sede):
    """Devuelve la sede o lanza EntidadNoEncontrada. La usan también otros servicios."""
    sede = dao.obtener_por_id(id_sede)
    if sede is None:
        raise EntidadNoEncontrada(f"No existe la sede con id {id_sede}.")
    return sede


class ServicioSedes:
    def registrar_sede(self, nombre, direccion, telefono=None, email=None, horario_atencion=None):
        """Da de alta una sede activa. El nombre no puede repetirse en la red."""
        nombre = texto_obligatorio(nombre, "nombre")
        direccion = texto_obligatorio(direccion, "dirección")
        email = email_opcional(email)
        with obtener_sesion() as sesion:
            dao = SedeDAO(sesion)
            if dao.obtener_por_nombre(nombre) is not None:
                raise EntidadDuplicada(f"Ya existe una sede llamada '{nombre}'.")
            sede = Sede(
                nombre=nombre,
                direccion=direccion,
                telefono=texto_opcional(telefono),
                email=email,
                horario_atencion=texto_opcional(horario_atencion),
            )
            dao.crear(sede)
        return sede

    def modificar_sede(self, id_sede, nombre=None, direccion=None, telefono=None, email=None, horario_atencion=None):
        """Modifica los datos indicados. Los parámetros en None no se cambian; "" borra un dato opcional."""
        with obtener_sesion() as sesion:
            dao = SedeDAO(sesion)
            sede = obtener_sede_o_error(dao, id_sede)
            if nombre is not None:
                nombre = texto_obligatorio(nombre, "nombre")
                otra = dao.obtener_por_nombre(nombre)
                if otra is not None and otra.id != sede.id:
                    raise EntidadDuplicada(f"Ya existe una sede llamada '{nombre}'.")
                sede.nombre = nombre
            if direccion is not None:
                sede.direccion = texto_obligatorio(direccion, "dirección")
            if telefono is not None:
                sede.telefono = texto_opcional(telefono)
            if email is not None:
                sede.email = email_opcional(email)
            if horario_atencion is not None:
                sede.horario_atencion = texto_opcional(horario_atencion)
            dao.actualizar(sede)
        return sede

    def dar_de_baja_sede(self, id_sede, fecha=None):
        """Baja lógica: la sede conserva su historial pero no puede iniciar nuevas operaciones.

        No se permite mientras un ejemplar tenga que volver desde o hacia la sede: su remito de
        retorno no podría despacharse (no se despacha con una sede dada de baja) ni anularse
        (un retorno no se anula). Los envíos de ida que todavía no salieron sí se pueden anular.
        """
        with obtener_sesion() as sesion:
            dao = SedeDAO(sesion)
            sede = obtener_sede_o_error(dao, id_sede)
            if not sede.esta_activa:
                raise OperacionNoPermitida(f"La sede '{sede.nombre}' ya está dada de baja.")
            falta_volver = (
                PrestamoDAO(sesion).hay_interbibliotecarios_fuera_de_sede(sede.id)
                or RemitoDAO(sesion).hay_retornos_en_curso(sede.id)
            )
            if falta_volver:
                raise OperacionNoPermitida(
                    f"La sede '{sede.nombre}' tiene ejemplares en préstamo o en viaje entre sedes que todavía "
                    "tienen que volver. Se puede dar de baja cuando terminen esos traslados."
                )
            sede.estado = EstadoSede.BAJA
            sede.fecha_baja = fecha or date.today()
            dao.actualizar(sede)
        return sede

    def reactivar_sede(self, id_sede):
        with obtener_sesion() as sesion:
            dao = SedeDAO(sesion)
            sede = obtener_sede_o_error(dao, id_sede)
            if sede.esta_activa:
                raise OperacionNoPermitida(f"La sede '{sede.nombre}' ya está activa.")
            sede.estado = EstadoSede.ACTIVA
            sede.fecha_baja = None
            dao.actualizar(sede)
        return sede

    def obtener_sede(self, id_sede):
        with obtener_sesion() as sesion:
            return obtener_sede_o_error(SedeDAO(sesion), id_sede)

    def listar_sedes(self, solo_activas=False):
        with obtener_sesion() as sesion:
            dao = SedeDAO(sesion)
            return dao.listar_activas() if solo_activas else dao.listar()
