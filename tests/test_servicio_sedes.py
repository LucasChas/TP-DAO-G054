"""Tests de administración de sedes."""
import pytest

from biblioteca.excepciones import DatoInvalido, EntidadDuplicada, EntidadNoEncontrada, OperacionNoPermitida
from biblioteca.modelos.enumeraciones import EstadoSede
from biblioteca.servicios import ServicioSedes


@pytest.fixture
def servicio():
    return ServicioSedes()


class TestAltaYModificacion:
    def test_se_registra_una_sede_activa(self, servicio):
        sede = servicio.registrar_sede("Sede Centro", "Av. Colón 100", email="centro@red.org")
        assert sede.id is not None
        assert sede.estado == EstadoSede.ACTIVA

    def test_no_se_registra_sede_con_nombre_duplicado(self, servicio):
        servicio.registrar_sede("Sede Centro", "Av. Colón 100")
        with pytest.raises(EntidadDuplicada):
            servicio.registrar_sede("sede centro", "Otra dirección 1")

    def test_no_se_registra_sede_sin_direccion(self, servicio):
        with pytest.raises(DatoInvalido):
            servicio.registrar_sede("Sede Centro", "   ")

    def test_no_se_registra_sede_con_email_invalido(self, servicio):
        with pytest.raises(DatoInvalido):
            servicio.registrar_sede("Sede Centro", "Av. Colón 100", email="centro.red.org")

    def test_se_modifican_los_datos_de_contacto(self, servicio):
        sede = servicio.registrar_sede("Sede Centro", "Av. Colón 100")
        servicio.modificar_sede(sede.id, telefono="351-1234567", horario_atencion="Lun a Vie 8 a 20")
        modificada = servicio.obtener_sede(sede.id)
        assert modificada.telefono == "351-1234567"
        assert modificada.horario_atencion == "Lun a Vie 8 a 20"

    def test_no_se_renombra_una_sede_con_el_nombre_de_otra(self, servicio):
        servicio.registrar_sede("Sede Centro", "Av. Colón 100")
        norte = servicio.registrar_sede("Sede Norte", "Av. Cabrera 3000")
        with pytest.raises(EntidadDuplicada):
            servicio.modificar_sede(norte.id, nombre="Sede Centro")

    def test_modificar_una_sede_inexistente_falla(self, servicio):
        with pytest.raises(EntidadNoEncontrada):
            servicio.modificar_sede(999, telefono="123")


class TestBaja:
    def test_se_da_de_baja_una_sede(self, servicio):
        sede = servicio.registrar_sede("Sede Centro", "Av. Colón 100")
        baja = servicio.dar_de_baja_sede(sede.id)
        assert baja.estado == EstadoSede.BAJA
        assert baja.fecha_baja is not None

    def test_no_se_da_de_baja_dos_veces(self, servicio):
        sede = servicio.registrar_sede("Sede Centro", "Av. Colón 100")
        servicio.dar_de_baja_sede(sede.id)
        with pytest.raises(OperacionNoPermitida):
            servicio.dar_de_baja_sede(sede.id)

    def test_se_reactiva_una_sede_dada_de_baja(self, servicio):
        sede = servicio.registrar_sede("Sede Centro", "Av. Colón 100")
        servicio.dar_de_baja_sede(sede.id)
        reactivada = servicio.reactivar_sede(sede.id)
        assert reactivada.esta_activa
        assert reactivada.fecha_baja is None

    def test_listar_solo_activas_excluye_las_dadas_de_baja(self, servicio):
        servicio.registrar_sede("Sede Centro", "Av. Colón 100")
        norte = servicio.registrar_sede("Sede Norte", "Av. Cabrera 3000")
        servicio.dar_de_baja_sede(norte.id)
        assert [s.nombre for s in servicio.listar_sedes(solo_activas=True)] == ["Sede Centro"]
        assert len(servicio.listar_sedes()) == 2
