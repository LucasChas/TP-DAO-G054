"""Reporte 1: préstamos en curso y material en tránsito, con un resumen por sede."""
from dataclasses import dataclass, field
from datetime import date, datetime

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import PrestamoDAO, RemitoDAO, SedeDAO
from biblioteca.modelos.enumeraciones import EstadoPrestamo

ESTADOS_EN_CURSO = [
    EstadoPrestamo.SOLICITADO,
    EstadoPrestamo.EN_ENVIO,
    EstadoPrestamo.LISTO_PARA_RETIRO,
    EstadoPrestamo.ACTIVO,
]
ESTADOS_EN_VIAJE = ["Despachado", "EnTransito"]


@dataclass
class FilaPrestamoEnCurso:
    id_prestamo: int
    socio: str
    libro: str
    ejemplar: str
    tipo: str
    sede_retiro: str
    estado: str
    vencimiento: date | None
    dias_restantes: int | None  # negativo si ya venció


@dataclass
class FilaEnTransito:
    numero: str
    sentido: str
    libro: str
    ejemplar: str
    origen: str
    destino: str
    despachado: datetime
    ultima_ubicacion: str | None
    horas_en_viaje: float


@dataclass
class ResumenSede:
    sede: str
    prestamos_activos: int = 0
    pendientes_de_llegada: int = 0
    listos_para_retiro: int = 0
    enviando: int = 0
    recibiendo: int = 0


@dataclass
class ReportePrestamosActivos:
    fecha: datetime
    prestamos: list = field(default_factory=list)
    en_transito: list = field(default_factory=list)
    resumen_por_sede: list = field(default_factory=list)


def generar(ahora=None):
    ahora = ahora or datetime.now()
    hoy = ahora.date()
    with obtener_sesion() as sesion:
        prestamos = PrestamoDAO(sesion).listar_por_vencimiento(ESTADOS_EN_CURSO)
        remitos = RemitoDAO(sesion).listar(ESTADOS_EN_VIAJE)
        sedes = SedeDAO(sesion).listar()

    reporte = ReportePrestamosActivos(fecha=ahora)
    resumen = {sede.id: ResumenSede(sede.nombre) for sede in sedes}

    for p in prestamos:
        dias = (p.fecha_vencimiento - hoy).days if p.fecha_vencimiento else None
        reporte.prestamos.append(FilaPrestamoEnCurso(
            p.id, p.socio.nombre_completo, p.ejemplar.libro.titulo, p.ejemplar.codigo_inventario,
            p.tipo.value, p.sede_destino.nombre, p.estado.value, p.fecha_vencimiento, dias,
        ))
        fila = resumen[p.sede_destino_id]
        if p.estado == EstadoPrestamo.ACTIVO:
            fila.prestamos_activos += 1
        elif p.estado == EstadoPrestamo.LISTO_PARA_RETIRO:
            fila.listos_para_retiro += 1
        else:
            fila.pendientes_de_llegada += 1

    for r in remitos:
        despachado = r.fecha_de("Despachado")
        reporte.en_transito.append(FilaEnTransito(
            r.numero, r.sentido.value, r.ejemplar.libro.titulo, r.ejemplar.codigo_inventario,
            r.sede_origen.nombre, r.sede_destino.nombre, despachado, r.ultima_ubicacion,
            round((ahora - despachado).total_seconds() / 3600, 1),
        ))
        resumen[r.sede_origen_id].enviando += 1
        resumen[r.sede_destino_id].recibiendo += 1

    reporte.resumen_por_sede = list(resumen.values())
    return reporte
