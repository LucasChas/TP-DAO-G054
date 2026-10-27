"""E2E de administración de sedes (proceso obligatorio 1). Escenarios en e2e/features/sedes.feature."""
from e2e.driver import Formulario, Mensaje


def test_cp01_alta_de_sede(gui, base):
    gui.ir_a("Sedes", captura="01_pestania_vacia")
    mensajes = gui.clic("Nueva sede", Formulario({
        "Nombre": "Sede Oeste", "Dirección": "Av. Sabattini 2500", "Teléfono": "351-4222222",
        "Email": "oeste@biblio.org", "Horario de atención": "Lun a Sab 9 a 18",
    }, captura="02_formulario_completo"), Mensaje(titulo="Listo", captura="03_confirmacion"))
    assert mensajes == [("Listo", "Sede registrada.")]
    filas = gui.filas(gui.pestania.tabla)
    gui.capturar("04_sede_en_la_tabla")
    assert filas[0]["Nombre"] == "Sede Oeste" and filas[0]["Estado"] == "Activa"


def test_cp02_modificar_sede(gui, red):
    gui.ir_a("Sedes")
    gui.seleccionar(gui.pestania.tabla, "Nombre", "Sede Norte")
    gui.clic("Modificar", Formulario({"Teléfono": "351-4999999", "Horario de atención": "Lun a Vie 8 a 14"},
                                     titulo="Modificar Sede Norte", captura="01_formulario_con_datos"),
             Mensaje(contiene="Sede modificada."))
    fila = next(f for f in gui.filas(gui.pestania.tabla) if f["Nombre"] == "Sede Norte")
    gui.capturar("02_sede_modificada")
    assert fila["Teléfono"] == "351-4999999" and fila["Horario"] == "Lun a Vie 8 a 14"


def test_cp03_baja_logica_y_reactivacion_de_sede(gui, red):
    gui.ir_a("Sedes")
    gui.seleccionar(gui.pestania.tabla, "Nombre", "Sede Sur")
    gui.clic("Dar de baja", Mensaje(titulo="Confirmar", responder="yes", captura="01_confirmar_baja"),
             Mensaje(contiene="Sede dada de baja."))
    fila = next(f for f in gui.filas(gui.pestania.tabla) if f["Nombre"] == "Sede Sur")
    gui.capturar("02_sede_dada_de_baja")
    assert fila["Estado"] == "Dada de baja"
    gui.clic("Reactivar", Mensaje(contiene="Sede reactivada."))
    fila = next(f for f in gui.filas(gui.pestania.tabla) if f["Nombre"] == "Sede Sur")
    assert fila["Estado"] == "Activa"


def test_cn01_alta_de_sede_sin_datos_obligatorios(gui, base):
    gui.ir_a("Sedes")
    mensajes = gui.clic("Nueva sede", Formulario({"Dirección": "Calle 1"}),
                        Mensaje(titulo="Atención", captura="01_falta_nombre"),
                        Formulario(boton="Cancelar"))
    assert mensajes == [("Atención", "Complete el dato 'Nombre'.")]
    assert gui.filas(gui.pestania.tabla) == []


def test_cn02_sede_con_nombre_duplicado(gui, red):
    gui.ir_a("Sedes")
    mensajes = gui.clic("Nueva sede", Formulario({"Nombre": "sede centro", "Dirección": "Otra calle 1"}),
                        Mensaje(titulo="Operación rechazada", captura="01_nombre_duplicado"))
    assert mensajes == [("Operación rechazada", "Ya existe una sede llamada 'sede centro'.")]
    assert len(gui.filas(gui.pestania.tabla)) == 3


def test_cn03_sede_con_email_invalido(gui, base):
    gui.ir_a("Sedes")
    mensajes = gui.clic("Nueva sede", Formulario({"Nombre": "Sede Este", "Dirección": "Calle 2", "Email": "este-arroba"}),
                        Mensaje(titulo="Operación rechazada", captura="01_email_invalido"))
    assert mensajes == [("Operación rechazada", "El email 'este-arroba' no tiene un formato válido.")]


def test_cn04_dar_de_baja_una_sede_ya_dada_de_baja(gui, red):
    from biblioteca.servicios import ServicioSedes

    ServicioSedes().dar_de_baja_sede(red.sur.id)
    gui.ir_a("Sedes")
    gui.seleccionar(gui.pestania.tabla, "Nombre", "Sede Sur")
    mensajes = gui.clic("Dar de baja", Mensaje(responder="yes"), Mensaje(titulo="Operación rechazada", captura="01_ya_dada_de_baja"))
    assert mensajes[-1] == ("Operación rechazada", "La sede 'Sede Sur' ya está dada de baja.")


def test_cn05_modificar_sin_seleccionar_una_sede(gui, red):
    gui.ir_a("Sedes")
    mensajes = gui.clic("Modificar", Mensaje(titulo="Atención", captura="01_sin_seleccion"))
    assert mensajes == [("Atención", "Seleccione una sede en la lista.")]


def test_cn45_vaciar_un_dato_opcional_al_modificar_la_sede(gui, red):
    """Antes era el defecto D2: la sede se informaba modificada pero conservaba los datos borrados."""
    gui.ir_a("Sedes")
    gui.seleccionar(gui.pestania.tabla, "Nombre", "Sede Centro")
    mensajes = gui.clic("Modificar", Formulario({"Teléfono": "", "Email": ""}, captura="01_campos_vaciados"),
                        Mensaje(captura="02_informa_modificada"))
    assert mensajes == [("Listo", "Sede modificada.")]
    fila = next(f for f in gui.filas(gui.pestania.tabla) if f["Nombre"] == "Sede Centro")
    gui.capturar("03_datos_borrados")
    assert (fila["Teléfono"], fila["Email"]) == ("-", "-")
