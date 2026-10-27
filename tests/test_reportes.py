"""Tests de los reportes sobre un escenario con fechas controladas.

Escenario (HOY = 14/10/2026):
- Ana pidió Rayuela (NOR-0001) de Norte a Centro: viajó 10 horas, lo retiró
  hace 19 días y venció hace 5 sin devolverlo.
- Juan pidió Rayuela (CEN-0001) de Centro a Norte: está en viaje.
- María pidió Ficciones (SUR-0001) de Sur a Centro y canceló antes del despacho.
- Lucía pidió Rayuela (CEN-0002) de Centro a Sur: se extravió en el camino.
- Pedro devolvió con 2 días de atraso un préstamo local en Sur y no pagó la multa.
"""
from datetime import date, datetime, timedelta

import pytest

from biblioteca.modelos.enumeraciones import EstadoFisico
from biblioteca.patrones.estrategias_multa import CalculadoraDeMultas, SinMulta
from biblioteca.reportes import (
    libros_mas_solicitados,
    movimiento_entre_sedes,
    prestamos_activos_y_transito,
    prestamos_vencidos_y_multas,
    tasa_de_envios,
)
from biblioteca.servicios import (
    ServicioCatalogo,
    ServicioDevoluciones,
    ServicioPrestamos,
    ServicioRemitos,
    ServicioSedes,
    ServicioSocios,
)

HOY = date(2026, 10, 14)
AHORA = datetime(2026, 10, 14, 12, 0)


def dias_atras(dias, hora=9):
    return datetime.combine(HOY - timedelta(days=dias), datetime.min.time()) + timedelta(hours=hora)


@pytest.fixture
def escenario(red):
    prestamos, remitos, catalogo, socios = ServicioPrestamos(), ServicioRemitos(), ServicioCatalogo(), ServicioSocios()
    sur = ServicioSedes().registrar_sede("Sede Sur", "Av. Vélez Sarsfield 500")
    ficciones = catalogo.registrar_libro("9789875666474", "Ficciones", "Jorge Luis Borges")
    sur_ficciones = catalogo.registrar_ejemplar(ficciones.id, sur.id, "SUR-0001")
    sur_rayuela = catalogo.registrar_ejemplar(red.rayuela.id, sur.id, "SUR-0002")
    centro_rayuela_2 = catalogo.registrar_ejemplar(red.rayuela.id, red.centro.id, "CEN-0002")
    maria = socios.registrar_socio("35444555", "María", "López")
    lucia = socios.registrar_socio("36555666", "Lucía", "Fernández")
    pedro = socios.registrar_socio("27888999", "Pedro", "Suárez")

    def remito_de(prestamo):
        return remitos.listar_remitos_de_prestamo(prestamo.id)[0]

    # Ana: Norte -> Centro, recibido tras 10 horas y entregado hace 19 días.
    p_ana = prestamos.solicitar_prestamo_interbibliotecario(red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY - timedelta(days=20))
    r_ana = remito_de(p_ana)
    remitos.empaquetar(r_ana.id, fecha_hora=dias_atras(20, 8))
    remitos.despachar(r_ana.id, fecha_hora=dias_atras(20, 9))
    remitos.recibir(r_ana.id, EstadoFisico.BUENO, fecha_hora=dias_atras(20, 19))
    prestamos.entregar_prestamo(p_ana.id, fecha=HOY - timedelta(days=19))

    # Juan: Centro -> Norte, en viaje.
    p_juan = prestamos.solicitar_prestamo_interbibliotecario(red.juan.id, red.ejemplar_centro.id, red.centro.id, red.norte.id, fecha=HOY - timedelta(days=3))
    r_juan = remito_de(p_juan)
    remitos.empaquetar(r_juan.id, fecha_hora=dias_atras(1, 8))
    remitos.despachar(r_juan.id, fecha_hora=dias_atras(1, 9))
    remitos.registrar_punto_de_control(r_juan.id, "Centro de distribución", fecha_hora=dias_atras(1, 15))

    # María: Sur -> Centro, cancelado antes del despacho.
    p_maria = prestamos.solicitar_prestamo_interbibliotecario(maria.id, sur_ficciones.id, sur.id, red.centro.id, fecha=HOY - timedelta(days=10))
    prestamos.cancelar_prestamo(p_maria.id)

    # Lucía: Centro -> Sur, extraviado.
    p_lucia = prestamos.solicitar_prestamo_interbibliotecario(lucia.id, centro_rayuela_2.id, red.centro.id, sur.id, fecha=HOY - timedelta(days=8))
    r_lucia = remito_de(p_lucia)
    remitos.empaquetar(r_lucia.id, fecha_hora=dias_atras(8, 9))
    remitos.despachar(r_lucia.id, fecha_hora=dias_atras(8, 10))
    remitos.reportar_extravio(r_lucia.id, "No llegó a Sede Sur", fecha_hora=dias_atras(6, 10))

    # Pedro: préstamo local en Sur devuelto con 2 días de atraso, multa impaga.
    p_pedro = prestamos.registrar_prestamo_local(pedro.id, sur_rayuela.id, sur.id, fecha=HOY - timedelta(days=30))
    ServicioDevoluciones().registrar_devolucion(p_pedro.id, EstadoFisico.BUENO, fecha=HOY - timedelta(days=14))

    return red


class TestPrestamosActivosYTransito:
    def test_lista_los_prestamos_en_curso_con_dias_restantes(self, escenario):
        reporte = prestamos_activos_y_transito.generar(AHORA)
        por_socio = {f.socio: f for f in reporte.prestamos}
        assert set(por_socio) == {"Pérez, Ana", "Gómez, Juan"}
        assert por_socio["Pérez, Ana"].dias_restantes == -5
        assert por_socio["Gómez, Juan"].estado == "En envío"

    def test_lista_el_material_en_transito_con_su_ultima_ubicacion(self, escenario):
        (fila,) = prestamos_activos_y_transito.generar(AHORA).en_transito
        assert (fila.ejemplar, fila.origen, fila.destino) == ("CEN-0001", "Sede Centro", "Sede Norte")
        assert fila.ultima_ubicacion == "Centro de distribución"
        assert fila.horas_en_viaje == 27.0

    def test_resume_por_sede(self, escenario):
        resumen = {f.sede: f for f in prestamos_activos_y_transito.generar(AHORA).resumen_por_sede}
        assert resumen["Sede Centro"].prestamos_activos == 1
        assert resumen["Sede Centro"].enviando == 1
        assert resumen["Sede Norte"].pendientes_de_llegada == 1
        assert resumen["Sede Norte"].recibiendo == 1


class TestVencidosYMultas:
    def test_lista_los_vencidos_con_la_multa_estimada(self, escenario):
        (fila,) = prestamos_vencidos_y_multas.generar(HOY).vencidos
        assert (fila.socio, fila.dias_atraso, fila.multa_estimada) == ("Pérez, Ana", 5, 2500)

    def test_acumula_multas_por_socio_ordenadas_por_total(self, escenario):
        reporte = prestamos_vencidos_y_multas.generar(HOY)
        assert [(f.socio, f.adeudado, f.estimado) for f in reporte.multas_por_socio] == [
            ("Pérez, Ana", 0, 2500),
            ("Suárez, Pedro", 1000, 0),
        ]
        assert reporte.total_adeudado == 3500

    def test_usa_la_politica_de_multas_que_recibe(self, escenario):
        reporte = prestamos_vencidos_y_multas.generar(HOY, CalculadoraDeMultas(SinMulta()))
        assert reporte.vencidos[0].multa_estimada == 0
        assert "Sin multa" in reporte.politica


class TestLibrosMasSolicitados:
    def test_ordena_por_cantidad_de_solicitudes(self, escenario):
        filas = libros_mas_solicitados.generar()
        assert [(f.posicion, f.titulo, f.solicitudes, f.concretadas) for f in filas] == [
            (1, "Rayuela", 3, 1),
            (2, "Ficciones", 1, 0),
        ]

    def test_filtra_por_rango_de_fechas(self, escenario):
        filas = libros_mas_solicitados.generar(desde=HOY - timedelta(days=9))
        assert [(f.titulo, f.solicitudes) for f in filas] == [("Rayuela", 2)]

    def test_los_empates_se_ordenan_por_titulo(self, escenario):
        filas = libros_mas_solicitados.generar(desde=HOY - timedelta(days=10), hasta=HOY - timedelta(days=8))
        assert [(f.titulo, f.solicitudes) for f in filas] == [("Ficciones", 1), ("Rayuela", 1)]

    def test_sin_solicitudes_el_reporte_esta_vacio(self, red):
        assert libros_mas_solicitados.generar() == []


class TestMovimientoEntreSedes:
    def test_agrupa_envios_por_ruta_con_tiempo_promedio(self, escenario):
        rutas = {(r.origen, r.destino): r for r in movimiento_entre_sedes.generar().rutas}
        assert set(rutas) == {("Sede Norte", "Sede Centro"), ("Sede Centro", "Sede Norte"), ("Sede Centro", "Sede Sur")}
        ida_ana = rutas[("Sede Norte", "Sede Centro")]
        assert (ida_ana.envios, ida_ana.recibidos, ida_ana.horas_promedio) == (1, 1, 10.0)
        assert rutas[("Sede Centro", "Sede Sur")].horas_promedio is None

    def test_totaliza_por_sede_y_excluye_los_no_despachados(self, escenario):
        reporte = movimiento_entre_sedes.generar()
        por_sede = {f.sede: f for f in reporte.por_sede}
        assert (por_sede["Sede Centro"].enviados, por_sede["Sede Centro"].recibidos) == (2, 1)
        assert por_sede["Sede Sur"].enviados == 0  # el envío de María se anuló antes de salir
        assert reporte.horas_promedio_general == 10.0

    def test_filtra_por_fecha_de_despacho(self, escenario):
        rutas = movimiento_entre_sedes.generar(desde=HOY - timedelta(days=9)).rutas
        assert {(r.origen, r.destino) for r in rutas} == {("Sede Centro", "Sede Norte"), ("Sede Centro", "Sede Sur")}


class TestTasaDeEnvios:
    def test_clasifica_los_envios_y_calcula_la_tasa(self, escenario):
        general = tasa_de_envios.generar().general
        assert (general.exitosos, general.con_danio, general.extraviados, general.anulados, general.en_curso) == (1, 0, 1, 1, 1)
        assert general.tasa_exito == 50.0

    def test_detalla_las_incidencias(self, escenario):
        (incidencia,) = tasa_de_envios.generar().incidencias
        assert (incidencia.tipo, incidencia.destino, incidencia.observacion) == ("Extravío", "Sede Sur", "No llegó a Sede Sur")

    def test_cuenta_el_danio_y_el_retorno_que_genera(self, red):
        prestamos, remitos = ServicioPrestamos(), ServicioRemitos()
        prestamo = prestamos.solicitar_prestamo_interbibliotecario(red.ana.id, red.ejemplar_norte.id, red.norte.id, red.centro.id, fecha=HOY)
        ida = remitos.listar_remitos_de_prestamo(prestamo.id)[0]
        remitos.empaquetar(ida.id)
        remitos.despachar(ida.id)
        remitos.recibir(ida.id, EstadoFisico.DANIADO, "Tapa rota")
        reporte = tasa_de_envios.generar()
        assert (reporte.general.con_danio, reporte.general.en_curso) == (1, 1)
        assert reporte.general.tasa_exito == 0.0

    def test_sin_envios_no_hay_tasa(self, red):
        assert tasa_de_envios.generar().general.tasa_exito is None
