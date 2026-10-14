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


def test_los_datos_de_ejemplo_dejan_informacion_para_los_reportes():
    from biblioteca.reportes import movimiento_entre_sedes, prestamos_activos_y_transito, prestamos_vencidos_y_multas, tasa_de_envios

    cargar_datos_de_ejemplo()
    assert len(prestamos_activos_y_transito.generar().en_transito) == 1
    assert len(prestamos_vencidos_y_multas.generar().vencidos) == 1
    assert movimiento_entre_sedes.generar().horas_promedio_general is not None
    assert tasa_de_envios.generar().general.con_danio == 1
