"""Tests de reservas: alta, cola por orden de llegada, cancelación y vencimiento."""
from datetime import date, timedelta

import pytest

from biblioteca.excepciones import (
    EjemplarNoDisponible,
    EntidadDuplicada,
    OperacionNoPermitida,
    SedeDadaDeBaja,
    SocioInhabilitado,
)
from biblioteca.modelos.enumeraciones import EstadoEjemplar, EstadoPrestamo, EstadoReserva
from biblioteca.servicios import ServicioCatalogo, ServicioPrestamos, ServicioReservas, ServicioSedes, ServicioSocios

HOY = date(2026, 10, 14)


@pytest.fixture
def servicio():
    return ServicioReservas()


@pytest.fixture
def prestamos():
    return ServicioPrestamos()


@pytest.fixture
def ejemplar_centro_ocupado(red):
    """Un tercer socio pide el único ejemplar de la Sede Centro como préstamo interbibliotecario
    hacia la Sede Norte; la solicitud se puede cancelar para liberar el ejemplar."""
    maria = ServicioSocios().registrar_socio("35444555", "María", "López")
    return ServicioPrestamos().solicitar_prestamo_interbibliotecario(
        maria.id, red.ejemplar_centro.id, red.centro.id, red.norte.id, fecha=HOY
    )


def estado_del_ejemplar(id_sede):
    return ServicioCatalogo().listar_ejemplares(id_sede=id_sede)[0].estado


class TestAltaDeReserva:
    def test_se_reserva_un_libro_sin_ejemplares_disponibles_en_la_sede(self, servicio, red, ejemplar_centro_ocupado):
        reserva = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        assert reserva.estado == EstadoReserva.PENDIENTE
        assert reserva.ejemplar is None

    def test_no_se_reserva_si_hay_ejemplares_disponibles(self, servicio, red):
        with pytest.raises(OperacionNoPermitida, match="disponibles"):
            servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)

    def test_no_se_reserva_en_una_sede_sin_ejemplares_del_libro(self, servicio, red):
        sur = ServicioSedes().registrar_sede("Sede Sur", "Av. Vélez Sarsfield 500")
        with pytest.raises(OperacionNoPermitida, match="interbibliotecario"):
            servicio.reservar(red.ana.id, red.rayuela.id, sur.id, fecha=HOY)

    def test_no_se_reserva_para_un_socio_inhabilitado(self, servicio, red, ejemplar_centro_ocupado):
        ServicioSocios().inhabilitar_socio(red.ana.id, "Deuda de multas")
        with pytest.raises(SocioInhabilitado):
            servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)

    def test_no_se_reserva_en_una_sede_dada_de_baja(self, servicio, red, ejemplar_centro_ocupado):
        ServicioSedes().dar_de_baja_sede(red.centro.id)
        with pytest.raises(SedeDadaDeBaja):
            servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)

    def test_no_se_reserva_dos_veces_el_mismo_libro(self, servicio, red, ejemplar_centro_ocupado):
        servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        with pytest.raises(EntidadDuplicada):
            servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)


class TestAsignacionDeEjemplares:
    def test_el_ejemplar_liberado_se_asigna_a_la_reserva_mas_antigua(self, servicio, prestamos, red, ejemplar_centro_ocupado):
        primera = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        segunda = servicio.reservar(red.juan.id, red.rayuela.id, red.centro.id, fecha=HOY + timedelta(days=1))
        prestamos.cancelar_prestamo(ejemplar_centro_ocupado.id, fecha=HOY + timedelta(days=2))

        asignada = servicio.obtener_reserva(primera.id)
        assert asignada.estado == EstadoReserva.DISPONIBLE
        assert asignada.ejemplar.codigo_inventario == "CEN-0001"
        assert asignada.fecha_limite_retiro == HOY + timedelta(days=5)
        assert servicio.obtener_reserva(segunda.id).estado == EstadoReserva.PENDIENTE
        assert estado_del_ejemplar(red.centro.id) == EstadoEjemplar.RESERVADO

    def test_el_titular_de_la_reserva_retira_el_ejemplar_apartado(self, servicio, prestamos, red, ejemplar_centro_ocupado):
        reserva = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        prestamos.cancelar_prestamo(ejemplar_centro_ocupado.id, fecha=HOY)
        prestamo = prestamos.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)
        assert prestamo.estado == EstadoPrestamo.ACTIVO
        assert servicio.obtener_reserva(reserva.id).estado == EstadoReserva.CUMPLIDA

    def test_otro_socio_no_puede_llevarse_un_ejemplar_apartado(self, servicio, prestamos, red, ejemplar_centro_ocupado):
        servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        prestamos.cancelar_prestamo(ejemplar_centro_ocupado.id, fecha=HOY)
        with pytest.raises(EjemplarNoDisponible, match="reserva"):
            prestamos.registrar_prestamo_local(red.juan.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)


class TestCancelacionYVencimiento:
    def test_se_cancela_una_reserva_pendiente(self, servicio, red, ejemplar_centro_ocupado):
        reserva = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        assert servicio.cancelar_reserva(reserva.id).estado == EstadoReserva.CANCELADA

    def test_al_cancelar_una_reserva_disponible_el_ejemplar_pasa_a_la_siguiente(self, servicio, prestamos, red, ejemplar_centro_ocupado):
        primera = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        segunda = servicio.reservar(red.juan.id, red.rayuela.id, red.centro.id, fecha=HOY)
        prestamos.cancelar_prestamo(ejemplar_centro_ocupado.id, fecha=HOY)
        servicio.cancelar_reserva(primera.id, fecha=HOY)
        assert servicio.obtener_reserva(segunda.id).estado == EstadoReserva.DISPONIBLE

    def test_no_se_cancela_una_reserva_ya_cancelada(self, servicio, red, ejemplar_centro_ocupado):
        reserva = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        servicio.cancelar_reserva(reserva.id)
        with pytest.raises(OperacionNoPermitida):
            servicio.cancelar_reserva(reserva.id)

    def test_vence_la_reserva_no_retirada_y_el_ejemplar_queda_disponible(self, servicio, prestamos, red, ejemplar_centro_ocupado):
        reserva = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        prestamos.cancelar_prestamo(ejemplar_centro_ocupado.id, fecha=HOY)
        vencidas = servicio.procesar_reservas_vencidas(fecha=HOY + timedelta(days=4))
        assert [r.id for r in vencidas] == [reserva.id]
        assert servicio.obtener_reserva(reserva.id).estado == EstadoReserva.VENCIDA
        assert estado_del_ejemplar(red.centro.id) == EstadoEjemplar.DISPONIBLE

    def test_no_vence_una_reserva_dentro_del_plazo_de_retiro(self, servicio, prestamos, red, ejemplar_centro_ocupado):
        reserva = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
        prestamos.cancelar_prestamo(ejemplar_centro_ocupado.id, fecha=HOY)
        assert servicio.procesar_reservas_vencidas(fecha=HOY + timedelta(days=3)) == []
        assert servicio.obtener_reserva(reserva.id).estado == EstadoReserva.DISPONIBLE


def test_las_reservas_activas_excluyen_las_canceladas(red, ejemplar_centro_ocupado):
    servicio = ServicioReservas()
    primera = servicio.reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=HOY)
    servicio.reservar(red.juan.id, red.rayuela.id, red.centro.id, fecha=HOY)
    servicio.cancelar_reserva(primera.id)
    assert [r.socio.dni for r in servicio.listar_reservas(solo_activas=True)] == [red.juan.dni]
    assert len(servicio.listar_reservas()) == 2
