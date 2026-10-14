"""Casos de uso y validaciones de negocio.

Cada método de servicio abre una sesión con obtener_sesion(), usa los DAO
necesarios y lanza excepciones de dominio cuando una regla no se cumple.
"""
from biblioteca.servicios.servicio_sedes import ServicioSedes
from biblioteca.servicios.servicio_socios import ServicioSocios

__all__ = ["ServicioSedes", "ServicioSocios"]
