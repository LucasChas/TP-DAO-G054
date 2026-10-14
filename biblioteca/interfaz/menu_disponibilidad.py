"""Consulta de disponibilidad de un libro en toda la red."""
from biblioteca.interfaz.consola import mostrar_tabla, pedir_entero
from biblioteca.interfaz.menu_catalogo import listar_libros
from biblioteca.servicios import ServicioCatalogo, ServicioDisponibilidad


def consultar_disponibilidad():
    listar_libros()
    id_libro = pedir_entero("Id del libro")
    libro = ServicioCatalogo().obtener_libro(id_libro)
    resumen = ServicioDisponibilidad().consultar_disponibilidad(id_libro)
    filas = [
        (
            r.sede if r.sede_activa else f"{r.sede} (baja)", r.total, r.disponibles, r.reservados,
            r.prestados, r.en_transito,
        )
        for r in resumen
    ]
    mostrar_tabla(
        f"Disponibilidad de '{libro.titulo}'",
        ["Sede", "Total", "Disponibles", "Reservados", "Prestados", "En tránsito"],
        filas,
    )
