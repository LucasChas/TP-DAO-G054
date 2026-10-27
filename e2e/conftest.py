"""Fixtures de las pruebas E2E.

Cada prueba arranca la aplicación gráfica real sobre una base SQLite en un
archivo temporal nuevo, así los datos son aislados y reproducibles. Las
precondiciones ("Dado ...") se cargan con los servicios del sistema, que
aplican las mismas validaciones que la interfaz.

Ejecutar con una pantalla virtual:
    xvfb-run -a -s "-screen 0 1320x780x24" python -m pytest e2e -v
Para guardar capturas:
    E2E_CAPTURAS=docs/capturas xvfb-run -a -s "-screen 0 1320x780x24" python -m pytest e2e -v
"""
import os
import re
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

tk = pytest.importorskip("tkinter")

from biblioteca.configuracion.base_de_datos import configurar_base_de_datos, crear_tablas  # noqa: E402
from biblioteca.modelos.enumeraciones import TipoMaterial  # noqa: E402
from biblioteca.servicios import ServicioCatalogo, ServicioSedes, ServicioSocios  # noqa: E402

from e2e.driver import ALTO, ANCHO, DriverGUI  # noqa: E402


@pytest.fixture
def base(tmp_path, monkeypatch):
    """Base SQLite nueva en un archivo temporal; los reportes exportados también van ahí."""
    configurar_base_de_datos(f"sqlite:///{tmp_path / 'e2e.db'}")
    crear_tablas()
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _prefijo(nombre_test):
    coincidencia = re.match(r"test_(cp|cn)(\d+)", nombre_test)
    return f"{coincidencia.group(1).upper()}-{coincidencia.group(2)}_" if coincidencia else ""


@pytest.fixture
def gui(base, request):
    if not os.environ.get("DISPLAY"):
        pytest.skip("No hay pantalla: ejecutar con xvfb-run")
    from biblioteca.interfaz_grafica.aplicacion import Aplicacion

    try:
        app = Aplicacion()
    except tk.TclError:
        pytest.skip("No hay pantalla disponible para Tkinter")
    app.geometry(f"{ANCHO}x{ALTO}+0+0")
    app.update()
    driver = DriverGUI(app, os.environ.get("E2E_CAPTURAS"), _prefijo(request.node.name))
    yield driver
    driver.app.destroy()  # puede ser otra ventana si la prueba reinicia el programa


HOY = date.today()


def hace(dias):
    return HOY - timedelta(days=dias)


@pytest.fixture
def red(base):
    """Datos de prueba fijos: tres sedes, tres socios (uno inhabilitado),
    tres libros de distinto tipo de material y cinco ejemplares."""
    sedes, socios, catalogo = ServicioSedes(), ServicioSocios(), ServicioCatalogo()
    centro = sedes.registrar_sede("Sede Centro", "Av. Colón 100", "351-4000000", "centro@biblio.org", "Lun a Vie 8 a 20")
    norte = sedes.registrar_sede("Sede Norte", "Av. Monseñor Pablo Cabrera 3000", "351-4111111")
    sur = sedes.registrar_sede("Sede Sur", "Av. Vélez Sarsfield 4500")
    ana = socios.registrar_socio("30111222", "Ana", "Pérez", "ana@correo.com")
    juan = socios.registrar_socio("28999888", "Juan", "Gómez")
    lia = socios.registrar_socio("33444555", "Lía", "Torres")
    socios.inhabilitar_socio(lia.id, "Deuda de cuota social")
    rayuela = catalogo.registrar_libro("9789500700016", "Rayuela", "Julio Cortázar", "Sudamericana", 1963)
    revista = catalogo.registrar_libro("9771234567003", "Revista Ñ", "Varios", None, 2025, TipoMaterial.REVISTA)
    diccionario = catalogo.registrar_libro("9788423968657", "Diccionario de la lengua", "RAE", "Espasa", 2014, TipoMaterial.CONSULTA)
    ejemplares = {
        codigo: catalogo.registrar_ejemplar(libro.id, sede.id, codigo)
        for libro, sede, codigo in [
            (rayuela, centro, "CEN-0001"),
            (rayuela, norte, "NOR-0001"),
            (diccionario, centro, "CEN-0002"),
            (revista, sur, "SUR-0001"),
            (rayuela, sur, "SUR-0002"),
        ]
    }
    return SimpleNamespace(
        centro=centro, norte=norte, sur=sur, ana=ana, juan=juan, lia=lia,
        rayuela=rayuela, revista=revista, diccionario=diccionario, ej=ejemplares,
    )
