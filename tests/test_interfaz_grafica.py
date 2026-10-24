"""Tests de la interfaz gráfica.

Se reemplazan los formularios y los mensajes por funciones de prueba, así no se
abre ninguna ventana modal. Si el Python no trae Tkinter o no hay pantalla
disponible, los tests se saltean.
"""
import pytest

tk = pytest.importorskip("tkinter")

from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo  # noqa: E402
from biblioteca.modelos.enumeraciones import EstadoFisico, TipoMaterial  # noqa: E402
from biblioteca.servicios import ServicioPrestamos, ServicioRemitos, ServicioSedes, ServicioSocios  # noqa: E402


@pytest.fixture
def mensajes(monkeypatch):
    """Registra los mensajes que la interfaz le mostraría al usuario."""
    from biblioteca.interfaz_grafica import componentes

    registro = {"errores": [], "informes": [], "avisos": []}
    monkeypatch.setattr(componentes, "mostrar_error", lambda mensaje, padre=None: registro["errores"].append(mensaje))
    monkeypatch.setattr(componentes, "informar", lambda mensaje, padre=None: registro["informes"].append(mensaje))
    monkeypatch.setattr(componentes, "avisar", lambda mensaje, padre=None: registro["avisos"].append(mensaje))
    monkeypatch.setattr(componentes, "confirmar", lambda mensaje, padre=None: True)
    return registro


@pytest.fixture
def responder(monkeypatch):
    """Permite indicar qué datos 'carga el usuario' en el próximo formulario."""
    from biblioteca.interfaz_grafica import componentes

    respuestas = []
    monkeypatch.setattr(componentes, "pedir_datos", lambda padre, titulo, campos: respuestas.pop(0))
    return respuestas


@pytest.fixture
def aplicacion(mensajes):
    from biblioteca.interfaz_grafica.aplicacion import Aplicacion

    try:
        app = Aplicacion()
    except tk.TclError:
        pytest.skip("No hay pantalla disponible para Tkinter")
    app.withdraw()
    yield app
    app.destroy()


def seleccionar(tabla, identificador):
    for item in tabla.arbol.get_children():
        if int(tabla.arbol.item(item, "values")[0]) == identificador:
            tabla.arbol.selection_set(item)
            tabla.arbol.update()
            return
    raise AssertionError(f"No está la fila {identificador}")


def test_la_ventana_tiene_una_pestania_por_area(aplicacion):
    assert list(aplicacion.pestanias) == [
        "Sedes", "Socios", "Catálogo", "Préstamos", "Reservas", "Remitos", "Devoluciones y multas", "Reportes",
    ]


def test_cargar_datos_de_ejemplo_llena_las_tablas(aplicacion, mensajes):
    aplicacion.cargar_datos()
    assert mensajes["informes"] == ["Se cargaron los datos de ejemplo."]
    for texto, filas_esperadas in [("Sedes", 3), ("Socios", 4), ("Préstamos", 2), ("Remitos", 4)]:
        aplicacion.mostrar_pestania(texto)
        assert len(aplicacion.pestanias[texto].tabla.filas()) == filas_esperadas


def test_se_registra_una_sede_desde_el_formulario(aplicacion, responder, mensajes):
    responder.append({"nombre": "Sede Oeste", "direccion": "Av. Sabattini 100", "telefono": None,
                      "email": None, "horario_atencion": None})
    pestania = aplicacion.pestanias["Sedes"]
    pestania.nueva()
    assert mensajes["informes"] == ["Sede registrada."]
    assert pestania.tabla.filas()[0][1] == "Sede Oeste"


def test_un_error_de_negocio_se_muestra_sin_cerrar_la_aplicacion(aplicacion, responder, mensajes):
    ServicioSocios().registrar_socio("30111222", "Ana", "Pérez")
    responder.append({"dni": "30.111.222", "nombre": "Otra", "apellido": "Persona", "email": None, "telefono": None})
    aplicacion.pestanias["Socios"].nuevo()
    assert mensajes["errores"] == ["Ya existe un socio con DNI 30111222."]


def test_las_acciones_que_requieren_una_fila_avisan_si_no_hay_seleccion(aplicacion, mensajes):
    aplicacion.pestanias["Remitos"].despachar()
    assert mensajes["avisos"] == ["Seleccione un remito en la lista."]


def test_la_seleccion_se_conserva_al_recargar_la_tabla(aplicacion, mensajes):
    cargar_datos_de_ejemplo()
    aplicacion.mostrar_pestania("Catálogo")
    pestania = aplicacion.pestanias["Catálogo"]
    seleccionar(pestania.tabla_libros, 1)
    pestania.actualizar()
    assert pestania.tabla_libros.id_seleccionado() == 1
    pestania.ver_disponibilidad()
    assert mensajes["avisos"] == []


def test_se_registra_un_libro_y_un_ejemplar_en_el_catalogo(aplicacion, responder, mensajes):
    sede = ServicioSedes().registrar_sede("Sede Centro", "Av. Colón 100")
    pestania = aplicacion.pestanias["Catálogo"]
    responder.append({"isbn": "9789500700011", "titulo": "Rayuela", "autor": "Julio Cortázar", "editorial": None,
                      "anio_publicacion": 1963, "tipo_material": TipoMaterial.LIBRO})
    pestania.nuevo_libro()
    seleccionar(pestania.tabla_libros, int(pestania.tabla_libros.filas()[0][0]))
    responder.append({"id_sede": sede.id, "codigo_inventario": "cen-0001"})
    pestania.nuevo_ejemplar()
    assert [fila[1] for fila in pestania.tabla_ejemplares.filas()] == ["CEN-0001"]


def test_el_remito_muestra_su_trayecto_y_la_transicion_invalida_se_informa(aplicacion, responder, mensajes):
    cargar_datos_de_ejemplo()
    pestania = aplicacion.pestanias["Remitos"]
    aplicacion.mostrar_pestania("Remitos")
    en_viaje = next(r for r in ServicioRemitos().listar_remitos() if r.nombre_estado == "EnTransito")
    seleccionar(pestania.tabla, en_viaje.id)
    assert [fila[2] for fila in pestania.tabla_trayecto.filas()] == [
        "Generado", "Empaquetado", "Despachado", "EnTransito",
    ]
    responder.append({"observacion": None})
    pestania.despachar()
    assert mensajes["errores"] == ["No se puede despachar un remito en estado EnTransito."]


def test_la_devolucion_usa_la_politica_de_multas_elegida(aplicacion, responder, mensajes):
    cargar_datos_de_ejemplo()
    pestania = aplicacion.pestanias["Devoluciones y multas"]
    pestania.selector_politica.set(next(texto for texto in pestania.estrategias if texto.startswith("Sin multa")))
    pestania.cambiar_politica()
    vencido = ServicioPrestamos().listar_vencidos()[0]
    responder.append({"id_prestamo": vencido.id, "estado_fisico": EstadoFisico.BUENO, "observaciones": None})
    pestania.registrar_devolucion()
    assert "multa" not in mensajes["informes"][-1]


def test_cada_reporte_se_muestra_sin_errores(aplicacion, mensajes):
    cargar_datos_de_ejemplo()
    pestania = aplicacion.pestanias["Reportes"]
    for _, mostrar in pestania.reportes:
        mostrar()
        assert pestania.titulo_actual
    assert mensajes["errores"] == []


def test_un_rango_de_fechas_invalido_se_avisa(aplicacion, mensajes):
    pestania = aplicacion.pestanias["Reportes"]
    pestania.desde.insert(0, "31/02/2026")
    pestania.reporte_mas_solicitados()
    assert mensajes["avisos"] == ["'31/02/2026' no es una fecha válida (dd/mm/aaaa)."]


def test_se_exporta_el_reporte_mostrado_a_pdf_y_csv(aplicacion, mensajes, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # los reportes se guardan en reportes_generados/ dentro de la carpeta actual
    cargar_datos_de_ejemplo()
    pestania = aplicacion.pestanias["Reportes"]
    pestania.reporte_tasa()
    pestania.exportar("pdf")
    assert pestania.ultimo_archivo.read_bytes().startswith(b"%PDF")
    assert pestania.ultimo_archivo.parent.name == "reportes_generados"
    pestania.exportar("csv")
    assert pestania.ultimo_archivo.suffix == ".csv"
    assert mensajes["errores"] == []


def test_exportar_sin_elegir_reporte_avisa(aplicacion, mensajes):
    aplicacion.pestanias["Reportes"].exportar("pdf")
    assert mensajes["avisos"] == ["Primero elija un reporte para mostrar."]


def test_el_selector_de_ejemplares_muestra_solo_los_de_la_sede_elegida(aplicacion, mensajes):
    from biblioteca.interfaz_grafica.componentes import Campo, Formulario
    from biblioteca.interfaz_grafica.opciones import opciones_ejemplares, opciones_sedes

    cargar_datos_de_ejemplo()
    sedes = ServicioSedes().listar_sedes()
    formulario = Formulario(aplicacion, "Préstamo local", [
        Campo("id_sede", "Sede", tipo="opcion", opciones=opciones_sedes()),
        Campo("id_ejemplar", "Ejemplar de la sede", tipo="opcion", depende_de="id_sede", opciones_segun=opciones_ejemplares),
    ])
    try:
        selector_sede, selector_ejemplar = formulario._controles["id_sede"], formulario._controles["id_ejemplar"]
        assert selector_ejemplar.cget("values") == ""
        for sede in sedes:
            selector_sede.set(sede.nombre)
            selector_sede.event_generate("<<ComboboxSelected>>")
            ejemplares = [texto for texto in selector_ejemplar.cget("values")]
            assert ejemplares
            assert all(f"({sede.nombre}," in texto for texto in ejemplares)
            assert selector_ejemplar.get() == ""
    finally:
        formulario.destroy()


def test_los_selectores_son_tan_anchos_como_su_opcion_mas_larga(aplicacion, mensajes):
    from tkinter import font

    from biblioteca.interfaz_grafica.componentes import Campo, Formulario
    from biblioteca.interfaz_grafica.opciones import opciones_ejemplares, opciones_sedes

    cargar_datos_de_ejemplo()
    formulario = Formulario(aplicacion, "Préstamo local", [
        Campo("id_sede", "Sede", tipo="opcion", opciones=opciones_sedes()),
        Campo("id_ejemplar", "Ejemplar de la sede", tipo="opcion", depende_de="id_sede", opciones_segun=opciones_ejemplares),
    ])
    try:
        selector = formulario._controles["id_ejemplar"]
        selector.update_idletasks()
        fuente = font.nametofont("TkTextFont")
        mas_larga = max(fuente.measure(texto) for texto, _ in opciones_ejemplares())
        assert selector.winfo_reqwidth() > mas_larga
    finally:
        formulario.destroy()
