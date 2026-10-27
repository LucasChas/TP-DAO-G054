"""Tests de administración de socios."""
import pytest

from biblioteca.excepciones import DatoInvalido, EntidadDuplicada, EntidadNoEncontrada, OperacionNoPermitida
from biblioteca.modelos.enumeraciones import EstadoSocio
from biblioteca.servicios import ServicioSocios


@pytest.fixture
def servicio():
    return ServicioSocios()


class TestAlta:
    def test_se_registra_un_socio_habilitado(self, servicio):
        socio = servicio.registrar_socio("30.111.222", "Ana", "Pérez")
        assert socio.dni == "30111222"
        assert socio.estado == EstadoSocio.HABILITADO

    def test_no_se_registra_socio_con_dni_duplicado(self, servicio):
        servicio.registrar_socio("30111222", "Ana", "Pérez")
        with pytest.raises(EntidadDuplicada):
            servicio.registrar_socio("30.111.222", "Otra", "Persona")

    @pytest.mark.parametrize("dni", ["123", "abc45678", "123456789", ""])
    def test_no_se_registra_socio_con_dni_invalido(self, servicio, dni):
        with pytest.raises(DatoInvalido):
            servicio.registrar_socio(dni, "Ana", "Pérez")

    def test_no_se_registra_socio_sin_apellido(self, servicio):
        with pytest.raises(DatoInvalido):
            servicio.registrar_socio("30111222", "Ana", "")


class TestModificacion:
    def test_se_modifican_los_datos_de_contacto(self, servicio):
        socio = servicio.registrar_socio("30111222", "Ana", "Pérez")
        servicio.modificar_socio(socio.id, email="ana@correo.com", telefono="351-5555555")
        modificado = servicio.obtener_socio(socio.id)
        assert modificado.email == "ana@correo.com"
        assert modificado.telefono == "351-5555555"

    def test_se_busca_un_socio_por_dni(self, servicio):
        socio = servicio.registrar_socio("30111222", "Ana", "Pérez")
        assert servicio.buscar_por_dni("30.111.222").id == socio.id

    def test_buscar_un_dni_inexistente_falla(self, servicio):
        with pytest.raises(EntidadNoEncontrada):
            servicio.buscar_por_dni("40000000")


class TestInhabilitacion:
    def test_se_inhabilita_un_socio_con_motivo(self, servicio):
        socio = servicio.registrar_socio("30111222", "Ana", "Pérez")
        inhabilitado = servicio.inhabilitar_socio(socio.id, "Deuda de multas")
        assert inhabilitado.estado == EstadoSocio.INHABILITADO
        assert inhabilitado.motivo_inhabilitacion == "Deuda de multas"

    def test_no_se_inhabilita_sin_motivo(self, servicio):
        socio = servicio.registrar_socio("30111222", "Ana", "Pérez")
        with pytest.raises(DatoInvalido):
            servicio.inhabilitar_socio(socio.id, "")

    def test_no_se_inhabilita_dos_veces(self, servicio):
        socio = servicio.registrar_socio("30111222", "Ana", "Pérez")
        servicio.inhabilitar_socio(socio.id, "Deuda de multas")
        with pytest.raises(OperacionNoPermitida):
            servicio.inhabilitar_socio(socio.id, "Otro motivo")

    def test_se_vuelve_a_habilitar_un_socio(self, servicio):
        socio = servicio.registrar_socio("30111222", "Ana", "Pérez")
        servicio.inhabilitar_socio(socio.id, "Deuda de multas")
        habilitado = servicio.habilitar_socio(socio.id)
        assert habilitado.esta_habilitado
        assert habilitado.motivo_inhabilitacion is None
