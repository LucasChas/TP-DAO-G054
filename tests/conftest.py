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
        nuevo = Libro(isbn="9789500000001", titulo="Rayuela", autor="Julio Cortázar")
        sesion.add(nuevo)
    return nuevo


@pytest.fixture
def ejemplar(libro, sede_central):
    with obtener_sesion() as sesion:
        nuevo = Ejemplar(codigo_inventario="CEN-0001", libro_id=libro.id, sede_id=sede_central.id)
        sesion.add(nuevo)
    return nuevo
