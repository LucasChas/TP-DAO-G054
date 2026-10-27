"""E2E de los reportes con su exportación, de la carga de datos de ejemplo y de la interfaz de consola.
Escenarios en e2e/features/reportes_y_general.feature."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from e2e.driver import Mensaje

RAIZ = Path(__file__).resolve().parent.parent
REPORTES = [
    ("1. Préstamos activos y tránsito", "activos", "Préstamos activos y material en tránsito"),
    ("2. Vencidos y multas", "vencidos", "Préstamos vencidos y multas acumuladas"),
    ("3. Libros más solicitados", "solicitados", "Libros más solicitados para préstamos inter-sedes"),
    ("4. Movimiento entre sedes", "movimientos", "Movimiento de ejemplares entre sedes"),
    ("5. Tasa de envíos e incidencias", "tasa", "Tasa de envíos exitosos e incidencias"),
]


def test_cp26_cargar_datos_de_ejemplo_desde_el_menu(gui, base):
    mensajes = gui.menu("Archivo", "Cargar datos de ejemplo", Mensaje(captura="01_datos_cargados"))
    assert mensajes == [("Listo", "Se cargaron los datos de ejemplo.")]
    assert len(gui.filas(gui.ir_a("Sedes").tabla)) == 3
    remitos = gui.ir_a("Remitos")
    assert [(f["Número"], f["Sentido"], f["Estado"]) for f in gui.filas(remitos.tabla)] == [
        ("R-000001", "Ida", "Cerrado"), ("R-000002", "Ida", "Cerrado"),
        ("R-000003", "Retorno", "Cerrado"), ("R-000004", "Ida", "EnTransito"),
    ]
    # Trayecto de cada tipo de remito de ejemplo: ida entregada, ida con daño, retorno y envío en viaje.
    for numero in ("R-000001", "R-000002", "R-000003", "R-000004"):
        gui.seleccionar(remitos.tabla, "Número", numero)
        gui.capturar(f"02_trayecto_{numero}")


def test_cp27_ver_y_exportar_los_cinco_reportes(gui, base):
    gui.menu("Archivo", "Cargar datos de ejemplo", Mensaje())
    pestania = gui.ir_a("Reportes")
    destino = os.environ.get("E2E_EJEMPLOS")
    for numero, (boton, clave, titulo) in enumerate(REPORTES, start=1):
        gui.clic(boton)
        assert pestania.titulo_actual == titulo
        gui.capturar(f"{numero:02d}_reporte_{clave}")
        for formato in ("pdf", "csv"):
            mensajes = gui.clic(f"Exportar a PDF (con gráfico)" if formato == "pdf" else "Exportar a CSV",
                                Mensaje(captura=f"{numero:02d}_exportado_{formato}" if formato == "pdf" else None))
            assert mensajes[0][1].startswith("Reporte exportado en:")
            ruta = pestania.ultimo_archivo
            assert ruta.exists() and ruta.stat().st_size > 0 and ruta.name.startswith(f"reporte_{clave}_")
            if destino:
                Path(destino).mkdir(parents=True, exist_ok=True)
                shutil.copy(ruta, Path(destino) / f"reporte_{clave}.{formato}")


def test_cp28_filtrar_reportes_por_rango_de_fechas(gui, base):
    gui.menu("Archivo", "Cargar datos de ejemplo", Mensaje())
    pestania = gui.ir_a("Reportes")
    pestania.desde.insert(0, "01/01/2000")
    pestania.hasta.insert(0, "31/12/2000")
    gui.clic("4. Movimiento entre sedes")
    gui.capturar("01_rango_sin_movimientos")
    textos = [w.cget("text") for w in pestania.contenido.winfo_children() if w.winfo_class() == "TLabel"]
    assert "Tiempo promedio de tránsito en la red: -" in textos


def test_cn41_fecha_invalida_en_el_filtro_de_reportes(gui, base):
    pestania = gui.ir_a("Reportes")
    pestania.desde.insert(0, "32/13/2026")
    mensajes = gui.clic("3. Libros más solicitados", Mensaje(titulo="Atención", captura="01_fecha_invalida"))
    assert mensajes == [("Atención", "'32/13/2026' no es una fecha válida (dd/mm/aaaa).")]


def test_cn42_cargar_datos_de_ejemplo_dos_veces(gui, base):
    gui.menu("Archivo", "Cargar datos de ejemplo", Mensaje())
    mensajes = gui.menu("Archivo", "Cargar datos de ejemplo", Mensaje(titulo="Atención", captura="01_ya_hay_datos"))
    assert mensajes == [("Atención", "La base ya tiene datos; no se cargó nada.")]


def _consola(base, entradas):
    """Ejecuta `python main.py` (interfaz de consola) en la carpeta temporal, con las entradas indicadas."""
    entorno = dict(os.environ, PYTHONPATH=str(RAIZ), COLUMNS="160", TERM="dumb")
    resultado = subprocess.run([sys.executable, str(RAIZ / "main.py")], input="\n".join(entradas) + "\n",
                               capture_output=True, text=True, cwd=base, env=entorno, timeout=60)
    salida = resultado.stdout
    if os.environ.get("E2E_CAPTURAS"):
        Path(os.environ["E2E_CAPTURAS"]).mkdir(parents=True, exist_ok=True)
    return resultado.returncode, salida


def test_cp29_consola_carga_datos_y_lista_sedes(base):
    codigo, salida = _consola(base, ["10", "1", "1", "0", "0"])
    assert codigo == 0
    assert "Se cargaron los datos de ejemplo." in salida
    assert "Sedes de la red" in salida and "Biblioteca Central" in salida and "Sede Norte" in salida
    assert "¡Hasta luego!" in salida
    _guardar_salida("CP-29_salida_consola.txt", salida)


def test_cn43_consola_opcion_invalida_y_error_de_negocio(base):
    # Opción inexistente y, en Socios > Registrar socio, un DNI inválido: el error se muestra y el programa sigue.
    codigo, salida = _consola(base, ["99", "2", "3", "12ab", "Ana", "Pérez", "", "", "0", "0"])
    assert codigo == 0
    assert "Opción inválida." in salida
    assert "El DNI '12ab' no es válido: debe tener 7 u 8 dígitos." in salida
    assert "¡Hasta luego!" in salida
    _guardar_salida("CN-43_salida_consola.txt", salida)


def _guardar_salida(nombre, salida):
    carpeta = os.environ.get("E2E_CAPTURAS")
    if carpeta:
        (Path(carpeta) / nombre).write_text(salida, encoding="utf-8")
