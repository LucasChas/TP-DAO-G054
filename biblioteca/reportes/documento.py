"""Estructura común de un reporte listo para exportar.

Cada reporte arma un DocumentoReporte con sus tablas y gráficos ya formateados.
Los exportadores (PDF y CSV) solo saben recorrer esta estructura, así que no
dependen de cómo se calculó cada reporte.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Seccion:
    """Una tabla del reporte."""

    titulo: str
    columnas: list
    filas: list


@dataclass
class Grafico:
    """Datos de un gráfico. tipo puede ser "barras", "barras_horizontales" o "torta"."""

    tipo: str
    titulo: str
    etiquetas: list
    valores: list
    eje_valores: str = ""
    enteros: bool = True  # cantidades: el eje muestra solo números enteros

    @property
    def tiene_datos(self):
        return any(valor for valor in self.valores)


@dataclass
class DocumentoReporte:
    titulo: str
    descripcion: str
    secciones: list = field(default_factory=list)
    graficos: list = field(default_factory=list)
    totales: list = field(default_factory=list)
    generado: datetime = field(default_factory=datetime.now)
