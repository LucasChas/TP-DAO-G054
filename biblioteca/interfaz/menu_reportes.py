"""Menú de reportes."""
from biblioteca.interfaz import menu_devoluciones
from biblioteca.interfaz.consola import (
    consola,
    ejecutar_menu,
    mostrar_error,
    mostrar_exito,
    mostrar_tabla,
    pedir_entero,
    pedir_fecha,
)
from biblioteca.reportes import (
    exportacion,
    libros_mas_solicitados,
    movimiento_entre_sedes,
    prestamos_activos_y_transito,
    prestamos_vencidos_y_multas,
    tasa_de_envios,
)
from biblioteca.reportes.armado import REPORTES


def _pesos(monto):
    return f"${monto:,.2f}"


def _horas(horas):
    return "-" if horas is None else f"{horas:.1f} h"


def _porcentaje(valor):
    return "-" if valor is None else f"{valor:.1f} %"


def _pedir_rango():
    consola.print("Rango de fechas opcional (deje vacío para no filtrar).")
    return pedir_fecha("Desde"), pedir_fecha("Hasta")


def reporte_prestamos_activos():
    reporte = prestamos_activos_y_transito.generar()
    mostrar_tabla(
        "Préstamos en curso",
        ["Id", "Socio", "Libro", "Ejemplar", "Tipo", "Sede de retiro", "Estado", "Vence", "Días restantes"],
        [
            (f.id_prestamo, f.socio, f.libro, f.ejemplar, f.tipo, f.sede_retiro, f.estado,
             f.vencimiento and f"{f.vencimiento:%d/%m/%Y}",
             None if f.dias_restantes is None else (f"[red]{f.dias_restantes}" if f.dias_restantes < 0 else f.dias_restantes))
            for f in reporte.prestamos
        ],
    )
    mostrar_tabla(
        "Material en tránsito",
        ["Remito", "Sentido", "Libro", "Ejemplar", "Origen", "Destino", "Despachado", "Última ubicación", "En viaje"],
        [
            (f.numero, f.sentido, f.libro, f.ejemplar, f.origen, f.destino, f"{f.despachado:%d/%m/%Y %H:%M}",
             f.ultima_ubicacion, _horas(f.horas_en_viaje))
            for f in reporte.en_transito
        ],
    )
    mostrar_tabla(
        "Resumen por sede",
        ["Sede", "Préstamos activos", "Por llegar", "Listos para retiro", "Enviando", "Recibiendo"],
        [
            (f.sede, f.prestamos_activos, f.pendientes_de_llegada, f.listos_para_retiro, f.enviando, f.recibiendo)
            for f in reporte.resumen_por_sede
        ],
    )


def reporte_vencidos_y_multas():
    reporte = prestamos_vencidos_y_multas.generar(calculadora=menu_devoluciones.servicio.calculadora)
    consola.print(f"Política de multas aplicada a los vencidos: {reporte.politica}")
    mostrar_tabla(
        "Préstamos vencidos",
        ["Id", "Socio", "Libro", "Sede de retiro", "Venció", "Días de atraso", "Multa estimada"],
        [
            (f.id_prestamo, f.socio, f.libro, f.sede_retiro, f"{f.vencimiento:%d/%m/%Y}", f.dias_atraso,
             _pesos(f.multa_estimada))
            for f in reporte.vencidos
        ],
    )
    mostrar_tabla(
        "Multas acumuladas por socio",
        ["Socio", "DNI", "Cobrado", "Adeudado", "Estimado (vencidos)", "Total"],
        [
            (f.socio, f.dni, _pesos(f.cobrado), _pesos(f.adeudado), _pesos(f.estimado), _pesos(f.total))
            for f in reporte.multas_por_socio
        ],
    )
    consola.print(f"Total cobrado: {_pesos(reporte.total_cobrado)} - Total a cobrar: {_pesos(reporte.total_adeudado)}")


def reporte_libros_mas_solicitados():
    desde, hasta = _pedir_rango()
    mostrar_tabla(
        "Libros más solicitados para préstamos inter-sedes",
        ["Puesto", "Título", "Autor", "Solicitudes", "Concretadas", "Sedes que lo pidieron"],
        [
            (f.posicion, f.titulo, f.autor, f.solicitudes, f.concretadas, f.sedes_destino)
            for f in libros_mas_solicitados.generar(desde, hasta)
        ],
    )


def reporte_movimiento_entre_sedes():
    desde, hasta = _pedir_rango()
    reporte = movimiento_entre_sedes.generar(desde, hasta)
    mostrar_tabla(
        "Envíos por ruta",
        ["Origen", "Destino", "Envíos", "Recibidos", "Tránsito promedio"],
        [(f.origen, f.destino, f.envios, f.recibidos, _horas(f.horas_promedio)) for f in reporte.rutas],
    )
    mostrar_tabla(
        "Envíos y recepciones por sede",
        ["Sede", "Enviados", "Recibidos"],
        [(f.sede, f.enviados, f.recibidos) for f in reporte.por_sede],
    )
    consola.print(f"Tiempo promedio de tránsito en la red: {_horas(reporte.horas_promedio_general)}")


def reporte_tasa_de_envios():
    reporte = tasa_de_envios.generar()
    columnas = ["Grupo", "Exitosos", "Con daño", "Extraviados", "Anulados", "En curso", "Tasa de éxito"]

    def filas(grupos):
        return [
            (f.grupo, f.exitosos, f.con_danio, f.extraviados, f.anulados, f.en_curso, _porcentaje(f.tasa_exito))
            for f in grupos
        ]

    mostrar_tabla("Tasa de envíos exitosos", columnas, filas([reporte.general] + reporte.por_sentido))
    mostrar_tabla("Por sede de origen", columnas, filas(reporte.por_sede_origen))
    mostrar_tabla(
        "Incidencias",
        ["Remito", "Sentido", "Libro", "Origen", "Destino", "Tipo", "Fecha", "Observación"],
        [
            (f.numero, f.sentido, f.libro, f.origen, f.destino, f.tipo, f"{f.fecha:%d/%m/%Y %H:%M}", f.observacion)
            for f in reporte.incidencias
        ],
    )


def _exportar(formato):
    for numero, (_, titulo, _) in enumerate(REPORTES, start=1):
        consola.print(f"  {numero}. {titulo}")
    numero = pedir_entero("Reporte a exportar")
    if not 1 <= numero <= len(REPORTES):
        mostrar_error("Opción fuera de rango.")
        return
    clave, _, acepta_rango = REPORTES[numero - 1]
    desde, hasta = _pedir_rango() if acepta_rango else (None, None)
    ruta = exportacion.exportar(
        clave, formato, desde=desde, hasta=hasta, calculadora=menu_devoluciones.servicio.calculadora
    )
    mostrar_exito(f"Reporte generado: {ruta.resolve()}")


def exportar_pdf():
    _exportar("pdf")


def exportar_csv():
    _exportar("csv")


def menu_reportes():
    ejecutar_menu("Reportes", [
        ("Préstamos activos y material en tránsito", reporte_prestamos_activos),
        ("Préstamos vencidos y multas acumuladas", reporte_vencidos_y_multas),
        ("Libros más solicitados para préstamos inter-sedes", reporte_libros_mas_solicitados),
        ("Movimiento de ejemplares entre sedes", reporte_movimiento_entre_sedes),
        ("Tasa de envíos exitosos e incidencias", reporte_tasa_de_envios),
        ("Exportar un reporte a PDF (tablas y gráficos)", exportar_pdf),
        ("Exportar un reporte a CSV", exportar_csv),
    ])
