"""Casos de uso de administración de socios."""
import re

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import SocioDAO
from biblioteca.excepciones import DatoInvalido, EntidadDuplicada, EntidadNoEncontrada, OperacionNoPermitida
from biblioteca.modelos import Socio
from biblioteca.modelos.enumeraciones import EstadoSocio
from biblioteca.servicios.validaciones import email_opcional, texto_obligatorio, texto_opcional


def normalizar_dni(dni):
    """Quita puntos y espacios y controla que queden entre 7 y 8 dígitos."""
    limpio = re.sub(r"[.\s]", "", dni or "")
    if not re.fullmatch(r"\d{7,8}", limpio):
        raise DatoInvalido(f"El DNI '{dni}' no es válido: debe tener 7 u 8 dígitos.")
    return limpio


def obtener_socio_o_error(dao, id_socio):
    socio = dao.obtener_por_id(id_socio)
    if socio is None:
        raise EntidadNoEncontrada(f"No existe el socio con id {id_socio}.")
    return socio


class ServicioSocios:
    def registrar_socio(self, dni, nombre, apellido, email=None, telefono=None):
        """Da de alta un socio habilitado. El DNI no puede repetirse."""
        dni = normalizar_dni(dni)
        nombre = texto_obligatorio(nombre, "nombre")
        apellido = texto_obligatorio(apellido, "apellido")
        email = email_opcional(email)
        with obtener_sesion() as sesion:
            dao = SocioDAO(sesion)
            if dao.obtener_por_dni(dni) is not None:
                raise EntidadDuplicada(f"Ya existe un socio con DNI {dni}.")
            socio = Socio(dni=dni, nombre=nombre, apellido=apellido, email=email, telefono=texto_opcional(telefono))
            dao.crear(socio)
        return socio

    def modificar_socio(self, id_socio, nombre=None, apellido=None, email=None, telefono=None):
        """Modifica los datos de contacto. El DNI no se modifica porque identifica al socio."""
        with obtener_sesion() as sesion:
            dao = SocioDAO(sesion)
            socio = obtener_socio_o_error(dao, id_socio)
            if nombre is not None:
                socio.nombre = texto_obligatorio(nombre, "nombre")
            if apellido is not None:
                socio.apellido = texto_obligatorio(apellido, "apellido")
            if email is not None:
                socio.email = email_opcional(email)
            if telefono is not None:
                socio.telefono = texto_opcional(telefono)
            dao.actualizar(socio)
        return socio

    def inhabilitar_socio(self, id_socio, motivo):
        """Un socio inhabilitado no puede recibir préstamos ni hacer reservas."""
        motivo = texto_obligatorio(motivo, "motivo")
        with obtener_sesion() as sesion:
            dao = SocioDAO(sesion)
            socio = obtener_socio_o_error(dao, id_socio)
            if not socio.esta_habilitado:
                raise OperacionNoPermitida(f"El socio {socio.nombre_completo} ya está inhabilitado.")
            socio.estado = EstadoSocio.INHABILITADO
            socio.motivo_inhabilitacion = motivo
            dao.actualizar(socio)
        return socio

    def habilitar_socio(self, id_socio):
        with obtener_sesion() as sesion:
            dao = SocioDAO(sesion)
            socio = obtener_socio_o_error(dao, id_socio)
            if socio.esta_habilitado:
                raise OperacionNoPermitida(f"El socio {socio.nombre_completo} ya está habilitado.")
            socio.estado = EstadoSocio.HABILITADO
            socio.motivo_inhabilitacion = None
            dao.actualizar(socio)
        return socio

    def obtener_socio(self, id_socio):
        with obtener_sesion() as sesion:
            return obtener_socio_o_error(SocioDAO(sesion), id_socio)

    def buscar_por_dni(self, dni):
        dni = normalizar_dni(dni)
        with obtener_sesion() as sesion:
            socio = SocioDAO(sesion).obtener_por_dni(dni)
        if socio is None:
            raise EntidadNoEncontrada(f"No existe un socio con DNI {dni}.")
        return socio

    def listar_socios(self):
        with obtener_sesion() as sesion:
            return SocioDAO(sesion).listar()
