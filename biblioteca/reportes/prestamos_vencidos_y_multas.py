"""Reporte 2: préstamos vencidos y multas acumuladas por socio.

Para cada socio se informa lo cobrado y lo adeudado por devoluciones ya
registradas, más la multa estimada de los préstamos vencidos que todavía no
se devolvieron, calculada con la política de multas vigente a la fecha.
"""
from dataclasses import dataclass, field
from datetime import date

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import DevolucionDAO, PrestamoDAO
from biblioteca.patrones.estrategias_multa import CalculadoraDeMultas
from biblioteca.servicios.servicio_devoluciones import estrategia_guardada


@dataclass
class FilaVencido:
    id_prestamo: int
    socio: str
    libro: str
    sede_retiro: str
    vencimiento: date
    dias_atraso: int
    multa_estimada: float


@dataclass
class FilaMultasSocio:
    socio: str
    dni: str
    cobrado: float = 0.0
    adeudado: float = 0.0
    estimado: float = 0.0

    @property
    def total(self):
        return self.cobrado + self.adeudado + self.estimado


@dataclass
class ReporteVencidosYMultas:
    fecha: date
    politica: str
    vencidos: list = field(default_factory=list)
    multas_por_socio: list = field(default_factory=list)

    @property
    def total_adeudado(self):
        return sum(f.adeudado + f.estimado for f in self.multas_por_socio)

    @property
    def total_cobrado(self):
        return sum(f.cobrado for f in self.multas_por_socio)


def generar(fecha=None, calculadora=None):
    fecha = fecha or date.today()
    calculadora = calculadora or CalculadoraDeMultas(estrategia_guardada())
    with obtener_sesion() as sesion:
        vencidos = PrestamoDAO(sesion).listar_vencidos_al(fecha)
        con_multa = DevolucionDAO(sesion).listar_con_multa()

    reporte = ReporteVencidosYMultas(fecha=fecha, politica=calculadora.estrategia.descripcion)
    por_socio = {}

    def fila_de(socio):
        if socio.id not in por_socio:
            por_socio[socio.id] = FilaMultasSocio(socio.nombre_completo, socio.dni)
        return por_socio[socio.id]

    for p in vencidos:
        dias, monto = calculadora.calcular(p, fecha)
        reporte.vencidos.append(FilaVencido(
            p.id, p.socio.nombre_completo, p.ejemplar.libro.titulo, p.sede_destino.nombre,
            p.fecha_vencimiento, dias, monto,
        ))
        fila_de(p.socio).estimado += monto

    for d in con_multa:
        fila = fila_de(d.prestamo.socio)
        if d.multa_pagada:
            fila.cobrado += d.monto_multa
        else:
            fila.adeudado += d.monto_multa

    reporte.multas_por_socio = sorted(por_socio.values(), key=lambda f: (-f.total, f.socio))
    return reporte
