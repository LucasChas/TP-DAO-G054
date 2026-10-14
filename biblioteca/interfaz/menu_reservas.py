"""Menú de reservas."""
from biblioteca.interfaz.consola import ejecutar_menu, mostrar_aviso, mostrar_exito, mostrar_tabla, pedir_entero
from biblioteca.interfaz.menu_catalogo import listar_libros
from biblioteca.interfaz.menu_sedes import listar_sedes
from biblioteca.servicios import ServicioReservas

servicio = ServicioReservas()

COLUMNAS = ["Id", "Socio", "Libro", "Sede de retiro", "Fecha", "Ejemplar apartado", "Retirar hasta", "Estado"]


def _filas(reservas):
    return [
        (
            r.id, r.socio.nombre_completo, r.libro.titulo, r.sede.nombre, r.fecha_reserva,
            r.ejemplar.codigo_inventario if r.ejemplar else None, r.fecha_limite_retiro, r.estado.value,
        )
        for r in reservas
    ]


def reservar():
    id_socio = pedir_entero("Id del socio")
    listar_libros()
    id_libro = pedir_entero("Id del libro")
    listar_sedes()
    id_sede = pedir_entero("Id de la sede de retiro")
    reserva = servicio.reservar(id_socio, id_libro, id_sede)
    mostrar_exito(f"Reserva {reserva.id} registrada. Los ejemplares se asignan por orden de llegada.")


def listar_activas():
    mostrar_tabla("Reservas activas", COLUMNAS, _filas(servicio.listar_reservas(solo_activas=True)))


def listar_todas():
    mostrar_tabla("Todas las reservas", COLUMNAS, _filas(servicio.listar_reservas()))


def cancelar_reserva():
    listar_activas()
    servicio.cancelar_reserva(pedir_entero("Id de la reserva a cancelar"))
    mostrar_exito("Reserva cancelada.")


def procesar_vencidas():
    vencidas = servicio.procesar_reservas_vencidas()
    if vencidas:
        mostrar_exito(f"Se vencieron {len(vencidas)} reservas no retiradas a tiempo.")
    else:
        mostrar_aviso("No hay reservas con plazo de retiro vencido.")


def menu_reservas():
    ejecutar_menu("Reservas", [
        ("Reservar libro", reservar),
        ("Listar reservas activas", listar_activas),
        ("Cancelar reserva", cancelar_reserva),
        ("Procesar reservas no retiradas", procesar_vencidas),
        ("Listar todas las reservas", listar_todas),
    ])
