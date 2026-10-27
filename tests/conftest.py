"""Fixtures compartidas: cada test trabaja sobre una base SQLite en memoria nueva."""
import pytest

from biblioteca.configuracion.base_de_datos import (
    configurar_base_de_datos,
    crear_tablas,
    eliminar_tablas,
    obtener_sesion,
)
from biblioteca.modelos import Ejemplar, Libro, Sede, Socio


@pytest.fixture(autouse=True)
def base_de_datos():
    """Crea las tablas en una base en memoria antes de cada test y las elimina después."""
    configurar_base_de_datos("sqlite:///:memory:")
    crear_tablas()
    yield
    eliminar_tablas()


@pytest.fixture
def sede_central():
    with obtener_sesion() as sesion:
        sede = Sede(nombre="Sede Central", direccion="Av. Colón 100", telefono="351-4000000")
        sesion.add(sede)
    return sede


@pytest.fixture
def sede_norte():
    with obtener_sesion() as sesion:
        sede = Sede(nombre="Sede Norte", direccion="Av. Monseñor Pablo Cabrera 3000")
        sesion.add(sede)
    return sede


@pytest.fixture
def socio():
    with obtener_sesion() as sesion:
        nuevo = Socio(dni="30111222", nombre="Ana", apellido="Pérez", email="ana@correo.com")
        sesion.add(nuevo)
    return nuevo


@pytest.fixture
def libro():
    with obtener_sesion() as sesion:
        nuevo = Libro(isbn="9789500000000", titulo="Rayuela", autor="Julio Cortázar")
        sesion.add(nuevo)
    return nuevo


@pytest.fixture
def ejemplar(libro, sede_central):
    with obtener_sesion() as sesion:
        nuevo = Ejemplar(codigo_inventario="CEN-0001", libro_id=libro.id, sede_id=sede_central.id)
        sesion.add(nuevo)
    return nuevo


@pytest.fixture
def red():
    """Red de prueba armada con los servicios: dos sedes, dos socios habilitados,
    un libro con un ejemplar en cada sede."""
    from types import SimpleNamespace

    from biblioteca.servicios import ServicioCatalogo, ServicioSedes, ServicioSocios

    sedes = ServicioSedes()
    socios = ServicioSocios()
    catalogo = ServicioCatalogo()
    centro = sedes.registrar_sede("Sede Centro", "Av. Colón 100")
    norte = sedes.registrar_sede("Sede Norte", "Av. Cabrera 3000")
    ana = socios.registrar_socio("30111222", "Ana", "Pérez")
    juan = socios.registrar_socio("28999888", "Juan", "Gómez")
    rayuela = catalogo.registrar_libro("9789500700016", "Rayuela", "Julio Cortázar")
    ejemplar_centro = catalogo.registrar_ejemplar(rayuela.id, centro.id, "CEN-0001")
    ejemplar_norte = catalogo.registrar_ejemplar(rayuela.id, norte.id, "NOR-0001")
    return SimpleNamespace(
        centro=centro, norte=norte, ana=ana, juan=juan, rayuela=rayuela,
        ejemplar_centro=ejemplar_centro, ejemplar_norte=ejemplar_norte,
    )
