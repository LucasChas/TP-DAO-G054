"""Funciones de validación de datos de entrada compartidas por los servicios."""
import re

from biblioteca.excepciones import DatoInvalido


def texto_obligatorio(valor, campo):
    """Devuelve el texto sin espacios sobrantes o lanza DatoInvalido si está vacío."""
    texto = (valor or "").strip()
    if not texto:
        raise DatoInvalido(f"El campo '{campo}' es obligatorio.")
    return texto


def texto_opcional(valor):
    """Devuelve el texto sin espacios sobrantes, o None si está vacío."""
    texto = (valor or "").strip()
    return texto or None


def email_opcional(valor):
    """Valida un email si se ingresó uno. Solo controla el formato básico usuario@dominio."""
    email = texto_opcional(valor)
    if email is not None and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise DatoInvalido(f"El email '{email}' no tiene un formato válido.")
    return email
