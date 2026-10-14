"""Tipos cerrados del dominio.

Se guardan en la base como texto (el nombre de cada constante) y el valor
es el texto que se muestra al usuario.
"""
from enum import Enum


class EstadoSede(Enum):
    ACTIVA = "Activa"
    BAJA = "Dada de baja"


class EstadoSocio(Enum):
    HABILITADO = "Habilitado"
    INHABILITADO = "Inhabilitado"


class TipoMaterial(Enum):
    LIBRO = "Libro"
    REVISTA = "Revista"
    CONSULTA = "Material de consulta"


class EstadoEjemplar(Enum):
    DISPONIBLE = "Disponible"
    RESERVADO = "Reservado"
    PRESTADO = "Prestado"
    EN_TRANSITO = "En tránsito"
    EN_REPARACION = "En reparación"
    EXTRAVIADO = "Extraviado"
    BAJA = "Dado de baja"


class EstadoFisico(Enum):
    BUENO = "Bueno"
    REGULAR = "Regular"
    DANIADO = "Dañado"


class TipoPrestamo(Enum):
    LOCAL = "Local"
    INTERBIBLIOTECARIO = "Interbibliotecario"


class EstadoPrestamo(Enum):
    SOLICITADO = "Solicitado"
    EN_ENVIO = "En envío"
    LISTO_PARA_RETIRO = "Listo para retiro"
    ACTIVO = "Activo"
    DEVUELTO = "Devuelto"
    CANCELADO = "Cancelado"


class EstadoReserva(Enum):
    PENDIENTE = "Pendiente"
    DISPONIBLE = "Disponible para retiro"
    CUMPLIDA = "Cumplida"
    CANCELADA = "Cancelada"
    VENCIDA = "Vencida"


class SentidoRemito(Enum):
    IDA = "Ida"
    RETORNO = "Retorno"
