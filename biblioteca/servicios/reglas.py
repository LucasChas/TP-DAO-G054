"""Validaciones de negocio que comparten préstamos y reservas."""
from biblioteca.excepciones import SedeDadaDeBaja, SocioInhabilitado


def validar_socio_habilitado(socio):
    if not socio.esta_habilitado:
        motivo = f" ({socio.motivo_inhabilitacion})" if socio.motivo_inhabilitacion else ""
        raise SocioInhabilitado(f"El socio {socio.nombre_completo} está inhabilitado{motivo}.")


def validar_sede_activa(sede, rol):
    """rol describe para qué se usa la sede en el mensaje, por ejemplo 'origen' o 'retiro'."""
    if not sede.esta_activa:
        raise SedeDadaDeBaja(f"La sede de {rol} '{sede.nombre}' está dada de baja.")
