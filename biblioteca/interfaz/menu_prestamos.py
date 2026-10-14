"""Menú de préstamos locales e interbibliotecarios."""
from biblioteca.interfaz.consola import (
    confirmar,
    ejecutar_menu,
    mostrar_exito,
    mostrar_tabla,
    pedir_entero,
)
from biblioteca.interfaz.menu_catalogo import listar_libros
from biblioteca.interfaz.menu_sedes import listar_sedes
from biblioteca.modelos.enumeraciones import EstadoPrestamo
from biblioteca.servicios import ServicioDisponibilidad, ServicioPrestamos

servicio = ServicioPrestamos()
disponibilidad = ServicioDisponibilidad()

COLUMNAS = ["Id", "Tipo", "Socio", "Ejemplar", "Libro", "Origen", "Destino", "Solicitud", "Vence", "Estado"]


def filas_prestamos(prestamos):
    return [
        (
            p.id, p.tipo.value, p.socio.nombre_completo, p.ejemplar.codigo_inventario, p.ejemplar.libro.titulo,
            p.sede_origen.nombre, p.sede_destino.nombre, p.fecha_solicitud, p.fecha_vencimiento, p.estado.value,
        )
        for p in prestamos
    ]


def _elegir_ejemplar_disponible(id_sede):
    """Muestra los ejemplares disponibles del libro elegido en la sede y pide el id."""
    listar_libros()
    id_libro = pedir_entero("Id del libro")
    filas = [(e.id, e.codigo_inventario, e.libro.titulo) for e in disponibilidad.ejemplares_disponibles(id_libro, id_sede)]
    mostrar_tabla("Ejemplares disponibles en la sede", ["Id", "Código", "Libro"], filas)
    return pedir_entero("Id del ejemplar (puede ser uno apartado por su reserva)")


def registrar_prestamo_local():
    id_socio = pedir_entero("Id del socio")
    listar_sedes()
    id_sede = pedir_entero("Id de la sede")
    id_ejemplar = _elegir_ejemplar_disponible(id_sede)
    prestamo = servicio.registrar_prestamo_local(id_socio, id_ejemplar, id_sede)
    mostrar_exito(f"Préstamo {prestamo.id} registrado. Vence el {prestamo.fecha_vencimiento:%d/%m/%Y}.")


def solicitar_prestamo_interbibliotecario():
    id_socio = pedir_entero("Id del socio")
    listar_sedes()
    id_sede_destino = pedir_entero("Id de la sede donde retira el socio (destino)")
    id_sede_origen = pedir_entero("Id de la sede dueña del ejemplar (origen)")
    id_ejemplar = _elegir_ejemplar_disponible(id_sede_origen)
    prestamo = servicio.solicitar_prestamo_interbibliotecario(id_socio, id_ejemplar, id_sede_origen, id_sede_destino)
    mostrar_exito(f"Solicitud {prestamo.id} registrada. El ejemplar queda comprometido hasta su envío.")


def cancelar_prestamo():
    listar_en_curso()
    id_prestamo = pedir_entero("Id de la solicitud a cancelar")
    if confirmar("¿Confirma la cancelación?"):
        servicio.cancelar_prestamo(id_prestamo)
        mostrar_exito("Solicitud cancelada.")


def listar_en_curso():
    en_curso = [
        EstadoPrestamo.SOLICITADO, EstadoPrestamo.EN_ENVIO, EstadoPrestamo.LISTO_PARA_RETIRO, EstadoPrestamo.ACTIVO
    ]
    mostrar_tabla("Préstamos en curso", COLUMNAS, filas_prestamos(servicio.listar_prestamos(en_curso)))


def listar_todos():
    mostrar_tabla("Todos los préstamos", COLUMNAS, filas_prestamos(servicio.listar_prestamos()))


def listar_de_socio():
    id_socio = pedir_entero("Id del socio")
    mostrar_tabla("Préstamos del socio", COLUMNAS, filas_prestamos(servicio.listar_prestamos_de_socio(id_socio)))


def listar_vencidos():
    mostrar_tabla("Préstamos vencidos", COLUMNAS, filas_prestamos(servicio.listar_vencidos()))


def menu_prestamos():
    ejecutar_menu("Préstamos", [
        ("Registrar préstamo local", registrar_prestamo_local),
        ("Solicitar préstamo interbibliotecario", solicitar_prestamo_interbibliotecario),
        ("Cancelar solicitud no despachada", cancelar_prestamo),
        ("Listar préstamos en curso", listar_en_curso),
        ("Listar préstamos de un socio", listar_de_socio),
        ("Listar préstamos vencidos", listar_vencidos),
        ("Listar todos los préstamos", listar_todos),
    ])
