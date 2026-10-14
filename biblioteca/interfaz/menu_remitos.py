"""Menú de remitos: empaquetado, despacho, seguimiento y recepción de ejemplares."""
from biblioteca.interfaz.consola import (
    ejecutar_menu,
    mostrar_exito,
    mostrar_tabla,
    pedir_entero,
    pedir_opcion_enum,
    pedir_texto,
)
from biblioteca.modelos.enumeraciones import EstadoFisico
from biblioteca.servicios import ServicioRemitos

servicio = ServicioRemitos()

COLUMNAS = ["Id", "Número", "Sentido", "Ejemplar", "Libro", "Origen", "Destino", "Generado", "Estado"]


def _filas(remitos):
    return [
        (
            r.id, r.numero, r.sentido.value, r.ejemplar.codigo_inventario, r.ejemplar.libro.titulo,
            r.sede_origen.nombre, r.sede_destino.nombre, f"{r.fecha_generacion:%d/%m/%Y %H:%M}", r.nombre_estado,
        )
        for r in remitos
    ]


def listar_en_curso():
    mostrar_tabla("Remitos en curso", COLUMNAS, _filas(servicio.listar_remitos(solo_en_curso=True)))


def listar_todos():
    mostrar_tabla("Todos los remitos", COLUMNAS, _filas(servicio.listar_remitos()))


def ver_trazabilidad():
    remito = servicio.obtener_remito(pedir_entero("Id del remito"))
    filas = [
        (f"{m.fecha_hora:%d/%m/%Y %H:%M}", m.estado_anterior, m.estado_nuevo, m.observacion)
        for m in remito.movimientos
    ]
    mostrar_tabla(
        f"Trayecto del remito {remito.numero} ({remito.sede_origen.nombre} → {remito.sede_destino.nombre})",
        ["Fecha y hora", "Estado anterior", "Estado nuevo", "Observación"],
        filas,
    )


def _pedir_remito():
    listar_en_curso()
    return pedir_entero("Id del remito")


def empaquetar():
    remito = servicio.empaquetar(_pedir_remito(), pedir_texto("Observación (opcional)"))
    mostrar_exito(f"Remito {remito.numero} empaquetado.")


def despachar():
    remito = servicio.despachar(_pedir_remito(), pedir_texto("Observación (opcional)"))
    mostrar_exito(f"Remito {remito.numero} despachado.")


def registrar_punto_de_control():
    id_remito = _pedir_remito()
    remito = servicio.registrar_punto_de_control(id_remito, pedir_texto("Ubicación", obligatorio=True))
    mostrar_exito(f"Punto de control registrado en el remito {remito.numero}.")


def recibir():
    id_remito = _pedir_remito()
    estado_fisico = pedir_opcion_enum("Estado físico del ejemplar recibido", EstadoFisico)
    remito = servicio.recibir(id_remito, estado_fisico, pedir_texto("Observación (opcional)"))
    mostrar_exito(f"Remito {remito.numero} recibido. Estado actual: {remito.nombre_estado}.")


def registrar_danio():
    id_remito = _pedir_remito()
    remito = servicio.registrar_danio(id_remito, pedir_texto("Descripción del daño", obligatorio=True))
    mostrar_exito(f"Daño registrado en el remito {remito.numero}. Se generó el remito de retorno.")


def reportar_extravio():
    id_remito = _pedir_remito()
    remito = servicio.reportar_extravio(id_remito, pedir_texto("Observación", obligatorio=True))
    mostrar_exito(f"Remito {remito.numero} cerrado por extravío.")


def anular():
    id_remito = _pedir_remito()
    remito = servicio.anular(id_remito, pedir_texto("Motivo", obligatorio=True))
    mostrar_exito(f"Remito {remito.numero} anulado y préstamo cancelado.")


def menu_remitos():
    ejecutar_menu("Remitos", [
        ("Listar remitos en curso", listar_en_curso),
        ("Ver trazabilidad de un remito", ver_trazabilidad),
        ("Empaquetar", empaquetar),
        ("Despachar", despachar),
        ("Registrar punto de control", registrar_punto_de_control),
        ("Recibir", recibir),
        ("Registrar daño (antes de entregar)", registrar_danio),
        ("Reportar extravío", reportar_extravio),
        ("Anular (antes de despachar)", anular),
        ("Listar todos los remitos", listar_todos),
    ])
