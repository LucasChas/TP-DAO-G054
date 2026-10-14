"""Menú principal del sistema."""
from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo
from biblioteca.excepciones import ErrorDeNegocio
from biblioteca.interfaz.consola import consola, mostrar_aviso, mostrar_error, mostrar_exito, mostrar_titulo
from biblioteca.interfaz.menu_catalogo import menu_catalogo
from biblioteca.interfaz.menu_devoluciones import menu_devoluciones
from biblioteca.interfaz.menu_disponibilidad import consultar_disponibilidad
from biblioteca.interfaz.menu_prestamos import menu_prestamos
from biblioteca.interfaz.menu_remitos import menu_remitos
from biblioteca.interfaz.menu_reportes import menu_reportes
from biblioteca.interfaz.menu_reservas import menu_reservas
from biblioteca.interfaz.menu_sedes import menu_sedes
from biblioteca.interfaz.menu_socios import menu_socios


def cargar_datos():
    if cargar_datos_de_ejemplo():
        mostrar_exito("Se cargaron los datos de ejemplo.")
    else:
        mostrar_aviso("La base ya tiene datos; no se cargó nada.")


OPCIONES = [
    ("Sedes", menu_sedes),
    ("Socios", menu_socios),
    ("Catálogo", menu_catalogo),
    ("Consultar disponibilidad", consultar_disponibilidad),
    ("Préstamos", menu_prestamos),
    ("Reservas", menu_reservas),
    ("Remitos", menu_remitos),
    ("Devoluciones y multas", menu_devoluciones),
    ("Reportes", menu_reportes),
    ("Cargar datos de ejemplo", cargar_datos),
]


def menu_principal():
    while True:
        mostrar_titulo("Red de Bibliotecas - Préstamos Interbibliotecarios")
        for numero, (texto, _) in enumerate(OPCIONES, start=1):
            consola.print(f"  {numero}. {texto}")
        consola.print("  0. Salir")
        opcion = consola.input("\nSeleccione una opción: ").strip()
        if opcion == "0":
            consola.print("¡Hasta luego!")
            return
        if not opcion.isdigit() or not 1 <= int(opcion) <= len(OPCIONES):
            mostrar_error("Opción inválida.")
            continue
        try:
            OPCIONES[int(opcion) - 1][1]()
        except ErrorDeNegocio as error:
            mostrar_error(error)
