"""E2E del ciclo de vida del remito (proceso obligatorio 5, patrón State) y la trazabilidad del trayecto.
Escenarios en e2e/features/remitos.feature."""
from biblioteca.modelos.enumeraciones import EstadoFisico
from biblioteca.servicios import ServicioPrestamos, ServicioRemitos, ServicioSedes
from e2e.driver import Formulario, Mensaje


def _solicitud(red):
    """Ana pide en la Sede Centro el ejemplar NOR-0001 de la Sede Norte: genera el remito R-000001."""
    prestamo = ServicioPrestamos().solicitar_prestamo_interbibliotecario(
        red.ana.id, red.ej["NOR-0001"].id, red.norte.id, red.centro.id)
    return prestamo, ServicioRemitos().listar_remitos_de_prestamo(prestamo.id)[0]


def _despachado(red):
    prestamo, remito = _solicitud(red)
    ServicioRemitos().empaquetar(remito.id)
    ServicioRemitos().despachar(remito.id)
    return prestamo, remito


def _fila(gui, numero):
    return next(f for f in gui.filas(gui.pestania.tabla) if f["Número"] == numero)


def _estado_ejemplar(gui, codigo):
    catalogo = gui.ir_a("Catálogo")
    gui.seleccionar(catalogo.tabla_libros, "Título", "Rayuela")
    return next(f for f in gui.filas(catalogo.tabla_ejemplares) if f["Código"] == codigo)


def test_cp13_ciclo_completo_del_remito_de_ida_con_trazabilidad(gui, red):
    _solicitud(red)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    gui.capturar("01_remito_generado")
    pasos = [
        ("Empaquetar", {"Observación": "Caja 12, sellada"}, "Remito empaquetado. Estado actual: Empaquetado."),
        ("Despachar", {"Observación": "Transporte interno, móvil 3"}, "Remito despachado. Estado actual: Despachado."),
        ("Punto de control", {"Ubicación": "Centro de distribución Alta Córdoba"},
         "Punto de control registrado. Estado actual: En tránsito."),
        ("Recibir", {"Estado físico del ejemplar": "Bueno", "Observación": "Llegó en condiciones"},
         "Remito recibido. Estado actual: Recibido."),
    ]
    for numero, (boton, valores, esperado) in enumerate(pasos, start=2):
        gui.seleccionar(pestania.tabla, "Número", "R-000001")
        nombre = boton.lower().replace(" ", "_")
        mensajes = gui.clic(boton, Formulario(valores, captura=f"{numero:02d}_{nombre}_formulario"),
                            Mensaje(captura=f"{numero:02d}_{nombre}_resultado"))
        assert mensajes == [("Listo", esperado)]
    prestamos = gui.ir_a("Préstamos")
    assert gui.filas(prestamos.tabla)[0]["Estado"] == "Listo para retiro"
    gui.seleccionar(prestamos.tabla, "Ejemplar", "NOR-0001")
    mensajes = gui.clic("Entregar al socio", Mensaje(captura="06_entrega_al_socio"))
    assert mensajes[0][1].startswith("Préstamo entregado. Vence el ")
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    gui.capturar("07_trayecto_completo")
    assert _fila(gui, "R-000001")["Estado"] == "Cerrado"
    trayecto = [(f["Estado anterior"], f["Estado nuevo"], f["Observación"]) for f in gui.filas(pestania.tabla_trayecto)]
    assert trayecto == [
        ("-", "Generado", "-"),
        ("Generado", "Empaquetado", "Caja 12, sellada"),
        ("Empaquetado", "Despachado", "Transporte interno, móvil 3"),
        ("Despachado", "En tránsito", "Centro de distribución Alta Córdoba"),
        ("En tránsito", "Recibido", "Llegó en condiciones"),
        ("Recibido", "Cerrado", "Entregado al socio"),
    ]


def test_cp14_recepcion_con_danio_genera_remito_de_retorno(gui, red):
    _despachado(red)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Recibir", Formulario({"Estado físico del ejemplar": "Dañado", "Observación": "Tapa rota"},
                                              captura="01_recibir_daniado"), Mensaje(captura="02_resultado"))
    assert mensajes == [("Listo", "Remito recibido. Estado actual: Cerrado.")]
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    gui.capturar("03_trayecto_con_incidente")
    estados = [f["Estado nuevo"] for f in gui.filas(pestania.tabla_trayecto)]
    assert estados == ["Generado", "Empaquetado", "Despachado", "Recibido", "Dañado", "Cerrado"]
    retorno = _fila(gui, "R-000002")
    assert (retorno["Sentido"], retorno["Origen"], retorno["Destino"], retorno["Estado"]) == (
        "Retorno", "Sede Centro", "Sede Norte", "Generado")
    pestania_prestamos = gui.ir_a("Préstamos")
    pestania_prestamos.filtro.set("Todos")
    pestania_prestamos.actualizar()
    assert gui.filas(pestania_prestamos.tabla)[0]["Estado"] == "Cancelado"


def test_cp15_registrar_danio_despues_de_recibir(gui, red):
    _, remito = _despachado(red)
    ServicioRemitos().recibir(remito.id, EstadoFisico.BUENO)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Registrar daño", Formulario({"Descripción del daño": "Hojas manchadas al abrir el paquete"},
                                                     captura="01_formulario_danio"), Mensaje(captura="02_resultado"))
    assert mensajes == [("Listo", "Daño registrado; se generó el remito de retorno. Estado actual: Cerrado.")]
    assert _fila(gui, "R-000002")["Sentido"] == "Retorno"


def test_cp16_reportar_extravio(gui, red):
    _despachado(red)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Reportar extravío", Formulario({"Observación": "El paquete no llegó a destino"}, captura="01_formulario"),
                        Mensaje(captura="02_resultado"))
    assert mensajes == [("Listo", "Extravío registrado. Estado actual: Cerrado.")]
    assert _estado_ejemplar(gui, "NOR-0001")["Estado"] == "Extraviado"
    gui.capturar("03_ejemplar_extraviado")


def test_cp17_anular_remito_de_ida_antes_del_despacho(gui, red):
    _solicitud(red)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Anular", Formulario({"Motivo": "El socio desistió"}, captura="01_motivo"), Mensaje(captura="02_resultado"))
    assert mensajes == [("Listo", "Remito anulado y préstamo cancelado. Estado actual: Anulado.")]
    assert _estado_ejemplar(gui, "NOR-0001")["Estado"] == "Disponible"


def test_cp18_remito_de_retorno_reintegra_el_ejemplar_a_su_sede(gui, red):
    prestamo, remito = _despachado(red)
    ServicioRemitos().recibir(remito.id, EstadoFisico.BUENO)
    ServicioPrestamos().entregar_prestamo(prestamo.id)
    devoluciones = gui.ir_a("Devoluciones y multas")
    mensajes = gui.clic("Registrar devolución", Formulario({"Préstamo": f"{prestamo.id} - Pérez, Ana", "Estado físico": "Bueno"},
                                                           captura="01_devolucion"), Mensaje(captura="02_resultado"))
    assert mensajes == [("Listo", "Devolución registrada.\nSe generó el remito de retorno a la sede propietaria.")]
    assert devoluciones.tabla.filas()
    pestania = gui.ir_a("Remitos")
    for boton, valores in [("Empaquetar", {}), ("Despachar", {}), ("Recibir", {"Estado físico del ejemplar": "Bueno"})]:
        gui.seleccionar(pestania.tabla, "Número", "R-000002")
        gui.clic(boton, Formulario(valores), Mensaje())
    gui.seleccionar(pestania.tabla, "Número", "R-000002")
    gui.capturar("03_retorno_cerrado")
    assert _fila(gui, "R-000002")["Estado"] == "Cerrado"
    assert gui.filas(pestania.tabla_trayecto)[-1]["Observación"] == "Ejemplar reintegrado a su sede"
    assert _estado_ejemplar(gui, "NOR-0001")["Estado"] == "Disponible"


def test_cn27_recibir_un_remito_que_no_salio(gui, red):
    _solicitud(red)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Recibir", Formulario({"Estado físico del ejemplar": "Bueno"}),
                        Mensaje(titulo="Operación rechazada", captura="01_transicion_invalida"))
    assert mensajes == [("Operación rechazada", "No se puede recibir un remito en estado Generado.")]
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    assert _fila(gui, "R-000001")["Estado"] == "Generado"
    assert len(gui.filas(pestania.tabla_trayecto)) == 1


def test_cn28_anular_un_remito_ya_despachado(gui, red):
    _despachado(red)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Anular", Formulario({"Motivo": "Error"}), Mensaje(titulo="Operación rechazada", captura="01_rechazo"))
    assert mensajes == [("Operación rechazada", "No se puede anular un remito en estado Despachado.")]


def test_cn29_despachar_hacia_una_sede_dada_de_baja(gui, red):
    _, remito = _solicitud(red)
    ServicioRemitos().empaquetar(remito.id)
    ServicioSedes().dar_de_baja_sede(red.centro.id)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Despachar", Formulario({}), Mensaje(titulo="Operación rechazada", captura="01_rechazo"))
    assert mensajes == [("Operación rechazada", "No se puede despachar: la sede de destino 'Sede Centro' está dada de baja.")]
    assert _fila(gui, "R-000001")["Estado"] == "Empaquetado"


def test_cn30_anular_un_remito_de_retorno(gui, red):
    _despachado(red)
    ServicioRemitos().recibir(1, EstadoFisico.DANIADO)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000002")
    mensajes = gui.clic("Anular", Formulario({"Motivo": "Prueba"}), Mensaje(titulo="Operación rechazada", captura="01_rechazo"))
    assert mensajes == [("Operación rechazada", "Un remito de retorno no se puede anular: el ejemplar debe volver a su sede.")]


def test_cn31_punto_de_control_sin_ubicacion(gui, red):
    _despachado(red)
    pestania = gui.ir_a("Remitos")
    gui.seleccionar(pestania.tabla, "Número", "R-000001")
    mensajes = gui.clic("Punto de control", Formulario({}), Mensaje(titulo="Atención", captura="01_falta_ubicacion"),
                        Formulario(boton="Cancelar"))
    assert mensajes == [("Atención", "Complete el dato 'Ubicación'.")]


def test_cn32_accion_sin_remito_seleccionado(gui, red):
    _solicitud(red)
    gui.ir_a("Remitos")
    mensajes = gui.clic("Empaquetar", Mensaje(titulo="Atención", captura="01_sin_seleccion"))
    assert mensajes == [("Atención", "Seleccione un remito en la lista.")]
