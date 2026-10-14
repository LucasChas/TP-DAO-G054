"""Menú principal del sistema."""
from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo
from biblioteca.interfaz.consola import consola, mostrar_aviso, mostrar_error, mostrar_exito, mostrar_titulo
from biblioteca.interfaz.menu_catalogo import menu_catalogo
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
        OPCIONES[int(opcion) - 1][1]()
