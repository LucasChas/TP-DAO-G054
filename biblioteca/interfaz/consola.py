"""Funciones de entrada y salida por consola compartidas por todos los menús."""
from rich.console import Console
from rich.table import Table

from biblioteca.excepciones import ErrorDeNegocio

consola = Console()


def mostrar_titulo(titulo):
    consola.print()
    consola.rule(f"[bold cyan]{titulo}")


def mostrar_exito(mensaje):
    consola.print(f"[green]✔ {mensaje}")


def mostrar_error(mensaje):
    consola.print(f"[red]✘ Error: {mensaje}")


def mostrar_aviso(mensaje):
    consola.print(f"[yellow]{mensaje}")


def mostrar_tabla(titulo, columnas, filas):
    """Muestra una tabla con rich. Si no hay filas, avisa en lugar de mostrar una tabla vacía."""
    if not filas:
        mostrar_aviso(f"{titulo}: no hay datos para mostrar.")
        return
    tabla = Table(title=titulo, header_style="bold magenta")
    for columna in columnas:
        tabla.add_column(columna)
    for fila in filas:
        tabla.add_row(*[("-" if valor is None else str(valor)) for valor in fila])
    consola.print(tabla)


def pedir_texto(mensaje, obligatorio=False):
    """Pide un texto. Si no es obligatorio y se deja vacío, devuelve None."""
    while True:
        texto = consola.input(f"{mensaje}: ").strip()
        if texto:
            return texto
        if not obligatorio:
            return None
        mostrar_error("Este dato es obligatorio.")


def pedir_entero(mensaje, obligatorio=True):
    """Pide un número entero; repite la pregunta hasta que el valor sea válido."""
    while True:
        texto = pedir_texto(mensaje, obligatorio)
        if texto is None:
            return None
        try:
            return int(texto)
        except ValueError:
            mostrar_error(f"'{texto}' no es un número entero.")


def pedir_opcion_enum(mensaje, tipo_enum, obligatorio=True):
    """Muestra las constantes de un Enum numeradas y devuelve la elegida."""
    valores = list(tipo_enum)
    for numero, valor in enumerate(valores, start=1):
        consola.print(f"  {numero}. {valor.value}")
    while True:
        numero = pedir_entero(mensaje, obligatorio)
        if numero is None:
            return None
        if 1 <= numero <= len(valores):
            return valores[numero - 1]
        mostrar_error("Opción fuera de rango.")


def confirmar(mensaje):
    return consola.input(f"{mensaje} (s/n): ").strip().lower() == "s"


def ejecutar_menu(titulo, opciones):
    """Muestra un menú numerado hasta que el usuario elige 0.

    opciones es una lista de tuplas (texto, funcion). Los errores de negocio
    se informan sin cortar el programa, como pide la cátedra.
    """
    while True:
        mostrar_titulo(titulo)
        for numero, (texto, _) in enumerate(opciones, start=1):
            consola.print(f"  {numero}. {texto}")
        consola.print("  0. Volver")
        opcion = consola.input("\nSeleccione una opción: ").strip()
        if opcion == "0":
            return
        if not opcion.isdigit() or not 1 <= int(opcion) <= len(opciones):
            mostrar_error("Opción inválida.")
            continue
        _, funcion = opciones[int(opcion) - 1]
        try:
            funcion()
        except ErrorDeNegocio as error:
            mostrar_error(error)
