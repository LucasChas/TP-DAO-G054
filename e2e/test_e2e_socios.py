"""E2E de administración de socios (proceso obligatorio 2). Escenarios en e2e/features/socios.feature."""
from e2e.driver import Formulario, Mensaje


def test_cp04_alta_de_socio_con_dni_normalizado(gui, base):
    gui.ir_a("Socios")
    mensajes = gui.clic("Nuevo socio", Formulario({
        "DNI": "30.555.666", "Nombre": "Carla", "Apellido": "Ruiz", "Email": "carla@correo.com", "Teléfono": "351-5550000",
    }, captura="01_formulario_socio"), Mensaje(captura="02_confirmacion"))
    assert mensajes == [("Listo", "Socio registrado.")]
    fila = gui.filas(gui.pestania.tabla)[0]
    gui.capturar("03_socio_en_la_tabla")
    assert fila["DNI"] == "30555666" and fila["Apellido y nombre"] == "Ruiz, Carla" and fila["Estado"] == "Habilitado"


def test_cp05_inhabilitar_y_rehabilitar_socio(gui, red):
    gui.ir_a("Socios")
    gui.seleccionar(gui.pestania.tabla, "DNI", "28999888")
    gui.clic("Inhabilitar", Formulario({"Motivo": "Extravió un ejemplar"}, captura="01_motivo"),
             Mensaje(contiene="Socio inhabilitado."))
    fila = next(f for f in gui.filas(gui.pestania.tabla) if f["DNI"] == "28999888")
    gui.capturar("02_socio_inhabilitado")
    assert fila["Estado"] == "Inhabilitado" and fila["Motivo"] == "Extravió un ejemplar"
    gui.clic("Habilitar", Mensaje(contiene="Socio habilitado."))
    fila = next(f for f in gui.filas(gui.pestania.tabla) if f["DNI"] == "28999888")
    assert fila["Estado"] == "Habilitado" and fila["Motivo"] == "-"


def test_cp06_modificar_datos_de_contacto_del_socio(gui, red):
    gui.ir_a("Socios")
    gui.seleccionar(gui.pestania.tabla, "DNI", "30111222")
    gui.clic("Modificar", Formulario({"Email": "ana.perez@correo.com"}, titulo="Modificar Pérez, Ana", captura="01_formulario"),
             Mensaje(contiene="Socio modificado."))
    fila = next(f for f in gui.filas(gui.pestania.tabla) if f["DNI"] == "30111222")
    assert fila["Email"] == "ana.perez@correo.com"


def test_cn06_alta_de_socio_con_dni_invalido(gui, base):
    gui.ir_a("Socios")
    mensajes = gui.clic("Nuevo socio", Formulario({"DNI": "12ab", "Nombre": "X", "Apellido": "Y"}),
                        Mensaje(titulo="Operación rechazada", captura="01_dni_invalido"))
    assert mensajes == [("Operación rechazada", "El DNI '12ab' no es válido: debe tener 7 u 8 dígitos.")]


def test_cn07_alta_de_socio_con_dni_duplicado(gui, red):
    gui.ir_a("Socios")
    mensajes = gui.clic("Nuevo socio", Formulario({"DNI": "30111222", "Nombre": "Otra", "Apellido": "Persona"}),
                        Mensaje(titulo="Operación rechazada", captura="01_dni_duplicado"))
    assert mensajes == [("Operación rechazada", "Ya existe un socio con DNI 30111222.")]
    assert len(gui.filas(gui.pestania.tabla)) == 3


def test_cn08_inhabilitar_sin_motivo(gui, red):
    gui.ir_a("Socios")
    gui.seleccionar(gui.pestania.tabla, "DNI", "30111222")
    mensajes = gui.clic("Inhabilitar", Formulario({}), Mensaje(titulo="Atención", captura="01_falta_motivo"),
                        Formulario(boton="Cancelar"))
    assert mensajes == [("Atención", "Complete el dato 'Motivo'.")]


def test_cn09_inhabilitar_un_socio_ya_inhabilitado(gui, red):
    gui.ir_a("Socios")
    gui.seleccionar(gui.pestania.tabla, "DNI", "33444555")
    mensajes = gui.clic("Inhabilitar", Formulario({"Motivo": "Otro"}), Mensaje(titulo="Operación rechazada", captura="01_ya_inhabilitado"))
    assert mensajes == [("Operación rechazada", "El socio Torres, Lía ya está inhabilitado.")]
