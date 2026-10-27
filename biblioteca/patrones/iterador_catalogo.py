"""Patrón Iterator para recorrer los ejemplares del catálogo.

CatalogoEjemplares es el agregado: guarda la colección y la mantiene oculta.
Quien lo usa solo puede recorrerlo con un IteradorEjemplares, que sabe
saltear los ejemplares que no cumplen el filtro pedido (por sede, por libro
o por disponibilidad).
"""
from biblioteca.modelos.enumeraciones import EstadoEjemplar


class IteradorEjemplares:
    """Recorre una lista de ejemplares devolviendo solo los que cumplen la condición."""

    def __init__(self, ejemplares, condicion=None):
        self._ejemplares = ejemplares
        self._condicion = condicion or (lambda ejemplar: True)
        self._posicion = 0

    def __iter__(self):
        return self

    def __next__(self):
        while self._posicion < len(self._ejemplares):
            ejemplar = self._ejemplares[self._posicion]
            self._posicion += 1
            if self._condicion(ejemplar):
                return ejemplar
        raise StopIteration


class CatalogoEjemplares:
    """Colección de ejemplares que se recorre con iteradores, sin exponer la lista interna."""

    def __init__(self, ejemplares):
        self._ejemplares = list(ejemplares)

    def __iter__(self):
        """Recorre todos los ejemplares."""
        return IteradorEjemplares(self._ejemplares)

    def por_sede(self, id_sede):
        return IteradorEjemplares(self._ejemplares, lambda e: e.sede_id == id_sede)

    def por_libro(self, id_libro):
        return IteradorEjemplares(self._ejemplares, lambda e: e.libro_id == id_libro)

    def disponibles(self, id_sede=None):
        """Recorre los ejemplares disponibles, opcionalmente solo los de una sede."""
        return IteradorEjemplares(
            self._ejemplares,
            lambda e: e.estado == EstadoEjemplar.DISPONIBLE and (id_sede is None or e.sede_id == id_sede),
        )

    def en_circulacion(self, id_sede=None):
        """Recorre los ejemplares que siguen formando parte del inventario (no dados de baja ni extraviados)."""
        fuera = (EstadoEjemplar.BAJA, EstadoEjemplar.EXTRAVIADO)
        return IteradorEjemplares(
            self._ejemplares,
            lambda e: e.estado not in fuera and (id_sede is None or e.sede_id == id_sede),
        )
