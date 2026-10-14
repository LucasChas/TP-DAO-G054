"""Tests de la consulta de disponibilidad."""
from datetime import date

from biblioteca.servicios import ServicioCatalogo, ServicioDisponibilidad, ServicioPrestamos


def test_la_disponibilidad_se_informa_por_sede(red):
    catalogo = ServicioCatalogo()
    catalogo.registrar_ejemplar(red.rayuela.id, red.centro.id, "CEN-0002")
    baja = catalogo.registrar_ejemplar(red.rayuela.id, red.centro.id, "CEN-0003")
    catalogo.dar_de_baja_ejemplar(baja.id)
    ServicioPrestamos().registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=date(2026, 10, 14))

    resumen = ServicioDisponibilidad().consultar_disponibilidad(red.rayuela.id)

    centro, norte = resumen
    assert (centro.sede, centro.total, centro.disponibles, centro.prestados) == ("Sede Centro", 2, 1, 1)
    assert (norte.sede, norte.total, norte.disponibles) == ("Sede Norte", 1, 1)


def test_un_libro_sin_ejemplares_no_tiene_disponibilidad():
    libro = ServicioCatalogo().registrar_libro("9789875666474", "Ficciones", "Jorge Luis Borges")
    assert ServicioDisponibilidad().consultar_disponibilidad(libro.id) == []


def test_se_listan_los_ejemplares_disponibles_de_una_sede(red):
    disponibles = ServicioDisponibilidad().ejemplares_disponibles(red.rayuela.id, red.norte.id)
    assert [e.codigo_inventario for e in disponibles] == ["NOR-0001"]
