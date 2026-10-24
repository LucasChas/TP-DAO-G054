"""Tests de devoluciones, multas y su efecto sobre préstamos, ejemplares, reservas y remitos."""
from datetime import date, datetime, timedelta

import pytest

from biblioteca.excepciones import DatoInvalido, OperacionNoPermitida, SocioConMultasImpagas
from biblioteca.modelos.enumeraciones import (
    EstadoEjemplar,
    EstadoFisico,
    EstadoPrestamo,
    EstadoReserva,
    SentidoRemito,
    TipoMaterial,
)
from biblioteca.patrones.estrategias_multa import CalculadoraDeMultas, MultaPorDiasDeAtraso, SinMulta
from biblioteca.servicios import (
    ServicioCatalogo,
    ServicioDevoluciones,
    ServicioPrestamos,
    ServicioRemitos,
    ServicioReservas,
    ServicioSocios,
)

HOY = date(2026, 10, 14)
VENCE = HOY + timedelta(days=14)


@pytest.fixture
def servicio():
    return ServicioDevoluciones()


@pytest.fixture
def prestamos():
    return ServicioPrestamos()


@pytest.fixture
def prestamo_local(prestamos, red):
    return prestamos.registrar_prestamo_local(red.ana.id, red.ejemplar_centro.id, red.centro.id, fecha=HOY)


def ejemplar_actual(ejemplar):
    return next(e for e in ServicioCatalogo().listar_ejemplares() if e.id == ejemplar.id)


class TestDevolucionLocal:
    def test_devolucion_en_termino_sin_multa(self, servicio, prestamos, prestamo_local, red):
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE)
        assert (devolucion.dias_atraso, devolucion.monto_multa, devolucion.multa_pagada) == (0, 0, True)
        assert prestamos.obtener_prestamo(prestamo_local.id).estado == EstadoPrestamo.DEVUELTO
        assert ejemplar_actual(red.ejemplar_centro).estado == EstadoEjemplar.DISPONIBLE

    def test_devolucion_tardia_genera_multa_segun_el_material(self, servicio, prestamo_local):
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE + timedelta(days=3))
        assert devolucion.dias_atraso == 3
        assert devolucion.monto_multa == 1500
        assert not devolucion.multa_pagada

    def test_el_material_de_consulta_tiene_multa_mas_alta(self, servicio, prestamos, red):
        catalogo = ServicioCatalogo()
        diccionario = catalogo.registrar_libro("9789502801334", "Diccionario", "RAE", tipo_material=TipoMaterial.CONSULTA)
        ejemplar = catalogo.registrar_ejemplar(diccionario.id, red.centro.id, "CEN-0100")
        prestamo = prestamos.registrar_prestamo_local(red.ana.id, ejemplar.id, red.centro.id, fecha=HOY)
        devolucion = servicio.registrar_devolucion(prestamo.id, EstadoFisico.BUENO, fecha=VENCE + timedelta(days=3))
        assert devolucion.monto_multa == 3000

    def test_se_registra_el_estado_fisico_y_el_ejemplar_danado_va_a_reparacion(self, servicio, prestamo_local, red):
        servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.DANIADO, "Hojas mojadas", fecha=VENCE)
        ejemplar = ejemplar_actual(red.ejemplar_centro)
        assert (ejemplar.estado, ejemplar.estado_fisico) == (EstadoEjemplar.EN_REPARACION, EstadoFisico.DANIADO)

    def test_devolver_el_material_danado_cobra_un_cargo_fijo(self, servicio, prestamo_local):
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.DANIADO, "Hojas mojadas", fecha=VENCE)
        assert (devolucion.multa_por_atraso, devolucion.cargo_por_danio, devolucion.monto_multa) == (0, 1000, 1000)
        assert devolucion.tiene_multa_impaga

    def test_el_cargo_por_danio_se_suma_a_la_multa_por_atraso(self, servicio, prestamo_local):
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.DANIADO, fecha=VENCE + timedelta(days=3))
        assert (devolucion.multa_por_atraso, devolucion.cargo_por_danio, devolucion.monto_multa) == (1500, 1000, 2500)

    def test_devolver_en_estado_regular_no_tiene_cargo(self, servicio, prestamo_local):
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.REGULAR, fecha=VENCE)
        assert (devolucion.cargo_por_danio, devolucion.monto_multa, devolucion.multa_pagada) == (0, 0, True)

    def test_la_condonacion_no_anula_el_cargo_por_danio(self, prestamo_local):
        servicio = ServicioDevoluciones(CalculadoraDeMultas(SinMulta()))
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.DANIADO, fecha=VENCE + timedelta(days=3))
        assert (devolucion.multa_por_atraso, devolucion.cargo_por_danio) == (0, 1000)

    def test_el_cargo_por_danio_impago_impide_nuevos_prestamos(self, servicio, prestamos, prestamo_local, red):
        servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.DANIADO, fecha=VENCE)
        with pytest.raises(SocioConMultasImpagas):
            prestamos.registrar_prestamo_local(red.ana.id, red.ejemplar_norte.id, red.norte.id, fecha=VENCE)

    def test_el_ejemplar_devuelto_se_aparta_para_la_reserva_pendiente(self, servicio, prestamos, red):
        # Ana se lleva el único ejemplar de la Sede Norte y Juan lo reserva.
        prestamo = prestamos.registrar_prestamo_local(red.ana.id, red.ejemplar_norte.id, red.norte.id, fecha=HOY)
        reserva = ServicioReservas().reservar(red.juan.id, red.rayuela.id, red.norte.id, fecha=HOY)
        servicio.registrar_devolucion(prestamo.id, EstadoFisico.BUENO, fecha=VENCE)
        assert ServicioReservas().obtener_reserva(reserva.id).estado == EstadoReserva.DISPONIBLE
        assert ejemplar_actual(red.ejemplar_norte).estado == EstadoEjemplar.RESERVADO


class TestValidaciones:
    def test_no_se_devuelve_dos_veces(self, servicio, prestamo_local):
        servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE)
        with pytest.raises(OperacionNoPermitida):
            servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE)

    def test_no_se_devuelve_un_prestamo_no_entregado(self, servicio, prestamos, red):
        solicitud = prestamos.solicitar_prestamo_interbibliotecario(
            red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
        )
        with pytest.raises(OperacionNoPermitida):
            servicio.registrar_devolucion(solicitud.id, EstadoFisico.BUENO)

    def test_la_fecha_de_devolucion_no_puede_ser_anterior_a_la_entrega(self, servicio, prestamo_local):
        with pytest.raises(DatoInvalido):
            servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=HOY - timedelta(days=1))


class TestMultas:
    def test_no_se_presta_a_socio_con_multas_impagas(self, servicio, prestamos, prestamo_local, red):
        servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE + timedelta(days=2))
        with pytest.raises(SocioConMultasImpagas):
            prestamos.registrar_prestamo_local(red.ana.id, red.ejemplar_norte.id, red.norte.id, fecha=VENCE + timedelta(days=2))

    def test_despues_de_pagar_la_multa_se_puede_volver_a_prestar(self, servicio, prestamos, prestamo_local, red):
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE + timedelta(days=2))
        assert servicio.registrar_pago_de_multa(devolucion.id).multa_pagada
        nuevo = prestamos.registrar_prestamo_local(red.ana.id, red.ejemplar_norte.id, red.norte.id, fecha=VENCE + timedelta(days=2))
        assert nuevo.estado == EstadoPrestamo.ACTIVO

    def test_no_se_paga_una_multa_inexistente_o_ya_pagada(self, servicio, prestamo_local):
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE)
        with pytest.raises(OperacionNoPermitida):
            servicio.registrar_pago_de_multa(devolucion.id)

    def test_se_listan_las_multas_impagas_por_socio(self, servicio, prestamos, prestamo_local, red):
        servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE + timedelta(days=1))
        assert len(servicio.listar_multas_impagas(red.ana.id)) == 1
        assert servicio.listar_multas_impagas(red.juan.id) == []

    def test_la_estrategia_se_elige_desde_afuera(self, prestamo_local):
        servicio = ServicioDevoluciones(CalculadoraDeMultas(MultaPorDiasDeAtraso()))
        servicio.cambiar_estrategia_de_multa(SinMulta())
        devolucion = servicio.registrar_devolucion(prestamo_local.id, EstadoFisico.BUENO, fecha=VENCE + timedelta(days=5))
        assert (devolucion.dias_atraso, devolucion.monto_multa, devolucion.multa_pagada) == (5, 0, True)


class TestDevolucionInterbibliotecaria:
    @pytest.fixture
    def prestamo_entregado(self, prestamos, red):
        """Ana retira en la Sede Centro el ejemplar NOR-0001 de la Sede Norte."""
        remitos = ServicioRemitos()
        solicitud = prestamos.solicitar_prestamo_interbibliotecario(
            red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
        )
        ida = remitos.listar_remitos_de_prestamo(solicitud.id)[0]
        remitos.empaquetar(ida.id)
        remitos.despachar(ida.id)
        remitos.recibir(ida.id, EstadoFisico.BUENO)
        return prestamos.entregar_prestamo(solicitud.id, fecha=HOY)

    def test_la_devolucion_genera_el_remito_de_retorno(self, servicio, prestamo_entregado, red):
        servicio.registrar_devolucion(prestamo_entregado.id, EstadoFisico.BUENO, fecha=VENCE)
        retorno = ServicioRemitos().listar_remitos_de_prestamo(prestamo_entregado.id)[-1]
        assert retorno.sentido == SentidoRemito.RETORNO
        assert (retorno.sede_origen.nombre, retorno.sede_destino.nombre) == ("Sede Centro", "Sede Norte")
        assert ejemplar_actual(red.ejemplar_norte).estado == EstadoEjemplar.EN_TRANSITO

    def test_el_ejemplar_vuelve_a_su_sede_al_recibir_el_retorno(self, servicio, prestamo_entregado, red):
        remitos = ServicioRemitos()
        servicio.registrar_devolucion(prestamo_entregado.id, EstadoFisico.BUENO, fecha=VENCE)
        retorno = remitos.listar_remitos_de_prestamo(prestamo_entregado.id)[-1]
        remitos.empaquetar(retorno.id)
        remitos.despachar(retorno.id)
        remitos.recibir(retorno.id, EstadoFisico.BUENO, fecha_hora=datetime(2026, 10, 30, 10, 0))
        ejemplar = ejemplar_actual(red.ejemplar_norte)
        assert (ejemplar.estado, ejemplar.sede.nombre) == (EstadoEjemplar.DISPONIBLE, "Sede Norte")

    def test_lo_devuelto_danado_por_el_socio_vuelve_a_reparacion_sin_incidente_logistico(self, servicio, prestamo_entregado, red):
        from biblioteca.reportes import tasa_de_envios

        remitos = ServicioRemitos()
        devolucion = servicio.registrar_devolucion(prestamo_entregado.id, EstadoFisico.DANIADO, "Hojas mojadas", fecha=VENCE)
        assert devolucion.cargo_por_danio == 1000
        retorno = remitos.listar_remitos_de_prestamo(prestamo_entregado.id)[-1]
        remitos.empaquetar(retorno.id)
        remitos.despachar(retorno.id)
        remitos.recibir(retorno.id, EstadoFisico.DANIADO)
        assert ejemplar_actual(red.ejemplar_norte).estado == EstadoEjemplar.EN_REPARACION
        assert tasa_de_envios.generar().general.con_danio == 0
