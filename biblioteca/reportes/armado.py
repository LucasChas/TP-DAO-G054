"""Arma el DocumentoReporte de cada reporte a partir de sus datos calculados."""
from datetime import datetime

from biblioteca.reportes import (
    libros_mas_solicitados,
    movimiento_entre_sedes,
    prestamos_activos_y_transito,
    prestamos_vencidos_y_multas,
    tasa_de_envios,
)
from biblioteca.reportes.documento import DocumentoReporte, Grafico, Seccion


def _fecha(valor, con_hora=False):
    if valor is None:
        return "-"
    return valor.strftime("%d/%m/%Y %H:%M" if con_hora else "%d/%m/%Y")


def _pesos(monto):
    return f"${monto:,.2f}"


def _horas(horas):
    return "-" if horas is None else f"{horas:.1f} h"


def _porcentaje(valor):
    return "-" if valor is None else f"{valor:.1f} %"


def _rango(desde, hasta):
    if desde is None and hasta is None:
        return "Sin filtro de fechas."
    return f"Período: {_fecha(desde) if desde else 'inicio'} a {_fecha(hasta) if hasta else 'hoy'}."


def documento_prestamos_activos(ahora=None):
    reporte = prestamos_activos_y_transito.generar(ahora)
    return DocumentoReporte(
        titulo="Préstamos activos y material en tránsito",
        descripcion="Préstamos en curso (activos y solicitudes interbibliotecarias sin entregar) y envíos que "
                    "salieron de su sede y todavía no llegaron. Los días restantes negativos indican préstamos vencidos.",
        secciones=[
            Seccion("Préstamos en curso",
                    ["Id", "Socio", "Libro", "Ejemplar", "Tipo", "Sede de retiro", "Estado", "Vence", "Días restantes"],
                    [[f.id_prestamo, f.socio, f.libro, f.ejemplar, f.tipo, f.sede_retiro, f.estado,
                      _fecha(f.vencimiento), "-" if f.dias_restantes is None else f.dias_restantes]
                     for f in reporte.prestamos]),
            Seccion("Material en tránsito",
                    ["Remito", "Sentido", "Libro", "Ejemplar", "Origen", "Destino", "Despachado", "Última ubicación", "En viaje"],
                    [[f.numero, f.sentido, f.libro, f.ejemplar, f.origen, f.destino, _fecha(f.despachado, True),
                      f.ultima_ubicacion or "-", _horas(f.horas_en_viaje)] for f in reporte.en_transito]),
            Seccion("Resumen por sede",
                    ["Sede", "Préstamos activos", "Por llegar", "Listos para retiro", "Enviando", "Recibiendo"],
                    [[f.sede, f.prestamos_activos, f.pendientes_de_llegada, f.listos_para_retiro, f.enviando, f.recibiendo]
                     for f in reporte.resumen_por_sede]),
        ],
        graficos=[
            Grafico("barras", "Préstamos activos por sede de retiro",
                    [f.sede for f in reporte.resumen_por_sede],
                    [f.prestamos_activos for f in reporte.resumen_por_sede], "Préstamos"),
        ],
        totales=[f"Préstamos en curso: {len(reporte.prestamos)}", f"Envíos en tránsito: {len(reporte.en_transito)}"],
    )


def documento_vencidos_y_multas(fecha=None, calculadora=None):
    reporte = prestamos_vencidos_y_multas.generar(fecha, calculadora)
    return DocumentoReporte(
        titulo="Préstamos vencidos y multas acumuladas",
        descripcion=f"Préstamos activos con la fecha de vencimiento pasada y multas por socio. "
                    f"La multa estimada de los vencidos se calcula con la política vigente: {reporte.politica}.",
        secciones=[
            Seccion("Préstamos vencidos",
                    ["Id", "Socio", "Libro", "Sede de retiro", "Venció", "Días de atraso", "Multa estimada"],
                    [[f.id_prestamo, f.socio, f.libro, f.sede_retiro, _fecha(f.vencimiento), f.dias_atraso,
                      _pesos(f.multa_estimada)] for f in reporte.vencidos]),
            Seccion("Multas acumuladas por socio",
                    ["Socio", "DNI", "Cobrado", "Adeudado", "Estimado (vencidos)", "Total"],
                    [[f.socio, f.dni, _pesos(f.cobrado), _pesos(f.adeudado), _pesos(f.estimado), _pesos(f.total)]
                     for f in reporte.multas_por_socio]),
        ],
        graficos=[
            Grafico("barras_horizontales", "Multas pendientes por socio (adeudado + estimado)",
                    [f.socio for f in reporte.multas_por_socio],
                    [f.adeudado + f.estimado for f in reporte.multas_por_socio], "Pesos", enteros=False),
        ],
        totales=[f"Total cobrado: {_pesos(reporte.total_cobrado)}", f"Total a cobrar: {_pesos(reporte.total_adeudado)}"],
    )


def documento_libros_mas_solicitados(desde=None, hasta=None):
    filas = libros_mas_solicitados.generar(desde, hasta)
    return DocumentoReporte(
        titulo="Libros más solicitados para préstamos inter-sedes",
        descripcion="Cantidad de solicitudes de préstamo interbibliotecario por libro (incluye las canceladas, porque "
                    "también reflejan demanda) y cuántas se concretaron. Los empates se ordenan por título. "
                    + _rango(desde, hasta),
        secciones=[
            Seccion("Ranking",
                    ["Puesto", "Título", "Autor", "Solicitudes", "Concretadas", "Sedes que lo pidieron"],
                    [[f.posicion, f.titulo, f.autor, f.solicitudes, f.concretadas, f.sedes_destino] for f in filas]),
        ],
        graficos=[
            Grafico("barras_horizontales", "Solicitudes inter-sedes por libro",
                    [f.titulo for f in filas], [f.solicitudes for f in filas], "Solicitudes"),
        ],
        totales=[f"Total de solicitudes: {sum(f.solicitudes for f in filas)}"],
    )


def documento_movimiento_entre_sedes(desde=None, hasta=None):
    reporte = movimiento_entre_sedes.generar(desde, hasta)
    return DocumentoReporte(
        titulo="Movimiento de ejemplares entre sedes",
        descripcion="Envíos despachados por ruta (sede de origen a sede de destino), cuántos se recibieron y el "
                    "tiempo promedio de tránsito entre el despacho y la recepción. " + _rango(desde, hasta),
        secciones=[
            Seccion("Envíos por ruta", ["Origen", "Destino", "Envíos", "Recibidos", "Tránsito promedio"],
                    [[f.origen, f.destino, f.envios, f.recibidos, _horas(f.horas_promedio)] for f in reporte.rutas]),
            Seccion("Envíos y recepciones por sede", ["Sede", "Enviados", "Recibidos"],
                    [[f.sede, f.enviados, f.recibidos] for f in reporte.por_sede]),
        ],
        graficos=[
            Grafico("barras", "Envíos por ruta",
                    [f"{f.origen} → {f.destino}" for f in reporte.rutas], [f.envios for f in reporte.rutas], "Envíos"),
        ],
        totales=[f"Tiempo promedio de tránsito en la red: {_horas(reporte.horas_promedio_general)}"],
    )


def documento_tasa_de_envios():
    reporte = tasa_de_envios.generar()
    columnas = ["Grupo", "Exitosos", "Con daño", "Extraviados", "Anulados", "En curso", "Tasa de éxito"]

    def filas(grupos):
        return [[f.grupo, f.exitosos, f.con_danio, f.extraviados, f.anulados, f.en_curso, _porcentaje(f.tasa_exito)]
                for f in grupos]

    general = reporte.general
    return DocumentoReporte(
        titulo="Tasa de envíos logísticos exitosos e incidencias",
        descripcion="Clasificación de los remitos según los estados de su historial. La tasa de éxito se calcula "
                    "sobre los envíos terminados (exitosos, con daño o extraviados).",
        secciones=[
            Seccion("Toda la red y por sentido", columnas, filas([general] + reporte.por_sentido)),
            Seccion("Por sede de origen", columnas, filas(reporte.por_sede_origen)),
            Seccion("Incidencias", ["Remito", "Sentido", "Libro", "Origen", "Destino", "Tipo", "Fecha", "Observación"],
                    [[f.numero, f.sentido, f.libro, f.origen, f.destino, f.tipo, _fecha(f.fecha, True), f.observacion or "-"]
                     for f in reporte.incidencias]),
        ],
        graficos=[
            Grafico("torta", "Resultado de los envíos terminados", ["Exitosos", "Con daño", "Extraviados"],
                    [general.exitosos, general.con_danio, general.extraviados]),
        ],
        totales=[f"Tasa de éxito de la red: {_porcentaje(general.tasa_exito)}"],
    )


# Catálogo de reportes: clave, título y si acepta rango de fechas.
REPORTES = [
    ("activos", "Préstamos activos y material en tránsito", False),
    ("vencidos", "Préstamos vencidos y multas acumuladas", False),
    ("solicitados", "Libros más solicitados para préstamos inter-sedes", True),
    ("movimientos", "Movimiento de ejemplares entre sedes", True),
    ("tasa", "Tasa de envíos exitosos e incidencias", False),
]


def armar(clave, desde=None, hasta=None, calculadora=None):
    """Arma el documento del reporte indicado por su clave."""
    if clave == "activos":
        return documento_prestamos_activos()
    if clave == "vencidos":
        return documento_vencidos_y_multas(calculadora=calculadora)
    if clave == "solicitados":
        return documento_libros_mas_solicitados(desde, hasta)
    if clave == "movimientos":
        return documento_movimiento_entre_sedes(desde, hasta)
    if clave == "tasa":
        return documento_tasa_de_envios()
    raise ValueError(f"Reporte desconocido: {clave}")


def nombre_de_archivo(clave, extension, momento=None):
    momento = momento or datetime.now()
    return f"reporte_{clave}_{momento:%Y%m%d_%H%M%S}.{extension}"
