"""E2E de préstamos locales e interbibliotecarios (proceso obligatorio 4) y sus validaciones.
Escenarios en e2e/features/prestamos.feature."""
from datetime import timedelta

from biblioteca.modelos.enumeraciones import EstadoFisico
from biblioteca.servicios import ServicioDevoluciones, ServicioPrestamos, ServicioRemitos, ServicioSedes
from e2e.conftest import HOY, hace
from e2e.driver import Formulario, Mensaje


def _vence(dias=14):
    return (HOY + timedelta(days=dias)).strftime("%d/%m/%Y")


def test_cp10_prestamo_local(gui, red):
    pestania = gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo local", Formulario({
        "Socio": "Pérez, Ana", "Sede": "Sede Centro", "Ejemplar de la sede": "CEN-0001",
    }, captura="01_formulario_prestamo_local"), Mensaje(captura="02_confirmacion"))
    assert mensajes == [("Listo", f"Préstamo registrado. Vence el {_vence()}.")]
    fila = gui.filas(pestania.tabla)[0]
    gui.capturar("03_prestamo_activo")
    assert (fila["Tipo"], fila["Socio"], fila["Ejemplar"], fila["Origen"], fila["Destino"], fila["Vence"], fila["Estado"]) == (
        "Local", "Pérez, Ana", "CEN-0001", "Sede Centro", "Sede Centro", _vence(), "Activo")


def test_cp11_solicitud_interbibliotecaria_genera_remito_de_ida(gui, red):
    pestania = gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo interbibliotecario", Formulario({
        "Socio": "Pérez, Ana", "Sede de origen (dueña del ejemplar)": "Sede Norte",
        "Sede de destino (retiro)": "Sede Centro", "Ejemplar de la sede de origen": "NOR-0001",
    }, captura="01_formulario_interbibliotecario"), Mensaje(captura="02_confirmacion"))
    assert mensajes == [("Listo", "Solicitud registrada. Se generó el remito de ida.")]
    fila = gui.filas(pestania.tabla)[0]
    gui.capturar("03_prestamo_solicitado")
    assert (fila["Tipo"], fila["Origen"], fila["Destino"], fila["Vence"], fila["Estado"]) == (
        "Interbibliotecario", "Sede Norte", "Sede Centro", "-", "Solicitado")
    remitos = gui.ir_a("Remitos")
    remito = gui.filas(remitos.tabla)[0]
    gui.capturar("04_remito_de_ida_generado")
    assert (remito["Número"], remito["Sentido"], remito["Origen"], remito["Destino"], remito["Estado"]) == (
        "R-000001", "Ida", "Sede Norte", "Sede Centro", "Generado")


def test_cp12_cancelar_solicitud_interbibliotecaria(gui, red):
    ServicioPrestamos().solicitar_prestamo_interbibliotecario(red.ana.id, red.ej["NOR-0001"].id, red.norte.id, red.centro.id)
    pestania = gui.ir_a("Préstamos")
    gui.seleccionar(pestania.tabla, "Ejemplar", "NOR-0001")
    gui.clic("Cancelar solicitud", Mensaje(titulo="Confirmar", responder="yes", captura="01_confirmar"),
             Mensaje(contiene="Solicitud cancelada."))
    pestania.filtro.set("Todos")
    pestania.actualizar()
    gui.capturar("02_prestamo_cancelado")
    assert gui.filas(pestania.tabla)[0]["Estado"] == "Cancelado"
    remito = gui.filas(gui.ir_a("Remitos").tabla)[0]
    assert remito["Estado"] == "Anulado"
    catalogo = gui.ir_a("Catálogo")
    gui.seleccionar(catalogo.tabla_libros, "Título", "Rayuela")
    assert next(f for f in gui.filas(catalogo.tabla_ejemplares) if f["Código"] == "NOR-0001")["Estado"] == "Disponible"


def test_cn18_prestamo_a_socio_inhabilitado(gui, red):
    gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo local", Formulario({
        "Socio": "Torres, Lía", "Sede": "Sede Centro", "Ejemplar de la sede": "CEN-0001",
    }, captura="01_socio_inhabilitado_en_la_lista"), Mensaje(titulo="Operación rechazada", captura="02_rechazo"))
    assert mensajes == [("Operación rechazada", "El socio Torres, Lía está inhabilitado (Deuda de cuota social).")]


def test_cn19_prestamo_de_ejemplar_no_disponible(gui, red):
    ServicioPrestamos().registrar_prestamo_local(red.juan.id, red.ej["CEN-0001"].id, red.centro.id)
    pestania = gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo local", Formulario({
        "Socio": "Pérez, Ana", "Sede": "Sede Centro", "Ejemplar de la sede": "CEN-0001",
    }), Mensaje(titulo="Operación rechazada", captura="01_ejemplar_prestado"))
    assert mensajes == [("Operación rechazada", "El ejemplar CEN-0001 no está disponible (prestado).")]
    assert len(gui.filas(pestania.tabla)) == 1


def test_cn20_la_lista_solo_ofrece_ejemplares_de_la_sede_de_origen(gui, red):
    """La validación 'no prestar ejemplares de otra sede' se cubre en la interfaz filtrando la lista:
    no hay forma de elegir desde la GUI un ejemplar de otra sede."""
    gui.ir_a("Préstamos")
    vistos = {}

    class Inspeccionar(Formulario):
        def resolver(self, driver, formulario):
            clic = super().resolver(driver, formulario)
            control = formulario._controles["id_ejemplar"]
            vistos["opciones"] = list(control.cget("values"))
            return clic

    gui.clic("Préstamo interbibliotecario", Inspeccionar({"Sede de origen (dueña del ejemplar)": "Sede Sur"},
                                                         captura="01_solo_ejemplares_de_sede_sur", boton="Cancelar"))
    assert vistos["opciones"] == [
        "SUR-0001 - Revista Ñ (Sede Sur, disponible)",
        "SUR-0002 - Rayuela (Sede Sur, disponible)",
    ]


def test_cn21_prestamo_desde_una_sede_dada_de_baja(gui, red):
    ServicioSedes().dar_de_baja_sede(red.norte.id)
    gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo interbibliotecario", Formulario({
        "Socio": "Pérez, Ana", "Sede de origen (dueña del ejemplar)": "Sede Norte (dada de baja)",
        "Sede de destino (retiro)": "Sede Centro", "Ejemplar de la sede de origen": "NOR-0001",
    }), Mensaje(titulo="Operación rechazada", captura="01_sede_de_baja"))
    assert mensajes == [("Operación rechazada", "La sede de origen 'Sede Norte' está dada de baja.")]


def test_cn22_prestamo_a_socio_con_prestamos_vencidos(gui, red):
    ServicioPrestamos().registrar_prestamo_local(red.juan.id, red.ej["CEN-0002"].id, red.centro.id, fecha=hace(20))
    pestania = gui.ir_a("Préstamos")
    pestania.filtro.set("Vencidos")
    pestania.actualizar()
    gui.capturar("01_prestamo_vencido")
    mensajes = gui.clic("Préstamo local", Formulario({
        "Socio": "Gómez, Juan", "Sede": "Sede Norte", "Ejemplar de la sede": "NOR-0001",
    }), Mensaje(titulo="Operación rechazada", captura="02_rechazo"))
    assert mensajes == [("Operación rechazada", "El socio Gómez, Juan tiene préstamos vencidos sin devolver.")]


def test_cn23_prestamo_a_socio_con_multas_impagas(gui, red):
    prestamo = ServicioPrestamos().registrar_prestamo_local(red.juan.id, red.ej["CEN-0002"].id, red.centro.id, fecha=hace(20))
    ServicioDevoluciones().registrar_devolucion(prestamo.id, EstadoFisico.BUENO)
    gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo local", Formulario({
        "Socio": "Gómez, Juan", "Sede": "Sede Norte", "Ejemplar de la sede": "NOR-0001",
    }), Mensaje(titulo="Operación rechazada", captura="01_rechazo"))
    assert mensajes == [("Operación rechazada", "El socio Gómez, Juan tiene multas sin pagar.")]


def test_cn24_interbibliotecario_con_la_misma_sede_de_origen_y_destino(gui, red):
    gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo interbibliotecario", Formulario({
        "Socio": "Pérez, Ana", "Sede de origen (dueña del ejemplar)": "Sede Centro",
        "Sede de destino (retiro)": "Sede Centro", "Ejemplar de la sede de origen": "CEN-0001",
    }), Mensaje(titulo="Operación rechazada", captura="01_misma_sede"))
    assert mensajes == [("Operación rechazada",
                         "En un préstamo interbibliotecario la sede de origen y la de destino deben ser distintas.")]


def test_cn25_entregar_un_prestamo_que_no_llego(gui, red):
    ServicioPrestamos().solicitar_prestamo_interbibliotecario(red.ana.id, red.ej["NOR-0001"].id, red.norte.id, red.centro.id)
    pestania = gui.ir_a("Préstamos")
    gui.seleccionar(pestania.tabla, "Ejemplar", "NOR-0001")
    mensajes = gui.clic("Entregar al socio", Mensaje(titulo="Operación rechazada", captura="01_no_listo"))
    assert mensajes == [("Operación rechazada",
                         "El préstamo está solicitado: solo se entregan préstamos listos para retiro.")]


def test_cn26_cancelar_una_solicitud_ya_despachada(gui, red):
    prestamo = ServicioPrestamos().solicitar_prestamo_interbibliotecario(
        red.ana.id, red.ej["NOR-0001"].id, red.norte.id, red.centro.id)
    remito = ServicioRemitos().listar_remitos_de_prestamo(prestamo.id)[0]
    ServicioRemitos().empaquetar(remito.id)
    ServicioRemitos().despachar(remito.id)
    pestania = gui.ir_a("Préstamos")
    gui.seleccionar(pestania.tabla, "Ejemplar", "NOR-0001")
    mensajes = gui.clic("Cancelar solicitud", Mensaje(responder="yes"), Mensaje(titulo="Operación rechazada", captura="01_rechazo"))
    assert mensajes[-1] == ("Operación rechazada",
                            "El préstamo está en envío: solo se cancelan solicitudes no despachadas.")


def test_cn44_prestamo_de_ejemplar_en_reparacion(gui, red):
    prestamo = ServicioPrestamos().registrar_prestamo_local(red.juan.id, red.ej["CEN-0001"].id, red.centro.id)
    ServicioDevoluciones().registrar_devolucion(prestamo.id, EstadoFisico.DANIADO)
    gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo local", Formulario({
        "Socio": "Pérez, Ana", "Sede": "Sede Centro", "Ejemplar de la sede": "CEN-0001",
    }, captura="01_ejemplar_en_reparacion_en_la_lista"), Mensaje(titulo="Operación rechazada", captura="02_rechazo"))
    assert mensajes == [("Operación rechazada", "El ejemplar CEN-0001 no está disponible (en reparación).")]
