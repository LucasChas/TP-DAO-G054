"""E2E del catálogo, ejemplares por sede y consulta de disponibilidad (procesos obligatorios 3 y 6).
Escenarios en e2e/features/catalogo.feature."""
from datetime import timedelta

from biblioteca.modelos.enumeraciones import EstadoFisico
from biblioteca.servicios import ServicioDevoluciones, ServicioPrestamos, ServicioSedes
from e2e.conftest import HOY
from e2e.driver import Formulario, Mensaje, Ventana


def test_cp07_alta_de_libro_y_de_ejemplar_en_una_sede(gui, red):
    pestania = gui.ir_a("Catálogo")
    gui.clic("Nuevo libro", Formulario({
        "ISBN": "978-950-04-3046-3", "Título": "Ficciones", "Autor": "Jorge Luis Borges",
        "Editorial": "Emecé", "Año de publicación": "1944", "Tipo de material": "Libro",
    }, captura="01_formulario_libro"), Mensaje(contiene="Libro registrado.", captura="02_libro_registrado"))
    libro = next(f for f in gui.filas(pestania.tabla_libros) if f["Título"] == "Ficciones")
    assert libro["ISBN"] == "9789500430463"
    gui.seleccionar(pestania.tabla_libros, "Título", "Ficciones")
    gui.clic("Nuevo ejemplar", Formulario({"Sede propietaria": "Sede Norte", "Código de inventario": "nor-0100"},
                                          captura="03_formulario_ejemplar"),
             Mensaje(contiene="Ejemplar registrado."))
    ejemplares = gui.filas(pestania.tabla_ejemplares)
    gui.capturar("04_ejemplar_del_libro")
    assert ejemplares == [{"Id": ejemplares[0]["Id"], "Código": "NOR-0100", "Sede propietaria": "Sede Norte",
                           "Estado": "Disponible", "Estado físico": "Bueno"}]


def test_cp08_consultar_disponibilidad_por_sede(gui, red):
    ServicioPrestamos().registrar_prestamo_local(red.ana.id, red.ej["CEN-0001"].id, red.centro.id)
    ServicioPrestamos().solicitar_prestamo_interbibliotecario(red.juan.id, red.ej["SUR-0002"].id, red.sur.id, red.norte.id)
    pestania = gui.ir_a("Catálogo")
    gui.seleccionar(pestania.tabla_libros, "Título", "Rayuela")
    ventana = Ventana("Disponibilidad de 'Rayuela'", captura="01_disponibilidad")
    gui.clic("Ver disponibilidad", ventana)
    assert ventana.tabla == [
        {"Sede": "Sede Centro", "Total": "1", "Disponibles": "0", "Reservados": "0", "Prestados": "1", "En tránsito": "0"},
        {"Sede": "Sede Norte", "Total": "1", "Disponibles": "1", "Reservados": "0", "Prestados": "0", "En tránsito": "0"},
        {"Sede": "Sede Sur", "Total": "1", "Disponibles": "0", "Reservados": "0", "Prestados": "1", "En tránsito": "0"},
    ]


def test_cp09_finalizar_reparacion_y_dar_de_baja_un_ejemplar(gui, red):
    prestamo = ServicioPrestamos().registrar_prestamo_local(red.ana.id, red.ej["CEN-0001"].id, red.centro.id)
    ServicioDevoluciones().registrar_devolucion(prestamo.id, EstadoFisico.DANIADO)
    pestania = gui.ir_a("Catálogo")
    gui.seleccionar(pestania.tabla_libros, "Título", "Rayuela")
    gui.seleccionar(pestania.tabla_ejemplares, "Código", "CEN-0001")
    gui.capturar("01_ejemplar_en_reparacion")
    gui.clic("Finalizar reparación", Mensaje(contiene="El ejemplar vuelve a circular."))
    fila = next(f for f in gui.filas(pestania.tabla_ejemplares) if f["Código"] == "CEN-0001")
    assert (fila["Estado"], fila["Estado físico"]) == ("Disponible", "Regular")
    gui.seleccionar(pestania.tabla_ejemplares, "Código", "CEN-0001")
    gui.clic("Dar de baja ejemplar", Mensaje(titulo="Confirmar", responder="yes", captura="02_confirmar_baja"),
             Mensaje(contiene="Ejemplar dado de baja."))
    fila = next(f for f in gui.filas(pestania.tabla_ejemplares) if f["Código"] == "CEN-0001")
    gui.capturar("03_ejemplar_dado_de_baja")
    assert fila["Estado"] == "Dado de baja"


def test_cn10_libro_con_isbn_invalido(gui, red):
    gui.ir_a("Catálogo")
    mensajes = gui.clic("Nuevo libro", Formulario({"ISBN": "123", "Título": "T", "Autor": "A"}),
                        Mensaje(titulo="Operación rechazada", captura="01_isbn_invalido"))
    assert mensajes == [("Operación rechazada", "El ISBN '123' no es válido: debe tener 10 o 13 dígitos.")]


def test_cn11_libro_con_isbn_duplicado(gui, red):
    gui.ir_a("Catálogo")
    mensajes = gui.clic("Nuevo libro", Formulario({"ISBN": "978-950-07-0001-6", "Título": "Rayuela (2da ed.)", "Autor": "Cortázar"}),
                        Mensaje(titulo="Operación rechazada", captura="01_isbn_duplicado"))
    assert mensajes == [("Operación rechazada", "Ya existe un libro con ISBN 9789500700016.")]


def test_cn12_ejemplar_con_codigo_de_inventario_duplicado(gui, red):
    pestania = gui.ir_a("Catálogo")
    gui.seleccionar(pestania.tabla_libros, "Título", "Rayuela")
    mensajes = gui.clic("Nuevo ejemplar", Formulario({"Sede propietaria": "Sede Centro", "Código de inventario": "cen-0001"}),
                        Mensaje(titulo="Operación rechazada", captura="01_codigo_duplicado"))
    assert mensajes == [("Operación rechazada", "Ya existe un ejemplar con código CEN-0001.")]


def test_cn13_ejemplar_en_una_sede_dada_de_baja(gui, red):
    ServicioSedes().dar_de_baja_sede(red.sur.id)
    pestania = gui.ir_a("Catálogo")
    gui.seleccionar(pestania.tabla_libros, "Título", "Rayuela")
    mensajes = gui.clic("Nuevo ejemplar", Formulario({"Sede propietaria": "Sede Sur (dada de baja)", "Código de inventario": "SUR-0099"},
                                                     captura="01_sede_de_baja_en_la_lista"),
                        Mensaje(titulo="Operación rechazada", captura="02_rechazo"))
    assert mensajes == [("Operación rechazada",
                         "No se pueden incorporar ejemplares a la sede 'Sede Sur' porque está dada de baja.")]


def test_cn14_anio_de_publicacion_no_numerico(gui, red):
    gui.ir_a("Catálogo")
    mensajes = gui.clic("Nuevo libro", Formulario({"ISBN": "9789500000017", "Título": "T", "Autor": "A", "Año de publicación": "abc"}),
                        Mensaje(titulo="Atención", captura="01_anio_invalido"), Formulario(boton="Cancelar"))
    assert mensajes == [("Atención", "'abc' no es un valor válido para 'Año de publicación'.")]


def test_cn15_anio_de_publicacion_fuera_de_rango(gui, red):
    gui.ir_a("Catálogo")
    anio = (HOY + timedelta(days=366)).year
    mensajes = gui.clic("Nuevo libro", Formulario({"ISBN": "9789500000017", "Título": "T", "Autor": "A", "Año de publicación": anio}),
                        Mensaje(titulo="Operación rechazada", captura="01_anio_futuro"))
    assert mensajes == [("Operación rechazada", f"El año de publicación {anio} no es válido.")]


def test_cn16_dar_de_baja_un_ejemplar_prestado(gui, red):
    ServicioPrestamos().registrar_prestamo_local(red.ana.id, red.ej["CEN-0001"].id, red.centro.id)
    pestania = gui.ir_a("Catálogo")
    gui.seleccionar(pestania.tabla_libros, "Título", "Rayuela")
    gui.seleccionar(pestania.tabla_ejemplares, "Código", "CEN-0001")
    mensajes = gui.clic("Dar de baja ejemplar", Mensaje(responder="yes"), Mensaje(titulo="Operación rechazada", captura="01_rechazo"))
    assert mensajes[-1] == ("Operación rechazada", "El ejemplar CEN-0001 está prestado y no se puede dar de baja.")


def test_cn17_finalizar_reparacion_de_un_ejemplar_sano(gui, red):
    pestania = gui.ir_a("Catálogo")
    gui.seleccionar(pestania.tabla_libros, "Título", "Rayuela")
    gui.seleccionar(pestania.tabla_ejemplares, "Código", "NOR-0001")
    mensajes = gui.clic("Finalizar reparación", Mensaje(titulo="Operación rechazada", captura="01_rechazo"))
    assert mensajes == [("Operación rechazada", "El ejemplar NOR-0001 no está en reparación.")]


def test_cp31_buscar_libros_por_titulo_o_autor(gui, red):
    pestania = gui.ir_a("Catálogo")
    pestania.busqueda.insert(0, "rae")
    gui.clic("Buscar")
    gui.capturar("01_resultado_de_la_busqueda")
    assert [f["Título"] for f in gui.filas(pestania.tabla_libros)] == ["Diccionario de la lengua"]
    gui.clic("Ver todos")
    assert len(gui.filas(pestania.tabla_libros)) == 3


def test_cn47_libro_con_digito_verificador_incorrecto(gui, red):
    gui.ir_a("Catálogo")
    mensajes = gui.clic("Nuevo libro", Formulario({"ISBN": "978-950-04-3046-7", "Título": "Ficciones", "Autor": "Borges"}),
                        Mensaje(titulo="Operación rechazada", captura="01_digito_verificador"))
    assert mensajes == [("Operación rechazada",
                         "El ISBN '978-950-04-3046-7' no es válido: el dígito verificador no corresponde.")]
