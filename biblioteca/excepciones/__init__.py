"""Excepciones de dominio del sistema."""
from biblioteca.excepciones.errores import (
    DatoInvalido,
    EntidadDuplicada,
    EntidadNoEncontrada,
    ErrorDeNegocio,
    OperacionNoPermitida,
    SedeDadaDeBaja,
)

__all__ = [
    "DatoInvalido",
    "EntidadDuplicada",
    "EntidadNoEncontrada",
    "ErrorDeNegocio",
    "OperacionNoPermitida",
    "SedeDadaDeBaja",
]
