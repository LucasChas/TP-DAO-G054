"""Patrón Strategy para calcular la multa por devolución tardía.

Cada estrategia encapsula una forma de calcular el monto. La calculadora
(contexto) recibe la estrategia desde afuera y la puede cambiar en cualquier
momento, sin que el servicio de devoluciones sepa cuál se está usando. A
diferencia del State, la estrategia no la elige el propio objeto sino quien
lo configura.

Además de la multa por atraso, la calculadora cobra un cargo fijo cuando el socio
devuelve dañado un material que se le prestó sano: la reparación es un gasto
para la biblioteca. Ese cargo no depende de la estrategia elegida, así que una
condonación de multas por atraso no lo anula.

Los montos están en pesos y se definen solo acá.
"""
from abc import ABC, abstractmethod

from biblioteca.modelos.enumeraciones import EstadoFisico, TipoMaterial


class EstrategiaMulta(ABC):
    """Calcula el monto de la multa a partir de los días de atraso y del material."""

    @property
    @abstractmethod
    def descripcion(self):
        """Texto que se muestra al usuario para identificar la política."""

    @abstractmethod
    def calcular(self, dias_atraso, tipo_material):
        """Devuelve el monto en pesos. Con cero días de atraso el monto siempre es cero."""


class MultaPorDiasDeAtraso(EstrategiaMulta):
    """Un monto fijo por cada día de atraso, sin importar el material."""

    MONTO_DIARIO = 500.0

    @property
    def descripcion(self):
        return f"Por días de atraso (${self.MONTO_DIARIO:.0f} por día)"

    def calcular(self, dias_atraso, tipo_material):
        return dias_atraso * self.MONTO_DIARIO


class MultaPorTipoDeMaterial(EstrategiaMulta):
    """El monto diario depende del material. El de consulta es el más caro porque
    es el más demandado y el que tiene menos copias."""

    MONTOS_DIARIOS = {
        TipoMaterial.LIBRO: 500.0,
        TipoMaterial.REVISTA: 300.0,
        TipoMaterial.CONSULTA: 1000.0,
    }

    @property
    def descripcion(self):
        detalle = ", ".join(f"{tipo.value} ${monto:.0f}" for tipo, monto in self.MONTOS_DIARIOS.items())
        return f"Por tipo de material ({detalle} por día)"

    def calcular(self, dias_atraso, tipo_material):
        return dias_atraso * self.MONTOS_DIARIOS[tipo_material]


class SinMulta(EstrategiaMulta):
    """No se cobra multa, por ejemplo durante una condonación."""

    @property
    def descripcion(self):
        return "Sin multa (condonación)"

    def calcular(self, dias_atraso, tipo_material):
        return 0.0


class CalculadoraDeMultas:
    """Contexto del patrón: delega el cálculo en la estrategia configurada."""

    CARGO_POR_DANIO = 1000.0

    def __init__(self, estrategia):
        self._estrategia = estrategia

    @property
    def estrategia(self):
        return self._estrategia

    def cambiar_estrategia(self, estrategia):
        self._estrategia = estrategia

    def calcular(self, prestamo, fecha_devolucion):
        """Devuelve (días de atraso, monto) para un préstamo devuelto en la fecha indicada."""
        dias_atraso = prestamo.dias_de_atraso_al(fecha_devolucion)
        monto = self._estrategia.calcular(dias_atraso, prestamo.ejemplar.libro.tipo_material) if dias_atraso else 0.0
        return dias_atraso, monto

    def cargo_por_danio(self, estado_fisico_prestado, estado_fisico_devuelto):
        """Cargo por devolver dañado un material. Solo se cobra el daño nuevo: si ya
        estaba dañado al prestarse, no lo causó el socio."""
        danio_nuevo = estado_fisico_devuelto == EstadoFisico.DANIADO and estado_fisico_prestado != EstadoFisico.DANIADO
        return self.CARGO_POR_DANIO if danio_nuevo else 0.0


ESTRATEGIAS_DISPONIBLES = [MultaPorTipoDeMaterial, MultaPorDiasDeAtraso, SinMulta]


def estrategia_por_defecto():
    return MultaPorTipoDeMaterial()


def estrategia_por_nombre(nombre):
    """Crea la estrategia a partir del nombre de su clase (así se guarda en la base).
    Si el nombre no corresponde a ninguna, usa la estrategia por defecto."""
    for clase in ESTRATEGIAS_DISPONIBLES:
        if clase.__name__ == nombre:
            return clase()
    return estrategia_por_defecto()
