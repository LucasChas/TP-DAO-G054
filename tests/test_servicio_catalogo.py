"""Tests de administración del catálogo: libros y ejemplares."""
import pytest

from biblioteca.excepciones import (
    DatoInvalido,
    EntidadDuplicada,
    EntidadNoEncontrada,
    OperacionNoPermitida,
    SedeDadaDeBaja,
)
from biblioteca.modelos.enumeraciones import EstadoEjemplar, TipoMaterial
from biblioteca.servicios import ServicioCatalogo, ServicioSedes


@pytest.fixture
def servicio():
    return ServicioCatalogo()


@pytest.fixture
def sede():
    return ServicioSedes().registrar_sede("Sede Centro", "Av. Colón 100")


@pytest.fixture
def libro(servicio):
    return servicio.registrar_libro("978-950-07-0001-1", "Rayuela", "Julio Cortázar", anio_publicacion=1963)


class TestLibros:
    def test_se_registra_un_libro_con_isbn_normalizado(self, libro):
        assert libro.isbn == "9789500700011"
        assert libro.tipo_material == TipoMaterial.LIBRO

    def test_no_se_registra_libro_con_isbn_duplicado(self, servicio, libro):
        with pytest.raises(EntidadDuplicada):
            servicio.registrar_libro("9789500700011", "Otro título", "Otro autor")

    @pytest.mark.parametrize("isbn", ["123", "97895007000AB", ""])
    def test_no_se_registra_libro_con_isbn_invalido(self, servicio, isbn):
        with pytest.raises(DatoInvalido):
            servicio.registrar_libro(isbn, "Título", "Autor")

    def test_se_acepta_isbn_10_terminado_en_x(self, servicio):
        assert servicio.registrar_libro("0-306-40615-X", "Título", "Autor").isbn == "030640615X"

    def test_no_se_registra_libro_con_anio_futuro(self, servicio):
        with pytest.raises(DatoInvalido):
            servicio.registrar_libro("9789500700028", "Título", "Autor", anio_publicacion=3000)

    def test_se_modifica_un_libro(self, servicio, libro):
        servicio.modificar_libro(libro.id, editorial="Sudamericana", tipo_material=TipoMaterial.CONSULTA)
        modificado = servicio.obtener_libro(libro.id)
        assert modificado.editorial == "Sudamericana"
        assert modificado.tipo_material == TipoMaterial.CONSULTA

    def test_se_buscan_libros_por_titulo_o_autor(self, servicio, libro):
        servicio.registrar_libro("9789500700028", "Ficciones", "Jorge Luis Borges")
        assert [l.titulo for l in servicio.buscar_libros("cortázar")] == ["Rayuela"]
        assert [l.titulo for l in servicio.buscar_libros("ficc")] == ["Ficciones"]


class TestEjemplares:
    def test_se_registra_un_ejemplar_disponible_en_su_sede(self, servicio, libro, sede):
        ejemplar = servicio.registrar_ejemplar(libro.id, sede.id, "cen-0001")
        assert ejemplar.codigo_inventario == "CEN-0001"
        assert ejemplar.estado == EstadoEjemplar.DISPONIBLE
        assert ejemplar.sede.nombre == "Sede Centro"
        assert ejemplar.libro.titulo == "Rayuela"

    def test_no_se_registra_ejemplar_con_codigo_duplicado(self, servicio, libro, sede):
        servicio.registrar_ejemplar(libro.id, sede.id, "CEN-0001")
        with pytest.raises(EntidadDuplicada):
            servicio.registrar_ejemplar(libro.id, sede.id, "cen-0001")

    def test_no_se_registra_ejemplar_en_sede_dada_de_baja(self, servicio, libro, sede):
        ServicioSedes().dar_de_baja_sede(sede.id)
        with pytest.raises(SedeDadaDeBaja):
            servicio.registrar_ejemplar(libro.id, sede.id, "CEN-0001")

    def test_no_se_registra_ejemplar_de_un_libro_inexistente(self, servicio, sede):
        with pytest.raises(EntidadNoEncontrada):
            servicio.registrar_ejemplar(999, sede.id, "CEN-0001")

    def test_se_listan_ejemplares_por_sede(self, servicio, libro, sede):
        norte = ServicioSedes().registrar_sede("Sede Norte", "Av. Cabrera 3000")
        servicio.registrar_ejemplar(libro.id, sede.id, "CEN-0001")
        servicio.registrar_ejemplar(libro.id, norte.id, "NOR-0001")
        assert [e.codigo_inventario for e in servicio.listar_ejemplares(id_sede=norte.id)] == ["NOR-0001"]
        assert len(servicio.listar_ejemplares(id_libro=libro.id)) == 2

    def test_se_da_de_baja_un_ejemplar_disponible(self, servicio, libro, sede):
        ejemplar = servicio.registrar_ejemplar(libro.id, sede.id, "CEN-0001")
        assert servicio.dar_de_baja_ejemplar(ejemplar.id).estado == EstadoEjemplar.BAJA

    def test_no_se_da_de_baja_un_ejemplar_que_no_esta_disponible(self, servicio, libro, sede):
        ejemplar = servicio.registrar_ejemplar(libro.id, sede.id, "CEN-0001")
        servicio.dar_de_baja_ejemplar(ejemplar.id)
        with pytest.raises(OperacionNoPermitida):
            servicio.dar_de_baja_ejemplar(ejemplar.id)
