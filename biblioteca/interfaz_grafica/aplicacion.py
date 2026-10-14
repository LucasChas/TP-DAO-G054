"""Ventana principal de la interfaz gráfica: una pestaña por área del sistema."""
import tkinter as tk
from tkinter import ttk

from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo
from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.pestania_catalogo import PestaniaCatalogo
from biblioteca.interfaz_grafica.pestania_devoluciones import PestaniaDevoluciones
from biblioteca.interfaz_grafica.pestania_prestamos import PestaniaPrestamos
from biblioteca.interfaz_grafica.pestania_remitos import PestaniaRemitos
from biblioteca.interfaz_grafica.pestania_reportes import PestaniaReportes
from biblioteca.interfaz_grafica.pestania_reservas import PestaniaReservas
from biblioteca.interfaz_grafica.pestania_sedes import PestaniaSedes
from biblioteca.interfaz_grafica.pestania_socios import PestaniaSocios
from biblioteca.servicios import ServicioDevoluciones


class Aplicacion(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Red de Bibliotecas - Préstamos Interbibliotecarios")
        self.geometry("1320x780")
        self.minsize(1050, 620)
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Treeview", rowheight=24)
        estilo.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))

        self._crear_menu()

        # Devoluciones y reportes comparten el servicio para usar la misma política de multas.
        servicio_devoluciones = ServicioDevoluciones()
        self.cuaderno = ttk.Notebook(self)
        self.cuaderno.pack(fill="both", expand=True, padx=8, pady=8)
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
            self.cuaderno.add(pestania, text=f"  {texto}  ")
        self.cuaderno.bind("<<NotebookTabChanged>>", lambda evento: self.pestania_actual().actualizar())

    def _crear_menu(self):
        barra = tk.Menu(self)
        archivo = tk.Menu(barra, tearoff=False)
        archivo.add_command(label="Cargar datos de ejemplo", command=self.cargar_datos)
        archivo.add_separator()
        archivo.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Archivo", menu=archivo)
        self.config(menu=barra)

    def pestania_actual(self):
        return self.nametowidget(self.cuaderno.select())

    def mostrar_pestania(self, texto):
        self.cuaderno.select(self.pestanias[texto])
        self.pestanias[texto].actualizar()

    def cargar_datos(self):
        if cargar_datos_de_ejemplo():
            c.informar("Se cargaron los datos de ejemplo.", self)
        else:
            c.avisar("La base ya tiene datos; no se cargó nada.", self)
        self.pestania_actual().actualizar()


def iniciar():
    Aplicacion().mainloop()
