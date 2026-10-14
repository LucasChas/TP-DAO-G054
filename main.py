"""Punto de entrada del sistema de préstamos interbibliotecarios."""
from biblioteca.configuracion.base_de_datos import configurar_base_de_datos, crear_tablas
from biblioteca.interfaz.menu_principal import menu_principal


def main():
    configurar_base_de_datos()
    crear_tablas()
    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")


if __name__ == "__main__":
    main()
