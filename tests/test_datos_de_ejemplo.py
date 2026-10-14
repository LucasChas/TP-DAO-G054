"""Tests de la carga de datos de ejemplo."""
from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo
from biblioteca.servicios import ServicioCatalogo, ServicioSedes, ServicioSocios


def test_se_cargan_los_datos_de_ejemplo_en_una_base_vacia():
    assert cargar_datos_de_ejemplo()
    assert len(ServicioSedes().listar_sedes()) == 3
    assert len(ServicioSocios().listar_socios()) == 4
    assert len(ServicioCatalogo().listar_ejemplares()) == 10


def test_no_se_cargan_dos_veces_los_datos_de_ejemplo():
    cargar_datos_de_ejemplo()
    assert not cargar_datos_de_ejemplo()
    assert len(ServicioSedes().listar_sedes()) == 3
