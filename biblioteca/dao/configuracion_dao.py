"""Acceso a datos de los parámetros de configuración."""
from biblioteca.modelos import Configuracion


class ConfiguracionDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def obtener(self, clave):
        """Devuelve el valor guardado para la clave, o None si nunca se guardó."""
        parametro = self.sesion.get(Configuracion, clave)
        return parametro.valor if parametro else None

    def guardar(self, clave, valor):
        parametro = self.sesion.get(Configuracion, clave)
        if parametro is None:
            self.sesion.add(Configuracion(clave=clave, valor=valor))
        else:
            parametro.valor = valor
        self.sesion.flush()
