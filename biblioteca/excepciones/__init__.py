"""Excepciones de dominio del sistema."""
from biblioteca.excepciones.errores import (
    DatoInvalido,
    EjemplarDeOtraSede,
    EjemplarNoDisponible,
    EntidadDuplicada,
    EntidadNoEncontrada,
    ErrorDeNegocio,
    OperacionNoPermitida,
    SedeDadaDeBaja,
    SocioConPrestamosVencidos,
    SocioInhabilitado,
)

__all__ = [
    "DatoInvalido",
    "EjemplarDeOtraSede",
    "EjemplarNoDisponible",
    "EntidadDuplicada",
    "EntidadNoEncontrada",
    "ErrorDeNegocio",
    "OperacionNoPermitida",
    "SedeDadaDeBaja",
    "SocioConPrestamosVencidos",
    "SocioInhabilitado",
]
