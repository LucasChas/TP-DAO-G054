"""Tests de préstamos locales e interbibliotecarios y de sus validaciones."""
from datetime import date, timedelta

import pytest

from biblioteca.excepciones import (
    DatoInvalido,
    EjemplarDeOtraSede,
    EjemplarNoDisponible,
    OperacionNoPermitida,
    SedeDadaDeBaja,
    SocioConPrestamosVencidos,
    SocioInhabilitado,
)
from biblioteca.modelos.enumeraciones import EstadoEjemplar, EstadoPrestamo, TipoPrestamo
from biblioteca.servicios import ServicioCatalogo, ServicioPrestamos, ServicioSedes, ServicioSocios

HOY = date(2026, 10, 14)


@pytest.fixture
def servicio():
    return ServicioPrestamos()


def estado_del_ejemplar(ejemplar):
    return ServicioCatalogo().listar_ejemplares(id_sede=ejemplar.sede_id)[0].estado


class TestPrestamoLocal:
    def test_se_presta_un_ejemplar_disponible_a_un_socio_habilitado(self, servicio, red):
        prestamo = servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)
        assert prestamo.tipo == TipoPrestamo.LOCAL
        assert prestamo.estado == EstadoPrestamo.ACTIVO
        assert prestamo.fecha_entrega == HOY
        assert prestamo.fecha_vencimiento == HOY + timedelta(days=14)
        assert estado_del_ejemplar(red.ejemplar_centro) == EstadoEjemplar.PRESTADO

    def test_no_se_presta_un_ejemplar_no_disponible(self, servicio, red):
        servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)
        with pytest.raises(EjemplarNoDisponible):
            servicio.registrar_prestamo_local(red.juan.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)

    def test_no_se_presta_un_ejemplar_dado_de_baja(self, servicio, red):
        ServicioCatalogo().dar_de_baja_ejemplar(red.ejemplar_centro.id)
        with pytest.raises(EjemplarNoDisponible):
            servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)

    def test_no_se_presta_a_socio_inhabilitado(self, servicio, red):
        ServicioSocios().inhabilitar_socio(red.ana.id, "Deuda de multas")
        with pytest.raises(SocioInhabilitado):
            servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)

    def test_no_se_presta_un_ejemplar_de_otra_sede(self, servicio, red):
        with pytest.raises(EjemplarDeOtraSede):
            servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_norte.id, red.centro.id, fecha=HOY)

    def test_no_se_presta_en_una_sede_dada_de_baja(self, servicio, red):
        ServicioSedes().dar_de_baja_sede(red.centro.id)
        with pytest.raises(SedeDadaDeBaja):
            servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)

    def test_se_presta_en_una_sede_reactivada(self, servicio, red):
        sedes = ServicioSedes()
        sedes.dar_de_baja_sede(red.centro.id)
        sedes.reactivar_sede(red.centro.id)
        prestamo = servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)
        assert prestamo.estado == EstadoPrestamo.ACTIVO

    def test_no_se_presta_a_socio_con_prestamos_vencidos(self, servicio, red):
        hace_un_mes = HOY - timedelta(days=30)
        servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=hace_un_mes)
        with pytest.raises(SocioConPrestamosVencidos):
            servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_norte.id, red.norte.id, fecha=HOY)

    def test_se_presta_a_socio_con_prestamos_dentro_del_plazo(self, servicio, red):
        servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY - timedelta(days=5))
        prestamo = servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_norte.id, red.norte.id, fecha=HOY)
        assert prestamo.estado == EstadoPrestamo.ACTIVO


class TestPrestamoInterbibliotecario:
    def test_se_solicita_un_prestamo_entre_sedes(self, servicio, red):
        prestamo = servicio.solicitar_prestamo_interbibliotecario(
            red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
        )
        assert prestamo.tipo == TipoPrestamo.INTERBIBLIOTECARIO
        assert prestamo.estado == EstadoPrestamo.SOLICITADO
        assert prestamo.fecha_vencimiento is None
        assert prestamo.sede_origen.nombre == "Sede Norte"
        assert prestamo.sede_destino.nombre == "Sede Centro"
        assert estado_del_ejemplar(red.ejemplar_norte) == EstadoEjemplar.PRESTADO

    def test_no_se_solicita_con_la_misma_sede_de_origen_y_destino(self, servicio, red):
        with pytest.raises(DatoInvalido):
            servicio.solicitar_prestamo_interbibliotecario(
                red.ana.id, red.ejemplar_norte.id, red.norte.id, red.norte.id, fecha=HOY
            )

    def test_no_se_solicita_un_ejemplar_que_no_pertenece_a_la_sede_de_origen(self, servicio, red):
        with pytest.raises(EjemplarDeOtraSede):
            servicio.solicitar_prestamo_interbibliotecario(
                red.ana.id, red.ejemplar_centro.id, red.norte.id, red.centro.id, fecha=HOY
            )

    def test_no_se_solicita_hacia_una_sede_dada_de_baja(self, servicio, red):
        ServicioSedes().dar_de_baja_sede(red.centro.id)
        with pytest.raises(SedeDadaDeBaja):
            servicio.solicitar_prestamo_interbibliotecario(
                red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
            )

    def test_no_se_solicita_desde_una_sede_dada_de_baja(self, servicio, red):
        ServicioSedes().dar_de_baja_sede(red.norte.id)
        with pytest.raises(SedeDadaDeBaja):
            servicio.solicitar_prestamo_interbibliotecario(
                red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
            )

    def test_no_se_solicita_para_un_socio_inhabilitado(self, servicio, red):
        ServicioSocios().inhabilitar_socio(red.ana.id, "Deuda de multas")
        with pytest.raises(SocioInhabilitado):
            servicio.solicitar_prestamo_interbibliotecario(
                red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
            )


class TestCancelacionYConsultas:
    def test_se_cancela_una_solicitud_y_el_ejemplar_vuelve_a_estar_disponible(self, servicio, red):
        prestamo = servicio.solicitar_prestamo_interbibliotecario(
            red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
        )
        assert servicio.cancelar_prestamo(prestamo.id).estado == EstadoPrestamo.CANCELADO
        assert estado_del_ejemplar(red.ejemplar_norte) == EstadoEjemplar.DISPONIBLE

    def test_no_se_cancela_un_prestamo_activo(self, servicio, red):
        prestamo = servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)
        with pytest.raises(OperacionNoPermitida):
            servicio.cancelar_prestamo(prestamo.id)

    def test_se_listan_los_prestamos_vencidos(self, servicio, red):
        servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY - timedelta(days=20))
        servicio.registrar_prestamo_local(red.juan.id, red.ejemplar_norte.id, red.norte.id, fecha=HOY)
        vencidos = servicio.listar_vencidos(fecha=HOY)
        assert [p.socio.dni for p in vencidos] == [red.ana.dni]
        assert vencidos[0].dias_de_atraso_al(HOY) == 6

    def test_se_listan_los_prestamos_por_estado(self, servicio, red):
        servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)
        servicio.solicitar_prestamo_interbibliotecario(red.juan.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY)
        assert len(servicio.listar_prestamos()) == 2
        assert [p.socio.dni for p in servicio.listar_prestamos([EstadoPrestamo.ACTIVO])] == [red.ana.dni]

    def test_se_listan_los_prestamos_de_un_socio(self, servicio, red):
        servicio.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)
        assert len(servicio.listar_prestamos_de_socio(red.ana.id)) == 1
        assert servicio.listar_prestamos_de_socio(red.juan.id) == []
