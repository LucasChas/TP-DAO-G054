"""Reporte 5: tasa de envíos logísticos exitosos e incidencias.

Se clasifica cada remito según los estados por los que pasó (su historial):
- exitoso: terminó cerrado sin pasar por Daniado ni Extraviado;
- con daño: pasó por Daniado;
- extraviado: pasó por Extraviado;
- anulado: se canceló antes de salir (no cuenta como envío);
- en curso: todavía no terminó.
La tasa de éxito se calcula sobre los envíos terminados.
"""
from dataclasses import dataclass, field

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import RemitoDAO


@dataclass
class FilaTasa:
    grupo: str
    exitosos: int = 0
    con_danio: int = 0
    extraviados: int = 0
    anulados: int = 0
    en_curso: int = 0

    @property
    def terminados(self):
        return self.exitosos + self.con_danio + self.extraviados

    @property
    def tasa_exito(self):
        """Porcentaje de envíos terminados que llegaron sin incidentes, o None si no hay."""
        return round(100 * self.exitosos / self.terminados, 1) if self.terminados else None


@dataclass
class FilaIncidencia:
    numero: str
    sentido: str
    libro: str
    origen: str
    destino: str
    tipo: str
    fecha: object
    observacion: str | None


@dataclass
class ReporteTasaDeEnvios:
    general: FilaTasa
    por_sentido: list = field(default_factory=list)
    por_sede_origen: list = field(default_factory=list)
    incidencias: list = field(default_factory=list)


def _clasificar(remito):
    if remito.paso_por("Daniado"):
        return "con_danio"
    if remito.paso_por("Extraviado"):
        return "extraviados"
    if remito.nombre_estado == "Anulado":
        return "anulados"
    if remito.nombre_estado == "Cerrado":
        return "exitosos"
    return "en_curso"


def generar():
    with obtener_sesion() as sesion:
        remitos = RemitoDAO(sesion).listar()

    general = FilaTasa("Toda la red")
    por_sentido, por_sede = {}, {}
    incidencias = []
    for remito in remitos:
        categoria = _clasificar(remito)
        sentido = por_sentido.setdefault(remito.sentido, FilaTasa(remito.sentido.value))
        sede = por_sede.setdefault(remito.sede_origen_id, FilaTasa(remito.sede_origen.nombre))
        for fila in (general, sentido, sede):
            setattr(fila, categoria, getattr(fila, categoria) + 1)
        if categoria in ("con_danio", "extraviados"):
            estado = "Daniado" if categoria == "con_danio" else "Extraviado"
            movimiento = next(m for m in remito.movimientos if m.estado_nuevo == estado)
            incidencias.append(FilaIncidencia(
                remito.numero, remito.sentido.value, remito.ejemplar.libro.titulo, remito.sede_origen.nombre,
                remito.sede_destino.nombre, "Daño" if categoria == "con_danio" else "Extravío",
                movimiento.fecha_hora, movimiento.observacion,
            ))

    return ReporteTasaDeEnvios(
        general=general,
        por_sentido=list(por_sentido.values()),
        por_sede_origen=sorted(por_sede.values(), key=lambda f: f.grupo),
        incidencias=incidencias,
    )
