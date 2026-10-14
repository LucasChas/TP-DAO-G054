"""Tests del patrón Strategy de cálculo de multas."""
from datetime import date
import pytest

from biblioteca.modelos import Ejemplar, Libro, Prestamo
from biblioteca.modelos.enumeraciones import EstadoPrestamo, TipoMaterial, TipoPrestamo
from biblioteca.patrones.estrategias_multa import (
    CalculadoraDeMultas,
    MultaPorDiasDeAtraso,
    MultaPorTipoDeMaterial,
    SinMulta,
)


def prestamo_de(tipo_material, vencimiento=date(2026, 10, 1)):
    """Préstamo en memoria (sin guardar) de un ejemplar del tipo de material indicado."""
    ejemplar = Ejemplar(libro=Libro(tipo_material=tipo_material))
    return Prestamo(
        tipo=TipoPrestamo.LOCAL, estado=EstadoPrestamo.ACTIVO, fecha_vencimiento=vencimiento, ejemplar=ejemplar
    )


class TestEstrategias:
    @pytest.mark.parametrize("tipo", list(TipoMaterial))
    def test_por_dias_de_atraso_no_depende_del_material(self, tipo):
        assert MultaPorDiasDeAtraso().calcular(4, tipo) == 2000

    @pytest.mark.parametrize("tipo, esperado", [
        (TipoMaterial.LIBRO, 1500),
        (TipoMaterial.REVISTA, 900),
        (TipoMaterial.CONSULTA, 3000),
    ])
    def test_por_tipo_de_material(self, tipo, esperado):
        assert MultaPorTipoDeMaterial().calcular(3, tipo) == esperado

    def test_sin_multa_siempre_es_cero(self):
        assert SinMulta().calcular(30, TipoMaterial.CONSULTA) == 0

    def test_todas_las_estrategias_tienen_descripcion(self):
        for estrategia in (MultaPorDiasDeAtraso(), MultaPorTipoDeMaterial(), SinMulta()):
            assert estrategia.descripcion


class TestCalculadora:
    def test_devolucion_en_termino_no_tiene_multa(self):
        calculadora = CalculadoraDeMultas(MultaPorTipoDeMaterial())
        assert calculadora.calcular(prestamo_de(TipoMaterial.LIBRO), date(2026, 10, 1)) == (0, 0)

    def test_calcula_dias_y_monto_con_la_estrategia_configurada(self):
        calculadora = CalculadoraDeMultas(MultaPorTipoDeMaterial())
        assert calculadora.calcular(prestamo_de(TipoMaterial.CONSULTA), date(2026, 10, 3)) == (2, 2000)

    def test_se_puede_cambiar_la_estrategia(self):
        calculadora = CalculadoraDeMultas(MultaPorTipoDeMaterial())
        calculadora.cambiar_estrategia(SinMulta())
        assert isinstance(calculadora.estrategia, SinMulta)
        assert calculadora.calcular(prestamo_de(TipoMaterial.CONSULTA), date(2026, 10, 3)) == (2, 0)
