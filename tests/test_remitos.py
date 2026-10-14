"""Tests del ciclo de vida del remito (patrón State) y de sus consecuencias
sobre el préstamo y el ejemplar."""
from datetime import date, datetime, timedelta

import pytest

from biblioteca.excepciones import (
    DatoInvalido,
    OperacionNoPermitida,
    SedeDadaDeBaja,
    SocioInhabilitado,
    TransicionRemitoInvalida,
)
from biblioteca.modelos.enumeraciones import (
    EstadoEjemplar,
    EstadoFisico,
    EstadoPrestamo,
    EstadoReserva,
    SentidoRemito,
)
from biblioteca.patrones.estados_remito import Cerrado, Generado
from biblioteca.servicios import (
    ServicioCatalogo,
    ServicioPrestamos,
    ServicioRemitos,
    ServicioReservas,
    ServicioSedes,
    ServicioSocios,
)

HOY = date(2026, 10, 14)
AHORA = datetime(2026, 10, 14, 9, 0)


@pytest.fixture
def remitos():
    return ServicioRemitos()


@pytest.fixture
def prestamos():
    return ServicioPrestamos()


@pytest.fixture
def solicitud(prestamos, red):
    """Ana pide en la Sede Centro el ejemplar NOR-0001 de la Sede Norte."""
    return prestamos.solicitar_prestamo_interbibliotecario(
        red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY
    )


@pytest.fixture
def remito_ida(remitos, solicitud):
    return remitos.listar_remitos_de_prestamo(solicitud.id)[0]


def despachado(remitos, remito):
    remitos.empaquetar(remito.id, fecha_hora=AHORA)
    return remitos.despachar(remito.id, fecha_hora=AHORA + timedelta(hours=2))


def estado_del_ejemplar(ejemplar):
    return next(e for e in ServicioCatalogo().listar_ejemplares() if e.id == ejemplar.id)


def historial(remitos, remito):
    return [m.estado_nuevo for m in remitos.obtener_remito(remito.id).movimientos]


class TestGeneracion:
    def test_la_solicitud_interbibliotecaria_genera_el_remito_de_ida(self, remito_ida, red):
        assert remito_ida.sentido == SentidoRemito.IDA
        assert isinstance(remito_ida.estado, Generado)
        assert remito_ida.sede_origen.nombre == "Sede Norte"
        assert remito_ida.sede_destino.nombre == "Sede Centro"
        assert remito_ida.numero == "R-000001"

    def test_los_remitos_se_numeran_en_forma_correlativa(self, prestamos, remitos, red, remito_ida):
        otra = prestamos.solicitar_prestamo_interbibliotecario(
            red.juan.id, red.ejemplar_centro.id, red.centro.id, red.norte.id, fecha=HOY
        )
        assert remitos.listar_remitos_de_prestamo(otra.id)[0].numero == "R-000002"

    def test_el_estado_se_reconstruye_al_leer_el_remito_de_la_base(self, remitos, remito_ida):
        remitos.empaquetar(remito_ida.id, fecha_hora=AHORA)
        assert remitos.obtener_remito(remito_ida.id).estado.nombre == "Empaquetado"


class TestCircuitoNormal:
    def test_circuito_completo_hasta_la_entrega_al_socio(self, remitos, prestamos, solicitud, remito_ida, red):
        despachado(remitos, remito_ida)
        assert prestamos.obtener_prestamo(solicitud.id).estado == EstadoPrestamo.EN_ENVIO
        assert estado_del_ejemplar(red.ejemplar_norte).estado == EstadoEjemplar.EN_TRANSITO

        remitos.registrar_punto_de_control(remito_ida.id, "Centro de distribución Alta Córdoba", fecha_hora=AHORA + timedelta(hours=3))
        remitos.registrar_punto_de_control(remito_ida.id, "Terminal de ómnibus", fecha_hora=AHORA + timedelta(hours=4))
        remitos.recibir(remito_ida.id, EstadoFisico.BUENO, fecha_hora=AHORA + timedelta(hours=6))
        assert prestamos.obtener_prestamo(solicitud.id).estado == EstadoPrestamo.LISTO_PARA_RETIRO

        entrega = HOY + timedelta(days=1)
        prestamo = prestamos.entregar_prestamo(solicitud.id, fecha=entrega)
        assert prestamo.estado == EstadoPrestamo.ACTIVO
        assert prestamo.fecha_vencimiento == entrega + timedelta(days=14)
        assert isinstance(remitos.obtener_remito(remito_ida.id).estado, Cerrado)
        assert historial(remitos, remito_ida) == [
            "Generado", "Empaquetado", "Despachado", "EnTransito", "EnTransito", "Recibido", "Cerrado",
        ]

    def test_cada_movimiento_guarda_estado_anterior_fecha_y_observacion(self, remitos, remito_ida):
        despachado(remitos, remito_ida)
        remitos.registrar_punto_de_control(remito_ida.id, "Ruta 9 km 20", fecha_hora=AHORA + timedelta(hours=3))
        ultimo = remitos.obtener_remito(remito_ida.id).movimientos[-1]
        assert (ultimo.estado_anterior, ultimo.estado_nuevo) == ("Despachado", "EnTransito")
        assert ultimo.fecha_hora == AHORA + timedelta(hours=3)
        assert ultimo.observacion == "Ruta 9 km 20"

    def test_un_traslado_directo_se_recibe_sin_puntos_de_control(self, remitos, remito_ida):
        despachado(remitos, remito_ida)
        assert remitos.recibir(remito_ida.id, EstadoFisico.BUENO).nombre_estado == "Recibido"

    def test_el_punto_de_control_requiere_ubicacion(self, remitos, remito_ida):
        despachado(remitos, remito_ida)
        with pytest.raises(DatoInvalido):
            remitos.registrar_punto_de_control(remito_ida.id, "  ")


class TestTransicionesInvalidas:
    @pytest.mark.parametrize("accion", [
        lambda s, r: s.despachar(r.id),
        lambda s, r: s.recibir(r.id, EstadoFisico.BUENO),
        lambda s, r: s.registrar_punto_de_control(r.id, "Ruta 9"),
        lambda s, r: s.reportar_extravio(r.id),
        lambda s, r: s.registrar_danio(r.id),
    ])
    def test_acciones_no_permitidas_en_un_remito_generado(self, remitos, remito_ida, accion):
        with pytest.raises(TransicionRemitoInvalida):
            accion(remitos, remito_ida)

    def test_una_transicion_invalida_no_cambia_el_estado_ni_el_historial(self, remitos, remito_ida):
        with pytest.raises(TransicionRemitoInvalida):
            remitos.recibir(remito_ida.id, EstadoFisico.BUENO)
        remito = remitos.obtener_remito(remito_ida.id)
        assert remito.nombre_estado == "Generado"
        assert len(remito.movimientos) == 1

    def test_no_se_anula_un_remito_ya_despachado(self, remitos, remito_ida):
        despachado(remitos, remito_ida)
        with pytest.raises(TransicionRemitoInvalida):
            remitos.anular(remito_ida.id, "El socio desistió")

    def test_no_se_opera_sobre_un_remito_cerrado(self, remitos, prestamos, solicitud, remito_ida):
        despachado(remitos, remito_ida)
        remitos.recibir(remito_ida.id, EstadoFisico.BUENO)
        prestamos.entregar_prestamo(solicitud.id, fecha=HOY)
        with pytest.raises(TransicionRemitoInvalida):
            remitos.registrar_danio(remito_ida.id)

    def test_no_se_despacha_hacia_una_sede_dada_de_baja(self, remitos, remito_ida, red):
        remitos.empaquetar(remito_ida.id)
        ServicioSedes().dar_de_baja_sede(red.centro.id)
        with pytest.raises(SedeDadaDeBaja):
            remitos.despachar(remito_ida.id)
        assert remitos.obtener_remito(remito_ida.id).nombre_estado == "Empaquetado"


class TestAnulacion:
    def test_se_anula_un_remito_empaquetado_y_se_cancela_el_prestamo(self, remitos, prestamos, solicitud, remito_ida, red):
        remitos.empaquetar(remito_ida.id)
        remitos.anular(remito_ida.id, "La sede de destino cierra por refacciones")
        assert remitos.obtener_remito(remito_ida.id).nombre_estado == "Anulado"
        assert prestamos.obtener_prestamo(solicitud.id).estado == EstadoPrestamo.CANCELADO
        assert estado_del_ejemplar(red.ejemplar_norte).estado == EstadoEjemplar.DISPONIBLE

    def test_no_se_anula_sin_motivo(self, remitos, remito_ida):
        with pytest.raises(DatoInvalido):
            remitos.anular(remito_ida.id, "")

    def test_cancelar_la_solicitud_anula_su_remito(self, remitos, prestamos, solicitud, remito_ida):
        prestamos.cancelar_prestamo(solicitud.id)
        assert remitos.obtener_remito(remito_ida.id).nombre_estado == "Anulado"

    def test_no_se_cancela_una_solicitud_ya_despachada(self, remitos, prestamos, solicitud, remito_ida):
        despachado(remitos, remito_ida)
        with pytest.raises(OperacionNoPermitida):
            prestamos.cancelar_prestamo(solicitud.id)


class TestIncidencias:
    def test_extravio_en_viaje(self, remitos, prestamos, solicitud, remito_ida, red):
        despachado(remitos, remito_ida)
        remitos.registrar_punto_de_control(remito_ida.id, "Ruta 9 km 20")
        remitos.reportar_extravio(remito_ida.id, "No llegó a destino")
        assert historial(remitos, remito_ida)[-2:] == ["Extraviado", "Cerrado"]
        assert prestamos.obtener_prestamo(solicitud.id).estado == EstadoPrestamo.CANCELADO
        assert estado_del_ejemplar(red.ejemplar_norte).estado == EstadoEjemplar.EXTRAVIADO

    def test_danio_en_la_recepcion_cancela_el_prestamo_y_genera_el_retorno(self, remitos, prestamos, solicitud, remito_ida, red):
        despachado(remitos, remito_ida)
        remitos.recibir(remito_ida.id, EstadoFisico.DANIADO, "Tapa rota")

        assert historial(remitos, remito_ida)[-3:] == ["Recibido", "Daniado", "Cerrado"]
        assert prestamos.obtener_prestamo(solicitud.id).estado == EstadoPrestamo.CANCELADO
        ejemplar = estado_del_ejemplar(red.ejemplar_norte)
        assert (ejemplar.estado, ejemplar.estado_fisico) == (EstadoEjemplar.EN_TRANSITO, EstadoFisico.DANIADO)

        retorno = remitos.listar_remitos_de_prestamo(solicitud.id)[1]
        assert retorno.sentido == SentidoRemito.RETORNO
        assert (retorno.sede_origen.nombre, retorno.sede_destino.nombre) == ("Sede Centro", "Sede Norte")
        assert retorno.nombre_estado == "Generado"

    def test_el_danio_se_puede_registrar_antes_de_que_el_socio_retire(self, remitos, prestamos, solicitud, remito_ida):
        despachado(remitos, remito_ida)
        remitos.recibir(remito_ida.id, EstadoFisico.BUENO)
        remitos.registrar_danio(remito_ida.id, "Páginas sueltas detectadas al entregar")
        assert prestamos.obtener_prestamo(solicitud.id).estado == EstadoPrestamo.CANCELADO
        assert len(remitos.listar_remitos_de_prestamo(solicitud.id)) == 2

    def test_el_ejemplar_danado_llega_a_su_sede_y_queda_en_reparacion(self, remitos, solicitud, remito_ida, red):
        despachado(remitos, remito_ida)
        remitos.recibir(remito_ida.id, EstadoFisico.DANIADO, "Tapa rota")
        retorno = remitos.listar_remitos_de_prestamo(solicitud.id)[1]
        despachado(remitos, retorno)
        remitos.recibir(retorno.id, EstadoFisico.DANIADO)

        assert remitos.obtener_remito(retorno.id).nombre_estado == "Cerrado"
        assert estado_del_ejemplar(red.ejemplar_norte).estado == EstadoEjemplar.EN_REPARACION

        reparado = ServicioCatalogo().finalizar_reparacion(red.ejemplar_norte.id)
        assert (reparado.estado, reparado.estado_fisico) == (EstadoEjemplar.DISPONIBLE, EstadoFisico.REGULAR)

    def test_un_remito_de_retorno_no_se_anula(self, remitos, solicitud, remito_ida):
        despachado(remitos, remito_ida)
        remitos.recibir(remito_ida.id, EstadoFisico.DANIADO)
        retorno = remitos.listar_remitos_de_prestamo(solicitud.id)[1]
        with pytest.raises(TransicionRemitoInvalida):
            remitos.anular(retorno.id, "No hace falta")

    def test_el_retorno_sano_deja_el_ejemplar_disponible_y_atiende_reservas(self, remitos, solicitud, remito_ida, red):
        despachado(remitos, remito_ida)
        remitos.recibir(remito_ida.id, EstadoFisico.DANIADO)
        reserva = ServicioReservas().reservar(red.juan.id, red.rayuela.id, red.norte.id, fecha=HOY)
        retorno = remitos.listar_remitos_de_prestamo(solicitud.id)[1]
        despachado(remitos, retorno)
        remitos.recibir(retorno.id, EstadoFisico.REGULAR, "Se pegó la tapa en destino")

        assert estado_del_ejemplar(red.ejemplar_norte).estado == EstadoEjemplar.RESERVADO
        assert ServicioReservas().obtener_reserva(reserva.id).estado == EstadoReserva.DISPONIBLE


class TestEntrega:
    def test_no_se_entrega_un_prestamo_que_no_llego(self, prestamos, solicitud):
        with pytest.raises(OperacionNoPermitida):
            prestamos.entregar_prestamo(solicitud.id)

    def test_no_se_entrega_a_un_socio_inhabilitado(self, remitos, prestamos, solicitud, remito_ida, red):
        despachado(remitos, remito_ida)
        remitos.recibir(remito_ida.id, EstadoFisico.BUENO)
        ServicioSocios().inhabilitar_socio(red.ana.id, "Deuda de multas")
        with pytest.raises(SocioInhabilitado):
            prestamos.entregar_prestamo(solicitud.id)


def test_se_da_de_baja_un_ejemplar_en_reparacion_sin_arreglo(remitos, solicitud, remito_ida, red):
    despachado(remitos, remito_ida)
    remitos.recibir(remito_ida.id, EstadoFisico.DANIADO)
    retorno = remitos.listar_remitos_de_prestamo(solicitud.id)[1]
    despachado(remitos, retorno)
    remitos.recibir(retorno.id, EstadoFisico.DANIADO)
    assert ServicioCatalogo().dar_de_baja_ejemplar(red.ejemplar_norte.id).estado == EstadoEjemplar.BAJA
