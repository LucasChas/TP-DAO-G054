"""E2E de devoluciones, estado físico y multas (proceso obligatorio 8, patrón Strategy).
Escenarios en e2e/features/devoluciones.feature."""
from biblioteca.servicios import ServicioPrestamos
from e2e.conftest import hace
from e2e.driver import Formulario, Mensaje


def _prestamo(red, codigo, sede, dias_atras=0, socio=None):
    return ServicioPrestamos().registrar_prestamo_local((socio or red.ana).id, red.ej[codigo].id, sede.id, fecha=hace(dias_atras))


def test_cp22_devolucion_en_termino_sin_multa(gui, red):
    prestamo = _prestamo(red, "CEN-0001", red.centro)
    pestania = gui.ir_a("Devoluciones y multas")
    mensajes = gui.clic("Registrar devolución", Formulario({"Préstamo": f"{prestamo.id} - Pérez, Ana", "Estado físico": "Bueno"},
                                                           captura="01_formulario"), Mensaje(captura="02_resultado"))
    assert mensajes == [("Listo", "Devolución registrada.")]
    fila = gui.filas(pestania.tabla)[0]
    assert (fila["Días de atraso"], fila["Total"], fila["Pagada"]) == ("0", "$0.00", "Sí")


def test_cp23_devolucion_con_atraso_multa_por_tipo_de_material_y_pago(gui, red):
    prestamo = _prestamo(red, "CEN-0002", red.centro, dias_atras=17)  # Diccionario (consulta): vence hace 3 días
    pestania = gui.ir_a("Devoluciones y multas")
    gui.capturar("01_politica_por_defecto")
    mensajes = gui.clic("Registrar devolución", Formulario({"Préstamo": f"{prestamo.id} - Pérez, Ana"}),
                        Mensaje(captura="02_multa_calculada"))
    assert mensajes == [("Listo", "Devolución registrada.\n3 días de atraso: multa de $3,000.00.\nTotal a pagar: $3,000.00.")]
    pestania.solo_impagas.set(True)
    pestania.actualizar()
    gui.seleccionar(pestania.tabla, "Préstamo", prestamo.id)
    gui.capturar("03_multa_impaga")
    gui.clic("Registrar pago de multa", Mensaje(contiene="Pago registrado.", captura="04_pago"))
    assert gui.filas(pestania.tabla) == []


def test_cp24_devolucion_daniada_cobra_cargo_y_envia_a_reparacion(gui, red):
    prestamo = _prestamo(red, "CEN-0001", red.centro)
    pestania = gui.ir_a("Devoluciones y multas")
    mensajes = gui.clic("Registrar devolución", Formulario({"Préstamo": f"{prestamo.id} - Pérez, Ana", "Estado físico": "Dañado",
                                                            "Observaciones": "Páginas arrancadas"}, captura="01_formulario"),
                        Mensaje(captura="02_cargo_por_danio"))
    assert mensajes == [("Listo", "Devolución registrada.\nMaterial devuelto dañado: cargo de $1,000.00.\nTotal a pagar: $1,000.00.")]
    fila = gui.filas(pestania.tabla)[0]
    assert (fila["Por atraso"], fila["Por daño"], fila["Total"], fila["Pagada"]) == ("$0.00", "$1,000.00", "$1,000.00", "No")
    catalogo = gui.ir_a("Catálogo")
    gui.seleccionar(catalogo.tabla_libros, "Título", "Rayuela")
    ejemplar = next(f for f in gui.filas(catalogo.tabla_ejemplares) if f["Código"] == "CEN-0001")
    assert (ejemplar["Estado"], ejemplar["Estado físico"]) == ("En reparación", "Dañado")


def test_cp25_cambiar_la_politica_de_multas_strategy(gui, red):
    p1 = _prestamo(red, "CEN-0002", red.centro, dias_atras=17)
    p2 = _prestamo(red, "NOR-0001", red.norte, dias_atras=17, socio=red.juan)
    pestania = gui.ir_a("Devoluciones y multas")

    def elegir(descripcion, captura):
        pestania.selector_politica.set(descripcion)
        return gui._con_pasos(lambda: pestania.selector_politica.event_generate("<<ComboboxSelected>>"),
                              [Mensaje(captura=captura)])

    assert elegir("Por días de atraso ($500 por día)", "01_politica_por_dias") == [
        ("Listo", "Política de multas: Por días de atraso ($500 por día).")]
    mensajes = gui.clic("Registrar devolución", Formulario({"Préstamo": f"{p1.id} - Pérez, Ana"}), Mensaje())
    assert "multa de $1,500.00" in mensajes[0][1]  # 3 días x $500 (con la política por defecto serían $3000)

    assert elegir("Sin multa (condonación)", "02_politica_sin_multa")[0][1] == "Política de multas: Sin multa (condonación)."
    mensajes = gui.clic("Registrar devolución", Formulario({"Préstamo": f"{p2.id} - Gómez, Juan"}), Mensaje(captura="03_condonada"))
    assert mensajes == [("Listo", "Devolución registrada.")]


def test_cn39_pagar_una_multa_que_no_esta_pendiente(gui, red):
    prestamo = _prestamo(red, "CEN-0001", red.centro)
    pestania = gui.ir_a("Devoluciones y multas")
    gui.clic("Registrar devolución", Formulario({"Préstamo": f"{prestamo.id} - Pérez, Ana"}), Mensaje())
    gui.seleccionar(pestania.tabla, "Préstamo", prestamo.id)
    mensajes = gui.clic("Registrar pago de multa", Mensaje(titulo="Operación rechazada", captura="01_sin_multa"))
    assert mensajes == [("Operación rechazada", "Esa devolución no tiene una multa pendiente de pago.")]


def test_cn40_registrar_devolucion_sin_prestamos_activos(gui, red):
    gui.ir_a("Devoluciones y multas")
    mensajes = gui.clic("Registrar devolución", Formulario({}, captura="01_lista_vacia"),
                        Mensaje(titulo="Atención", captura="02_falta_prestamo"), Formulario(boton="Cancelar"))
    assert mensajes == [("Atención", "Complete el dato 'Préstamo'.")]
