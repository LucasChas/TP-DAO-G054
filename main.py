"""Punto de entrada del sistema de préstamos interbibliotecarios.

    python main.py    abre la interfaz gráfica (Tkinter)
"""
from biblioteca.configuracion.base_de_datos import configurar_base_de_datos, crear_tablas
from biblioteca.interfaz_grafica.aplicacion import iniciar


def main():
    configurar_base_de_datos()
    crear_tablas()
    iniciar()


if __name__ == "__main__":
    main()
