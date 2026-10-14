"""Tests del patrón Iterator sobre el catálogo de ejemplares."""
from types import SimpleNamespace

import pytest

from biblioteca.modelos.enumeraciones import EstadoEjemplar
from biblioteca.patrones.iterador_catalogo import CatalogoEjemplares, IteradorEjemplares


def ejemplar(codigo, sede_id, libro_id=1, estado=EstadoEjemplar.DISPONIBLE):
    return SimpleNamespace(codigo_inventario=codigo, sede_id=sede_id, libro_id=libro_id, estado=estado)


@pytest.fixture
def catalogo():
    return CatalogoEjemplares([
        ejemplar("A", 1),
        ejemplar("B", 1, estado=EstadoEjemplar.PRESTADO),
        ejemplar("C", 2),
        ejemplar("D", 2, libro_id=2, estado=EstadoEjemplar.BAJA),
        ejemplar("E", 1, libro_id=2, estado=EstadoEjemplar.EXTRAVIADO),
    ])


def codigos(iterador):
    return [e.codigo_inventario for e in iterador]


class TestIteradorCatalogo:
    def test_recorre_todos_los_ejemplares(self, catalogo):
        assert codigos(catalogo) == ["A", "B", "C", "D", "E"]

    def test_filtra_por_sede(self, catalogo):
        assert codigos(catalogo.por_sede(2)) == ["C", "D"]

    def test_filtra_por_libro(self, catalogo):
        assert codigos(catalogo.por_libro(2)) == ["D", "E"]

    def test_filtra_disponibles_de_toda_la_red_y_de_una_sede(self, catalogo):
        assert codigos(catalogo.disponibles()) == ["A", "C"]
        assert codigos(catalogo.disponibles(id_sede=1)) == ["A"]

    def test_en_circulacion_excluye_bajas_y_extraviados(self, catalogo):
        assert codigos(catalogo.en_circulacion()) == ["A", "B", "C"]

    def test_el_iterador_se_agota_y_lanza_stop_iteration(self):
        iterador = IteradorEjemplares([ejemplar("A", 1)])
        assert next(iterador).codigo_inventario == "A"
        with pytest.raises(StopIteration):
            next(iterador)

    def test_cada_recorrido_es_independiente(self, catalogo):
        assert codigos(catalogo.por_sede(1)) == codigos(catalogo.por_sede(1))

    def test_un_catalogo_vacio_no_devuelve_nada(self):
        assert codigos(CatalogoEjemplares([])) == []
