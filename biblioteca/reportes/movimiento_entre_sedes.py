"""Reporte 4: movimiento de ejemplares entre sedes.

Agrupa los envíos (remitos despachados) por par sede origen → destino e
informa cuántos se recibieron y el tiempo promedio de tránsito, medido desde
el despacho hasta la recepción. También totaliza envíos y recepciones por sede.
"""
from dataclasses import dataclass, field

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import RemitoDAO, SedeDAO


@dataclass
class FilaRuta:
    origen: str
    destino: str
    envios: int = 0
    recibidos: int = 0
    horas_totales: float = 0.0

    @property
    def horas_promedio(self):
        return round(self.horas_totales / self.recibidos, 1) if self.recibidos else None


@dataclass
class FilaSede:
    sede: str
    enviados: int = 0
    recibidos: int = 0


@dataclass
class ReporteMovimientos:
    rutas: list = field(default_factory=list)
    por_sede: list = field(default_factory=list)

    @property
    def horas_promedio_general(self):
        recibidos = sum(r.recibidos for r in self.rutas)
        horas = sum(r.horas_totales for r in self.rutas)
        return round(horas / recibidos, 1) if recibidos else None


def generar(desde=None, hasta=None):
    """desde y hasta (fechas, inclusive) filtran por fecha de despacho; ambos son opcionales."""
    with obtener_sesion() as sesion:
        remitos = RemitoDAO(sesion).listar()
        sedes = SedeDAO(sesion).listar()

    rutas = {}
    por_sede = {sede.id: FilaSede(sede.nombre) for sede in sedes}
    for remito in remitos:
        despacho = remito.fecha_de("Despachado")
        if despacho is None:
            continue  # nunca salió de la sede (generado, empaquetado o anulado)
        if (desde and despacho.date() < desde) or (hasta and despacho.date() > hasta):
            continue
        clave = (remito.sede_origen_id, remito.sede_destino_id)
        if clave not in rutas:
            rutas[clave] = FilaRuta(remito.sede_origen.nombre, remito.sede_destino.nombre)
        ruta = rutas[clave]
        ruta.envios += 1
        por_sede[remito.sede_origen_id].enviados += 1
        recepcion = remito.fecha_de("Recibido")
        if recepcion is not None:
            ruta.recibidos += 1
            ruta.horas_totales += (recepcion - despacho).total_seconds() / 3600
            por_sede[remito.sede_destino_id].recibidos += 1

    return ReporteMovimientos(
        rutas=sorted(rutas.values(), key=lambda r: (-r.envios, r.origen, r.destino)),
        por_sede=list(por_sede.values()),
    )
