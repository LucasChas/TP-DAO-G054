"""Componentes reutilizables de la interfaz gráfica: tablas, formularios y mensajes.

Las pestañas llaman a estas funciones a través del módulo (componentes.pedir_datos,
componentes.mostrar_error, ...) para que los tests puedan reemplazarlas sin abrir ventanas.
"""
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from tkinter import font, messagebox, ttk

from biblioteca.excepciones import ErrorDeNegocio


def formatear_fecha(valor, con_hora=False):
    if valor is None:
        return "-"
    return valor.strftime("%d/%m/%Y %H:%M" if con_hora else "%d/%m/%Y")


def formatear_pesos(monto):
    return f"${monto:,.2f}"


# --- Mensajes -----------------------------------------------------------------------------


def mostrar_error(mensaje, padre=None):
    messagebox.showerror("Operación rechazada", mensaje, parent=padre)


def informar(mensaje, padre=None):
    messagebox.showinfo("Listo", mensaje, parent=padre)


def avisar(mensaje, padre=None):
    messagebox.showwarning("Atención", mensaje, parent=padre)


def confirmar(mensaje, padre=None):
    return messagebox.askyesno("Confirmar", mensaje, parent=padre)


def ejecutar(accion, padre=None, mensaje_exito=None):
    """Ejecuta una operación de los servicios. Si se rompe una regla de negocio,
    muestra el motivo sin cerrar la aplicación y devuelve None."""
    try:
        resultado = accion()
    except ErrorDeNegocio as error:
        mostrar_error(str(error), padre)
        return None
    if mensaje_exito:
        informar(mensaje_exito(resultado) if callable(mensaje_exito) else mensaje_exito, padre)
    return resultado if resultado is not None else True


# --- Tabla --------------------------------------------------------------------------------


class Tabla(ttk.Frame):
    """Treeview con barra de desplazamiento. La primera columna es el identificador de la fila."""

    def __init__(self, padre, columnas, alto=12, anchos=None):
        super().__init__(padre)
        anchos = anchos or {}
        self._columnas = columnas
        self._anchos_minimos = {columna: anchos.get(columna, 70) for columna in columnas}
        self.arbol = ttk.Treeview(self, columns=columnas, show="headings", height=alto, selectmode="browse")
        for columna in columnas:
            self.arbol.heading(columna, text=columna, anchor="w")
            self.arbol.column(columna, width=anchos.get(columna, 120), anchor="w")
        barra = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview)
        self.arbol.configure(yscrollcommand=barra.set)
        self.arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def cargar(self, filas):
        """Reemplaza el contenido. Si la fila que estaba seleccionada sigue estando, queda seleccionada."""
        seleccionado = self.id_seleccionado()
        self.arbol.delete(*self.arbol.get_children())
        filas = [["-" if valor is None else valor for valor in fila] for fila in filas]
        for fila in filas:
            item = self.arbol.insert("", "end", values=fila)
            if seleccionado is not None and str(fila[0]) == str(seleccionado):
                self.arbol.selection_set(item)
        self._ajustar_anchos(filas)

    ANCHO_MAXIMO = 420

    def _ajustar_anchos(self, filas):
        """Ensancha cada columna lo necesario para que no se corte el texto, hasta un máximo."""
        medir = font.nametofont("TkDefaultFont").measure
        for indice, columna in enumerate(self._columnas):
            textos = [columna] + [str(fila[indice]) for fila in filas]
            ancho = max(medir(texto) for texto in textos) + 28
            self.arbol.column(columna, width=max(self._anchos_minimos[columna], min(ancho, self.ANCHO_MAXIMO)))

    def filas(self):
        return [self.arbol.item(item, "values") for item in self.arbol.get_children()]

    def seleccionar_primera(self):
        hijos = self.arbol.get_children()
        if hijos:
            self.arbol.selection_set(hijos[0])

    def id_seleccionado(self):
        seleccion = self.arbol.selection()
        if not seleccion:
            return None
        return int(self.arbol.item(seleccion[0], "values")[0])

    def al_seleccionar(self, funcion):
        self.arbol.bind("<<TreeviewSelect>>", lambda evento: funcion())


def id_seleccionado_o_aviso(tabla, padre, descripcion):
    """Devuelve el id de la fila elegida o avisa que hay que elegir una."""
    identificador = tabla.id_seleccionado()
    if identificador is None:
        avisar(f"Seleccione {descripcion} en la lista.", padre)
    return identificador


def barra_de_botones(padre, botones):
    """Crea una fila de botones a partir de una lista de (texto, comando)."""
    barra = ttk.Frame(padre)
    for texto, comando in botones:
        ttk.Button(barra, text=texto, command=comando).pack(side="left", padx=(0, 6))
    return barra


def centrar_sobre(ventana, padre):
    """Ubica una ventana secundaria centrada sobre la ventana principal."""
    ventana.update_idletasks()
    raiz = padre.winfo_toplevel()
    x = raiz.winfo_rootx() + (raiz.winfo_width() - ventana.winfo_reqwidth()) // 2
    y = raiz.winfo_rooty() + (raiz.winfo_height() - ventana.winfo_reqheight()) // 3
    ventana.geometry(f"+{max(x, 0)}+{max(y, 0)}")


# --- Formularios --------------------------------------------------------------------------


@dataclass
class Campo:
    """Un dato a pedir en un formulario.

    tipo puede ser "texto", "entero", "fecha" (dd/mm/aaaa) u "opcion"; las opciones
    son pares (texto que se muestra, valor que se devuelve).

    Una opción puede depender de otro campo del formulario: depende_de es la clave de
    ese campo y opciones_segun recibe su valor elegido y devuelve las opciones a mostrar.
    """

    clave: str
    etiqueta: str
    tipo: str = "texto"
    obligatorio: bool = False
    valor: object = None
    opciones: list = field(default_factory=list)
    depende_de: str = None
    opciones_segun: object = None


class Formulario(tk.Toplevel):
    """Ventana modal que pide los campos indicados y deja el resultado en self.resultado."""

    def __init__(self, padre, titulo, campos):
        super().__init__(padre)
        self.title(titulo)
        self.transient(padre)
        self.resizable(False, False)
        self.resultado = None
        self._campos = campos
        self._controles = {}

        marco = ttk.Frame(self, padding=14)
        marco.pack(fill="both", expand=True)
        for fila, campo in enumerate(campos):
            texto = campo.etiqueta + (" *" if campo.obligatorio else "")
            if campo.tipo == "fecha":
                texto += " (dd/mm/aaaa)"
            ttk.Label(marco, text=texto).grid(row=fila, column=0, sticky="w", padx=(0, 10), pady=4)
            control = self._crear_control(marco, campo)
            control.grid(row=fila, column=1, sticky="we", pady=4)
            self._controles[campo.clave] = control
        for campo in campos:
            if campo.depende_de:
                self._controles[campo.depende_de].bind(
                    "<<ComboboxSelected>>", lambda evento, campo=campo: self._actualizar_opciones(campo), add="+"
                )

        botones = ttk.Frame(marco)
        botones.grid(row=len(campos), column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right")
        ttk.Button(botones, text="Aceptar", command=self._aceptar).pack(side="right", padx=(0, 6))
        self.bind("<Return>", lambda evento: self._aceptar())
        self.bind("<Escape>", lambda evento: self.destroy())
        if campos:
            self._controles[campos[0].clave].focus_set()
        centrar_sobre(self, padre)
        self.grab_set()

    def _crear_control(self, marco, campo):
        if campo.tipo == "opcion":
            control = ttk.Combobox(marco, values=[texto for texto, _ in campo.opciones], state="readonly", width=50)
            for texto, valor in campo.opciones:
                if valor == campo.valor:
                    control.set(texto)
            return control
        control = ttk.Entry(marco, width=53)
        if campo.valor is not None:
            control.insert(0, formatear_fecha(campo.valor) if campo.tipo == "fecha" else str(campo.valor))
        return control

    def _actualizar_opciones(self, campo):
        """Vuelve a armar las opciones de un campo cuando cambia el campo del que depende."""
        texto_elegido = self._controles[campo.depende_de].get()
        del_que_depende = next(c for c in self._campos if c.clave == campo.depende_de)
        valor = dict(del_que_depende.opciones).get(texto_elegido)
        campo.opciones = campo.opciones_segun(valor) if valor is not None else []
        control = self._controles[campo.clave]
        control.configure(values=[texto for texto, _ in campo.opciones])
        control.set("")

    def _convertir(self, campo, texto):
        if campo.tipo == "entero":
            return int(texto)
        if campo.tipo == "fecha":
            return datetime.strptime(texto, "%d/%m/%Y").date()
        if campo.tipo == "opcion":
            return dict(campo.opciones)[texto]
        return texto

    def _aceptar(self):
        datos = {}
        for campo in self._campos:
            texto = self._controles[campo.clave].get().strip()
            if not texto:
                if campo.obligatorio:
                    avisar(f"Complete el dato '{campo.etiqueta}'.", self)
                    return
                datos[campo.clave] = None
                continue
            try:
                datos[campo.clave] = self._convertir(campo, texto)
            except ValueError:
                avisar(f"'{texto}' no es un valor válido para '{campo.etiqueta}'.", self)
                return
        self.resultado = datos
        self.destroy()


def pedir_datos(padre, titulo, campos):
    """Abre un formulario modal y devuelve un diccionario con los datos, o None si se canceló."""
    formulario = Formulario(padre, titulo, campos)
    padre.wait_window(formulario)
    return formulario.resultado


def mostrar_tabla_en_ventana(padre, titulo, columnas, filas, anchos=None):
    """Ventana de solo lectura con una tabla, por ejemplo para la disponibilidad de un libro."""
    ventana = tk.Toplevel(padre)
    ventana.title(titulo)
    ventana.transient(padre)
    marco = ttk.Frame(ventana, padding=12)
    marco.pack(fill="both", expand=True)
    tabla = Tabla(marco, columnas, alto=max(3, min(len(filas), 10)), anchos=anchos)
    tabla.pack(fill="both", expand=True)
    tabla.cargar(filas)
    ttk.Button(marco, text="Cerrar", command=ventana.destroy).pack(anchor="e", pady=(10, 0))
    centrar_sobre(ventana, padre)
    return ventana
