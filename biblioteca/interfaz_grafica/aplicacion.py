"""Ventana principal de la interfaz gráfica: una pestaña por área del sistema.

Arriba hay una banda con el nombre del sistema y cuatro indicadores de la red
(préstamos en curso, vencidos, envíos en tránsito y multas impagas); abajo, una
barra de estado con el resultado de la última operación.
"""
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from biblioteca.configuracion import base_de_datos
from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo
from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica import tema
from biblioteca.interfaz_grafica.pestania_catalogo import PestaniaCatalogo
from biblioteca.interfaz_grafica.pestania_devoluciones import PestaniaDevoluciones
from biblioteca.interfaz_grafica.pestania_prestamos import EN_CURSO, PestaniaPrestamos
from biblioteca.interfaz_grafica.pestania_remitos import PestaniaRemitos
from biblioteca.interfaz_grafica.pestania_reportes import PestaniaReportes
from biblioteca.interfaz_grafica.pestania_reservas import PestaniaReservas
from biblioteca.interfaz_grafica.pestania_sedes import PestaniaSedes
from biblioteca.interfaz_grafica.pestania_socios import PestaniaSocios
from biblioteca.servicios import ServicioDevoluciones, ServicioPrestamos, ServicioRemitos

TITULO = "Red de Bibliotecas - Préstamos Interbibliotecarios"

ATAJOS = (
    ("Ctrl+1 … Ctrl+8", "Ir a la pestaña correspondiente"),
    ("F5", "Actualizar la pestaña visible"),
    ("Doble clic / Enter", "Modificar la fila elegida (sedes, socios y libros)"),
    ("Clic en un encabezado", "Ordenar la tabla por esa columna"),
    ("Enter en un formulario", "Aceptar"),
    ("Esc en un formulario", "Cancelar"),
    ("Ctrl+Q", "Salir"),
)


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO)
        self.geometry("1320x780")
        self.minsize(1050, 620)
        tema.aplicar(self)

        self._crear_menu()
        self._crear_cabecera()
        self._crear_barra_de_estado()

        # Devoluciones y reportes comparten el servicio para usar la misma política de multas.
        servicio_devoluciones = ServicioDevoluciones()
        self.servicio_devoluciones = servicio_devoluciones
        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True, padx=10, pady=(8, 0))
        self.pestanias = {
            "Sedes": PestaniaSedes(self.cuaderno),
            "Socios": PestaniaSocios(self.cuaderno),
            "Catálogo": PestaniaCatalogo(self.cuaderno),
            "Préstamos": PestaniaPrestamos(self.cuaderno),
            "Reservas": PestaniaReservas(self.cuaderno),
            "Remitos": PestaniaRemitos(self.cuaderno),
            "Devoluciones y multas": PestaniaDevoluciones(self.cuaderno, servicio_devoluciones),
            "Reportes": PestaniaReportes(self.cuaderno, servicio_devoluciones),
        }
        for texto, pestania in self.pestanias.items():
            self.cuaderno.add(pestania, text=texto)
        self.cuaderno.bind("<<NotebookTabChanged>>", lambda evento: self.actualizar_todo())
        self._crear_atajos()
        self.actualizar_indicadores()

    # --- Armado de la ventana ----------------------------------------------------------

    def _crear_menu(self):
        barra = tk.Menu(self)
        archivo = tk.Menu(barra, tearoff=False)
        archivo.add_command(label="Cargar datos de ejemplo", command=self.cargar_datos)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.destroy, accelerator="Ctrl+Q")
        barra.add_cascade(label="Archivo", menu=archivo)

        ver = tk.Menu(barra, tearoff=False)
        ver.add_command(label="Actualizar", command=self.actualizar_todo, accelerator="F5")
        ver.add_separator()
        for numero, texto in enumerate(("Sedes", "Socios", "Catálogo", "Préstamos", "Reservas", "Remitos",
                                        "Devoluciones y multas", "Reportes"), start=1):
            ver.add_command(label=texto, accelerator=f"Ctrl+{numero}",
                            command=lambda texto=texto: self.mostrar_pestania(texto))
        barra.add_cascade(label="Ver", menu=ver)

        ayuda = tk.Menu(barra, tearoff=False)
        ayuda.add_command(label="Atajos de teclado", command=self.mostrar_atajos)
        ayuda.add_command(label="Acerca del sistema", command=self.mostrar_acerca_de)
        barra.add_cascade(label="Ayuda", menu=ayuda)
        self.config(menu=barra)

    def _crear_cabecera(self):
        cabecera = ttk.Frame(self, style="Cabecera.TFrame", padding=(18, 12))
        cabecera.pack(fill="x")
        titulos = ttk.Frame(cabecera, style="Cabecera.TFrame")
        titulos.pack(side="left")
        ttk.Label(titulos, text="Red de Bibliotecas", style="Cabecera.TLabel").pack(anchor="w")
        ttk.Label(titulos, text="Sistema de préstamos interbibliotecarios", style="CabeceraSuave.TLabel").pack(anchor="w")

        self._indicadores = {}
        for clave, texto in (("impagas", "Multas impagas"), ("transito", "Envíos en tránsito"),
                             ("vencidos", "Préstamos vencidos"), ("en_curso", "Préstamos en curso")):
            marco = ttk.Frame(cabecera, style="Indicador.TFrame", padding=(22, 0, 0, 0))
            marco.pack(side="right")
            valor = ttk.Label(marco, text="-", style="IndicadorValor.TLabel")
            valor.pack(anchor="e")
            ttk.Label(marco, text=texto, style="IndicadorTexto.TLabel").pack(anchor="e")
            self._indicadores[clave] = valor

    def _crear_barra_de_estado(self):
        barra = ttk.Frame(self, style="Estado.TFrame", padding=(12, 5))
        barra.pack(side="bottom", fill="x")
        ttk.Separator(self).pack(side="bottom", fill="x")
        self.estado = ttk.Label(barra, text="Listo.", style="Estado.TLabel")
        self.estado.pack(side="left")
        url = base_de_datos.motor.url if base_de_datos.motor is not None else None
        en_memoria = url is not None and url.database in (None, "", ":memory:")
        texto_base = "" if url is None else f"Base de datos: {'en memoria' if en_memoria else url.database}"
        ttk.Label(barra, text=texto_base, style="Estado.TLabel").pack(side="right")

    def _crear_atajos(self):
        for numero, pestania in enumerate(self.pestanias, start=1):
            self.bind_all(f"<Control-Key-{numero}>", lambda evento, pestania=pestania: self.mostrar_pestania(pestania))
        self.bind_all("<F5>", lambda evento: self.actualizar_todo())
        self.bind_all("<Control-q>", lambda evento: self.destroy())

    # --- Navegación y estado -----------------------------------------------------------

    def pestania_actual(self):
        return self.nametowidget(self.cuaderno.select())

    def mostrar_pestania(self, texto):
        self.cuaderno.select(self.pestanias[texto])
        self.pestanias[texto].actualizar()

    def actualizar_todo(self):
        self.pestania_actual().actualizar()
        self.actualizar_indicadores()

    def actualizar_indicadores(self):
        """Recalcula los indicadores de la cabecera con los servicios."""
        try:
            valores = {
                "en_curso": len(ServicioPrestamos().listar_prestamos(EN_CURSO)),
                "vencidos": len(ServicioPrestamos().listar_vencidos()),
                "transito": len(ServicioRemitos().listar_remitos(solo_en_curso=True)),
                "impagas": len(self.servicio_devoluciones.listar_multas_impagas()),
            }
        except Exception:  # noqa: BLE001 - los indicadores son informativos, no deben cortar la interfaz
            return
        for clave, valor in valores.items():
            alerta = clave in ("vencidos", "impagas") and valor > 0
            self._indicadores[clave].configure(
                text=str(valor), style="IndicadorValorAlerta.TLabel" if alerta else "IndicadorValor.TLabel"
            )

    def registrar_actividad(self, mensaje, es_error=False):
        """La llaman los componentes después de cada operación: actualiza la barra de estado y los indicadores."""
        if mensaje:
            hora = datetime.now().strftime("%H:%M")
            self.estado.configure(text=f"{hora}  ·  {mensaje}", foreground=tema.PELIGRO if es_error else tema.TEXTO_SUAVE)
        if not es_error:
            self.actualizar_indicadores()

    def cargar_datos(self):
        if cargar_datos_de_ejemplo():
            self.registrar_actividad("Se cargaron los datos de ejemplo.")
            c.informar("Se cargaron los datos de ejemplo.", self)
        else:
            c.avisar("La base ya tiene datos; no se cargó nada.", self)
        self.actualizar_todo()

    # --- Ayuda -------------------------------------------------------------------------

    def mostrar_atajos(self):
        c.mostrar_tabla_en_ventana(self, "Atajos de teclado", ("Atajo", "Acción"), ATAJOS, anchos={"Atajo": 170})

    def mostrar_acerca_de(self):
        c.informar(
            "Red de Bibliotecas - Sistema de préstamos interbibliotecarios.\n\n"
            "TP Integrador 2026 - Desarrollo de Aplicaciones con Objetos\n"
            "UTN FRC - Grupo G054",
            self,
        )


def iniciar():
    Aplicacion().mainloop()
