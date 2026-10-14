"""Menú de devoluciones y multas."""
from biblioteca.interfaz.consola import (
    consola,
    ejecutar_menu,
    mostrar_aviso,
    mostrar_exito,
    mostrar_tabla,
    pedir_entero,
    pedir_opcion_enum,
    pedir_texto,
)
from biblioteca.interfaz.menu_prestamos import COLUMNAS as COLUMNAS_PRESTAMOS
from biblioteca.interfaz.menu_prestamos import filas_prestamos
from biblioteca.modelos.enumeraciones import EstadoFisico, EstadoPrestamo
from biblioteca.patrones.estrategias_multa import ESTRATEGIAS_DISPONIBLES
from biblioteca.servicios import ServicioDevoluciones, ServicioPrestamos

servicio = ServicioDevoluciones()

COLUMNAS = ["Id", "Préstamo", "Socio", "Libro", "Fecha", "Estado físico", "Días de atraso", "Multa", "Pagada"]


def _filas(devoluciones):
    return [
        (
            d.id, d.prestamo_id, d.prestamo.socio.nombre_completo, d.prestamo.ejemplar.libro.titulo,
            f"{d.fecha:%d/%m/%Y}", d.estado_fisico.value, d.dias_atraso, f"${d.monto_multa:,.2f}",
            "Sí" if d.multa_pagada else "No",
        )
        for d in devoluciones
    ]


def registrar_devolucion():
    activos = ServicioPrestamos().listar_prestamos([EstadoPrestamo.ACTIVO])
    mostrar_tabla("Préstamos activos", COLUMNAS_PRESTAMOS, filas_prestamos(activos))
    id_prestamo = pedir_entero("Id del préstamo a devolver")
    estado_fisico = pedir_opcion_enum("Estado físico del material devuelto", EstadoFisico)
    observaciones = pedir_texto("Observaciones (opcional)")
    devolucion = servicio.registrar_devolucion(id_prestamo, estado_fisico, observaciones)
    mostrar_exito("Devolución registrada.")
    if devolucion.monto_multa > 0:
        mostrar_aviso(f"{devolucion.dias_atraso} días de atraso: multa de ${devolucion.monto_multa:,.2f}.")
    if devolucion.prestamo.es_interbibliotecario:
        mostrar_aviso("Se generó el remito de retorno a la sede propietaria del ejemplar.")


def listar_multas_impagas():
    mostrar_tabla("Multas impagas", COLUMNAS, _filas(servicio.listar_multas_impagas()))


def registrar_pago():
    listar_multas_impagas()
    devolucion = servicio.registrar_pago_de_multa(pedir_entero("Id de la devolución cuya multa se paga"))
    mostrar_exito(f"Se registró el pago de ${devolucion.monto_multa:,.2f}.")


def listar_devoluciones():
    mostrar_tabla("Devoluciones", COLUMNAS, _filas(servicio.listar_devoluciones()))


def cambiar_politica_de_multas():
    consola.print(f"Política vigente: {servicio.calculadora.estrategia.descripcion}")
    estrategias = [clase() for clase in ESTRATEGIAS_DISPONIBLES]
    for numero, estrategia in enumerate(estrategias, start=1):
        consola.print(f"  {numero}. {estrategia.descripcion}")
    numero = pedir_entero("Nueva política")
    if not 1 <= numero <= len(estrategias):
        mostrar_aviso("Opción fuera de rango; no se cambió la política.")
        return
    servicio.cambiar_estrategia_de_multa(estrategias[numero - 1])
    mostrar_exito(f"Política de multas: {servicio.calculadora.estrategia.descripcion}.")


def menu_devoluciones():
    ejecutar_menu("Devoluciones y multas", [
        ("Registrar devolución", registrar_devolucion),
        ("Listar multas impagas", listar_multas_impagas),
        ("Registrar pago de multa", registrar_pago),
        ("Listar devoluciones", listar_devoluciones),
        ("Cambiar política de multas", cambiar_politica_de_multas),
    ])
