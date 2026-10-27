"""Punto de entrada del sistema de préstamos interbibliotecarios.

    python main.py             interfaz de consola
    python main.py --grafica   interfaz gráfica (Tkinter)
"""
import sys

from biblioteca.configuracion.base_de_datos import configurar_base_de_datos, crear_tablas
from biblioteca.interfaz.menu_principal import menu_principal


def main():
    configurar_base_de_datos()
    crear_tablas()
    if "--grafica" in sys.argv[1:]:
        # Se importa acá para que la consola funcione aunque el Python instalado no traiga Tkinter.
        from biblioteca.interfaz_grafica.aplicacion import iniciar

        iniciar()
        return
    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")


if __name__ == "__main__":
    main()
