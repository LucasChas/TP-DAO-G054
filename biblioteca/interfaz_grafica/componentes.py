"""Componentes reutilizables de la interfaz gráfica: tablas, formularios y mensajes.

Las pestañas llaman a estas funciones a través del módulo (componentes.pedir_datos,
componentes.mostrar_error, ...) para que los tests puedan reemplazarlas sin abrir ventanas.
"""
import re
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from tkinter import font, messagebox, ttk

from biblioteca.excepciones import ErrorDeNegocio
from biblioteca.interfaz_grafica import tema


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


def notificar_ventana(padre, mensaje, es_error=False):
    """Avisa a la ventana principal (si la hay) que pasó algo, para la barra de estado y los indicadores."""
    if padre is None:
        return
    try:
        raiz = padre.winfo_toplevel()
        while getattr(raiz, "master", None) is not None and not hasattr(raiz, "registrar_actividad"):
            raiz = raiz.master.winfo_toplevel()
    except tk.TclError:
        return
    registrar = getattr(raiz, "registrar_actividad", None)
    if registrar:
        registrar(mensaje, es_error)


def ejecutar(accion, padre=None, mensaje_exito=None):
    """Ejecuta una operación de los servicios. Si se rompe una regla de negocio,
    muestra el motivo sin cerrar la aplicación y devuelve None."""
    try:
        resultado = accion()
    except ErrorDeNegocio as error:
        notificar_ventana(padre, f"Operación rechazada: {error}", es_error=True)
        mostrar_error(str(error), padre)
        return None
    texto = None
    if mensaje_exito:
        texto = mensaje_exito(resultado) if callable(mensaje_exito) else mensaje_exito
    notificar_ventana(padre, texto.splitlines()[0] if texto else None)
    if texto:
        informar(texto, padre)
    return resultado if resultado is not None else True


# --- Tabla --------------------------------------------------------------------------------


_NUMERO = re.compile(r"^-?\$?-?[\d.,]+(\s*(h|%|días?))?$")


def _clave_de_orden(texto):
    """Clave para ordenar una columna: números, montos, fechas y textos, con los vacíos al final."""
    texto = str(texto).strip()
    if texto in ("", "-"):
        return (2, "")
    for formato in ("%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return (0, datetime.strptime(texto, formato).timestamp())
        except ValueError:
            pass
    if _NUMERO.match(texto):
        limpio = re.sub(r"[^\d.,-]", "", texto).replace(",", "")
        try:
            return (0, float(limpio))
        except ValueError:
            pass
    return (1, texto.casefold())


def _barra_automatica(barra):
    """Devuelve un 'set' para una barra de desplazamiento que se oculta cuando no hace falta."""
    def fijar(primero, ultimo):
        if float(primero) <= 0.0 and float(ultimo) >= 1.0:
            barra.grid_remove()
        else:
            barra.grid()
        barra.set(primero, ultimo)
    return fijar


class Tabla(ttk.Frame):
    """Treeview con barras de desplazamiento que aparecen solo si hacen falta.

    - columnas: todas las columnas de cada fila. La primera es el identificador.
    - ocultas: columnas que se guardan en la fila pero no se muestran (por ejemplo "Id").
    - columna_estado: si se indica, esa columna se muestra primera, con un punto de color
      según el estado (ver tema.CATEGORIA_POR_ESTADO). El texto de la fila queda siempre oscuro.

    Un clic en el encabezado ordena por esa columna y otro clic invierte el orden.
    """

    ANCHO_MAXIMO = 420
    FLECHAS = {False: " ▲", True: " ▼"}

    def __init__(self, padre, columnas, alto=12, anchos=None, mensaje_vacio="No hay datos para mostrar.",
                 ocultas=("Id",), columna_estado=None):
        super().__init__(padre, style="Panel.TFrame")
        anchos = anchos or {}
        self._columnas = tuple(columnas)
        self._anchos_minimos = {columna: anchos.get(columna, 70) for columna in columnas}
        self._orden = None  # (columna, descendente)
        self._filas = []
        self._estado = columna_estado if columna_estado in self._columnas else None
        self._indice_estado = self._columnas.index(self._estado) if self._estado else None
        self._visibles = [c for c in self._columnas if c not in ocultas and c != self._estado]
        self._puntos = {}
        self.arbol = ttk.Treeview(self, columns=self._columnas, displaycolumns=self._visibles,
                                  show="tree headings" if self._estado else "headings", height=alto,
                                  selectmode="browse")
        if self._estado:
            self.arbol.heading("#0", text=self._estado, anchor="w", command=lambda: self.ordenar_por(self._estado))
            self.arbol.column("#0", width=anchos.get(self._estado, 130), anchor="w", stretch=False)
        for columna in self._columnas:
            self.arbol.heading(columna, text=columna, anchor="w", command=lambda columna=columna: self.ordenar_por(columna))
            self.arbol.column(columna, width=anchos.get(columna, 120), anchor="w", stretch=True)
        self.arbol.tag_configure("alterna", background=tema.SUPERFICIE_SUAVE)
        vertical = ttk.Scrollbar(self, orient="vertical", command=self.arbol.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.arbol.xview)
        self.arbol.configure(yscrollcommand=_barra_automatica(vertical), xscrollcommand=_barra_automatica(horizontal))
        self.arbol.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._vacio = ttk.Label(self.arbol, text=mensaje_vacio, style="Vacio.TLabel")
        self._vacio.place(relx=0.5, rely=0.55, anchor="center")

    def _punto(self, estado):
        color = tema.color_de_estado(estado)
        if color not in self._puntos:
            self._puntos[color] = tema.punto(self, color)
        return self._puntos[color]

    def cargar(self, filas):
        """Reemplaza el contenido. Si la fila que estaba seleccionada sigue estando, queda seleccionada."""
        # Se compara como texto: en tablas como el trayecto del remito la primera columna es una fecha, no un id.
        seleccion = self.arbol.selection()
        seleccionado = self.arbol.item(seleccion[0], "values")[0] if seleccion else None
        self._filas = [["-" if valor is None else valor for valor in fila] for fila in filas]
        self._mostrar(seleccionado)
        self._ajustar_anchos(self._filas)

    def _mostrar(self, seleccionado=None):
        self.arbol.delete(*self.arbol.get_children())
        filas = self._filas
        if self._orden is not None:
            indice = self._columnas.index(self._orden[0])
            filas = sorted(filas, key=lambda fila: _clave_de_orden(fila[indice]), reverse=self._orden[1])
        for numero, fila in enumerate(filas):
            opciones = {"values": fila, "tags": ["alterna"] if numero % 2 else []}
            if self._estado:
                estado = fila[self._indice_estado]
                opciones.update(text=f" {estado}", image=self._punto(estado))
            item = self.arbol.insert("", "end", **opciones)
            if seleccionado is not None and str(fila[0]) == str(seleccionado):
                self.arbol.selection_set(item)
                self.arbol.see(item)
        if filas:
            self._vacio.place_forget()
        else:
            self._vacio.place(relx=0.5, rely=0.55, anchor="center")

    def ordenar_por(self, columna):
        """Ordena por la columna indicada; si ya estaba ordenada por ella, invierte el orden."""
        descendente = self._orden is not None and self._orden[0] == columna and not self._orden[1]
        self._orden = (columna, descendente)
        for nombre in self._columnas:
            texto = nombre + (self.FLECHAS[descendente] if nombre == columna else "")
            self.arbol.heading("#0" if nombre == self._estado else nombre, text=texto)
        seleccion = self.arbol.selection()
        self._mostrar(self.arbol.item(seleccion[0], "values")[0] if seleccion else None)

    def _ajustar_anchos(self, filas):
        """Ensancha cada columna visible lo necesario para que no se corte el texto, hasta un máximo."""
        medir = font.nametofont("TkDefaultFont").measure
        medir_encabezado = font.nametofont("FuenteNegrita").measure if "FuenteNegrita" in font.names() else medir
        for indice, columna in enumerate(self._columnas):
            if columna not in self._visibles and columna != self._estado:
                continue
            ancho_texto = max([medir(str(fila[indice])) for fila in filas] + [medir_encabezado(columna + " ▼")])
            if columna == self._estado:
                self.arbol.column("#0", width=max(self._anchos_minimos[columna], ancho_texto + 56))
                continue
            ancho = ancho_texto + 30
            self.arbol.column(columna, width=max(self._anchos_minimos[columna], min(ancho, self.ANCHO_MAXIMO)))

    def filas(self):
        return [self.arbol.item(item, "values") for item in self.arbol.get_children()]

    def cantidad(self):
        return len(self.arbol.get_children())

    def seleccionar_primera(self):
        hijos = self.arbol.get_children()
        if hijos:
            self.arbol.selection_set(hijos[0])

    def seleccionar_id(self, identificador):
        """Selecciona y muestra la fila cuyo identificador es el indicado."""
        for item in self.arbol.get_children():
            if str(self.arbol.item(item, "values")[0]) == str(identificador):
                self.arbol.selection_set(item)
                self.arbol.see(item)
                return

    def id_seleccionado(self):
        seleccion = self.arbol.selection()
        if not seleccion:
            return None
        return int(self.arbol.item(seleccion[0], "values")[0])

    def al_seleccionar(self, funcion):
        self.arbol.bind("<<TreeviewSelect>>", lambda evento: funcion(), add="+")

    def al_doble_clic(self, funcion):
        """Ejecuta la función al hacer doble clic (o Enter) sobre una fila."""
        def manejar(evento):
            if evento.type == tk.EventType.ButtonPress and self.arbol.identify_region(evento.x, evento.y) not in ("cell", "tree"):
                return
            if self.arbol.selection():
                funcion()
        self.arbol.bind("<Double-1>", manejar)
        self.arbol.bind("<Return>", manejar)


def id_seleccionado_o_aviso(tabla, padre, descripcion):
    """Devuelve el id de la fila elegida o avisa que hay que elegir una."""
    identificador = tabla.id_seleccionado()
    if identificador is None:
        avisar(f"Seleccione {descripcion} en la lista.", padre)
    return identificador


# --- Botones, encabezado y filtros -----------------------------------------------------------

PRIMARIO = "Primario.TButton"
PELIGRO = "Peligro.TButton"
ATENUADO = "Atenuado.TButton"


def barra_de_botones(padre, botones, estilo_marco="Panel.TFrame"):
    """Crea una fila de botones a partir de una lista de (texto, comando) o (texto, comando, estilo).

    El estilo es PRIMARIO para la acción principal de la pestaña o PELIGRO para las que
    dan de baja, cancelan o anulan; sin estilo el botón es secundario.
    """
    barra = ttk.Frame(padre, style=estilo_marco)
    barra.botones = {}
    for boton in botones:
        texto, comando = boton[0], boton[1]
        estilo = boton[2] if len(boton) > 2 else "TButton"
        widget = ttk.Button(barra, text=texto, command=comando, style=estilo)
        widget.pack(side="left", padx=(0, 8))
        widget.estilo_base = estilo
        barra.botones[texto] = widget
    return barra


def encabezado_de_pestania(padre, titulo, descripcion, acciones=()):
    """Título y descripción de la pestaña, con sus acciones principales a la derecha.

    acciones es una lista como la de barra_de_botones; se muestran de derecha a izquierda,
    así la primera queda en el extremo derecho. Devuelve el marco del encabezado.
    """
    marco = ttk.Frame(padre, style="Panel.TFrame")
    textos = ttk.Frame(marco, style="Panel.TFrame")
    textos.pack(side="left", fill="x", expand=True)
    ttk.Label(textos, text=titulo, style="PanelTitulo.TLabel").pack(anchor="w")
    ttk.Label(textos, text=descripcion, style="PanelSuave.TLabel").pack(anchor="w", pady=(2, 0))
    marco.botones = {}
    for boton in acciones:
        texto, comando = boton[0], boton[1]
        estilo = boton[2] if len(boton) > 2 else "TButton"
        widget = ttk.Button(marco, text=texto, command=comando, style=estilo)
        widget.pack(side="right", padx=(8, 0), anchor="n")
        marco.botones[texto] = widget
    return marco


def acciones_de_seleccion(barra, botones):
    """Agrega a la derecha de una barra las acciones que se aplican a la fila elegida."""
    marco = barra_de_botones(barra, botones)
    marco.pack(side="right")
    ttk.Label(barra, text="Selección:", style="PanelSuave.TLabel").pack(side="right", padx=(0, 8))
    return marco


class FiltroSegmentado(ttk.Frame):
    """Botones contiguos para elegir una opción de filtro, cada uno con su cantidad.

    Tiene la misma interfaz que una lista desplegable (get y set), así las pestañas y las
    pruebas pueden elegir una opción por su nombre.
    """

    def __init__(self, padre, opciones, al_cambiar=None, inicial=None):
        super().__init__(padre, style="Panel.TFrame")
        self._opciones = list(opciones)
        self._al_cambiar = al_cambiar
        self._valor = inicial or self._opciones[0]
        self._cantidades = {}
        self.botones = {}
        for opcion in self._opciones:
            boton = ttk.Button(self, text=opcion, command=lambda opcion=opcion: self.elegir(opcion))
            boton.pack(side="left", padx=(0, 1))
            self.botones[opcion] = boton
        self._pintar()

    def get(self):
        return self._valor

    def set(self, opcion):
        """Elige la opción sin avisar (como Combobox.set); la pestaña actualiza cuando corresponde."""
        if opcion not in self._opciones:
            raise ValueError(f"'{opcion}' no es una opción del filtro: {self._opciones}")
        self._valor = opcion
        self._pintar()

    def elegir(self, opcion):
        """Lo que hace un clic: elige la opción y avisa a la pestaña."""
        self.set(opcion)
        if self._al_cambiar:
            self._al_cambiar()

    def mostrar_cantidades(self, cantidades):
        self._cantidades = dict(cantidades)
        self._pintar()

    def _pintar(self):
        for opcion, boton in self.botones.items():
            cantidad = self._cantidades.get(opcion)
            boton.configure(text=opcion if cantidad is None else f"{opcion}  {cantidad}",
                            style="SegmentoElegido.TButton" if opcion == self._valor else "Segmento.TButton")


class CampoDeBusqueda(ttk.Frame):
    """Campo de texto con una indicación ("Buscar por…") que filtra mientras se escribe.

    La indicación es una etiqueta encima del campo, así el contenido del campo es siempre
    lo que escribió el usuario. self.entrada es el ttk.Entry.
    """

    def __init__(self, padre, indicacion, al_escribir, ancho=34):
        super().__init__(padre, style="Panel.TFrame")
        self.texto = tk.StringVar(self)
        self.entrada = ttk.Entry(self, textvariable=self.texto, width=ancho)
        self.entrada.pack(fill="x")
        self._indicacion = tk.Label(self.entrada, text=indicacion, bg=tema.SUPERFICIE, fg=tema.TEXTO_SUAVE,
                                    font="TkDefaultFont", cursor="xterm")
        self._indicacion.bind("<Button-1>", lambda evento: self.entrada.focus_set())
        self.texto.trace_add("write", lambda *args: (self._actualizar_indicacion(), al_escribir()))
        self._actualizar_indicacion()

    def _actualizar_indicacion(self):
        if self.texto.get():
            self._indicacion.place_forget()
        else:
            self._indicacion.place(x=8, rely=0.5, anchor="w")

    def get(self):
        return self.texto.get().strip()

    def limpiar(self):
        self.texto.set("")


def coincide(busqueda, *textos):
    """True si la búsqueda está contenida en alguno de los textos, sin distinguir mayúsculas ni puntos."""
    if not busqueda:
        return True
    buscado = busqueda.casefold().replace(".", "")
    return any(buscado in str(texto or "").casefold().replace(".", "") for texto in textos)


def barra_de_filtros(padre):
    """Fila con la búsqueda y los filtros a la izquierda y las acciones de la selección a la derecha."""
    return ttk.Frame(padre, style="Panel.TFrame")


def tarjeta(padre, valor, texto, detalle=None, alerta=False):
    """Recuadro con un número destacado, su descripción y, opcionalmente, un detalle."""
    marco = ttk.Frame(padre, style="Tarjeta.TFrame", padding=(14, 8))
    ttk.Label(marco, text=texto, style="TarjetaTexto.TLabel").pack(anchor="w")
    ttk.Label(marco, text=valor, style="TarjetaValorAlerta.TLabel" if alerta else "TarjetaValor.TLabel").pack(anchor="w")
    if detalle:
        ttk.Label(marco, text=detalle, style="TarjetaDetalle.TLabel").pack(anchor="w")
    return marco


def division_vertical(padre, arriba, abajo, proporcion=0.45):
    """PanedWindow con la tabla arriba y el detalle abajo, separados por un divisor que se puede arrastrar.

    proporcion es la parte de la altura que ocupa la tabla al mostrarse por primera vez.
    arriba y abajo son funciones que reciben el PanedWindow y devuelven el widget de cada parte.
    """
    division = ttk.PanedWindow(padre, orient="vertical")
    parte_de_arriba, parte_de_abajo = arriba(division), abajo(division)
    division.add(parte_de_arriba, weight=1)
    division.add(parte_de_abajo, weight=1)

    def ubicar(evento):
        if evento.height > 50 and not getattr(division, "ubicado", False):
            division.ubicado = True
            division.after_idle(lambda: division.sashpos(0, int(evento.height * proporcion)))
    division.bind("<Configure>", ubicar, add="+")
    return division, parte_de_arriba, parte_de_abajo


class PanelDeDetalle(ttk.Frame):
    """Recuadro debajo de la tabla con el registro elegido: cabecera (título, datos y acciones) y cuerpo."""

    def __init__(self, padre, titulo_vacio):
        super().__init__(padre, style="Detalle.TFrame", padding=1)
        self._titulo_vacio = titulo_vacio
        self.cabecera = ttk.Frame(self, style="DetalleCabecera.TFrame", padding=(14, 9))
        self.cabecera.pack(fill="x")
        self.titulo = ttk.Label(self.cabecera, text=titulo_vacio, style="DetalleTitulo.TLabel")
        self.titulo.pack(side="left")
        self.subtitulo = ttk.Label(self.cabecera, text="", style="DetalleSuave.TLabel")
        self.subtitulo.pack(side="left", padx=(12, 0))
        self.acciones = ttk.Frame(self.cabecera, style="DetalleCabecera.TFrame")
        self.acciones.pack(side="right")
        ttk.Separator(self, style="Panel.TSeparator").pack(fill="x")
        self.cuerpo = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        self.cuerpo.pack(fill="both", expand=True)

    def mostrar(self, titulo, subtitulo=""):
        self.titulo.configure(text=titulo)
        self.subtitulo.configure(text=subtitulo)

    def vaciar(self):
        self.mostrar(self._titulo_vacio, "")
        for hijo in self.cuerpo.winfo_children():
            hijo.destroy()


class MarcoDesplazable(ttk.Frame):
    """Marco con desplazamiento vertical: el contenido va en self.interior."""

    def __init__(self, padre, fondo=tema.SUPERFICIE, estilo="Panel.TFrame"):
        super().__init__(padre, style=estilo)
        self.lienzo = tk.Canvas(self, highlightthickness=0, borderwidth=0, background=fondo)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.lienzo.yview)
        self.interior = ttk.Frame(self.lienzo, style=estilo)
        self._ventana = self.lienzo.create_window((0, 0), window=self.interior, anchor="nw")
        self.lienzo.configure(yscrollcommand=_barra_automatica(barra))
        self.lienzo.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.interior.bind("<Configure>", lambda evento: self._ajustar())
        self.lienzo.bind("<Configure>", lambda evento: self._ajustar())
        for secuencia in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.lienzo.bind_all(secuencia, self._rueda, add="+")

    def _ajustar(self):
        alto = max(self.interior.winfo_reqheight(), self.lienzo.winfo_height())
        self.lienzo.itemconfigure(self._ventana, width=self.lienzo.winfo_width(), height=alto)
        self.lienzo.configure(scrollregion=(0, 0, self.lienzo.winfo_width(), self.interior.winfo_reqheight()))

    def _rueda(self, evento):
        """Desplaza con la rueda del mouse si el puntero está sobre el marco y no sobre una tabla."""
        try:
            debajo = self.winfo_containing(evento.x_root, evento.y_root)
        except (tk.TclError, KeyError):
            return
        if debajo is None or isinstance(debajo, ttk.Treeview) or not str(debajo).startswith(str(self)):
            return
        if self.interior.winfo_reqheight() <= self.lienzo.winfo_height():
            return
        paso = -1 if getattr(evento, "num", None) == 4 or getattr(evento, "delta", 0) > 0 else 1
        self.lienzo.yview_scroll(paso * 3, "units")

    def limpiar(self):
        for hijo in self.interior.winfo_children():
            hijo.destroy()
        self.lienzo.yview_moveto(0)


def centrar_sobre(ventana, padre):
    """Ubica una ventana secundaria centrada sobre la ventana principal."""
    ventana.update_idletasks()
    raiz = padre.winfo_toplevel()
    x = raiz.winfo_rootx() + (raiz.winfo_width() - ventana.winfo_reqwidth()) // 2
    y = raiz.winfo_rooty() + (raiz.winfo_height() - ventana.winfo_reqheight()) // 3
    ventana.geometry(f"+{max(x, 0)}+{max(y, 0)}")


# --- Formularios --------------------------------------------------------------------------


ANCHO_MINIMO_OPCION = 50


def _ancho_en_caracteres(texto):
    """Ancho que necesita un texto, en la unidad de width de ttk (el ancho del carácter "0")."""
    # La caja muestra el texto con TkTextFont y la lista desplegable con TkDefaultFont.
    return max(
        -(-fuente.measure(texto) // fuente.measure("0")) + 2
        for fuente in (font.nametofont("TkTextFont"), font.nametofont("TkDefaultFont"))
    )


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
        self.configure(background=tema.FONDO)
        self.resultado = None
        self._campos = campos
        self._controles = {}

        marco = ttk.Frame(self, padding=(20, 16, 20, 16))
        marco.pack(fill="both", expand=True)
        ttk.Label(marco, text=titulo, style="Subtitulo.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        if any(campo.obligatorio for campo in campos):
            ttk.Label(marco, text="Los datos marcados con * son obligatorios.", style="Suave.TLabel").grid(
                row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))
        ttk.Separator(marco).grid(row=2, column=0, columnspan=2, sticky="we", pady=(10, 8))
        for fila, campo in enumerate(campos, start=3):
            texto = campo.etiqueta + (" *" if campo.obligatorio else "")
            if campo.tipo == "fecha":
                texto += " (dd/mm/aaaa)"
            ttk.Label(marco, text=texto).grid(row=fila, column=0, sticky="w", padx=(0, 14), pady=5)
            control = self._crear_control(marco, campo)
            control.grid(row=fila, column=1, sticky="we", pady=5)
            # La marca de error se quita cuando el usuario corrige el dato.
            evento_cambio = "<<ComboboxSelected>>" if isinstance(control, ttk.Combobox) else "<Key>"
            control.bind(evento_cambio, lambda evento, control=control: self._quitar_error(control), add="+")
            self._controles[campo.clave] = control
        for campo in campos:
            if campo.depende_de:
                self._controles[campo.depende_de].bind(
                    "<<ComboboxSelected>>", lambda evento, campo=campo: self._actualizar_opciones(campo), add="+"
                )

        ttk.Separator(marco).grid(row=len(campos) + 3, column=0, columnspan=2, sticky="we", pady=(10, 0))
        botones = ttk.Frame(marco)
        botones.grid(row=len(campos) + 4, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(botones, text="Aceptar", command=self._aceptar, style=PRIMARIO).pack(side="right")
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="right", padx=(0, 8))
        self.bind("<Return>", lambda evento: self._aceptar())
        self.bind("<Escape>", lambda evento: self.destroy())
        if campos:
            self._controles[campos[0].clave].focus_set()
        centrar_sobre(self, padre)
        self.grab_set()

    def _crear_control(self, marco, campo):
        if campo.tipo == "opcion":
            # Un campo que depende de otro se mide con todas sus opciones posibles, así la
            # ventana no cambia de tamaño al elegir el otro campo.
            posibles = campo.opciones_segun(None) if campo.opciones_segun else campo.opciones
            ancho = max([ANCHO_MINIMO_OPCION] + [_ancho_en_caracteres(texto) for texto, _ in posibles])
            control = ttk.Combobox(marco, values=[texto for texto, _ in campo.opciones], state="readonly", width=ancho)
            for texto, valor in campo.opciones:
                if valor == campo.valor:
                    control.set(texto)
            return control
        control = ttk.Entry(marco, width=53)
        if campo.valor is not None:
            control.insert(0, formatear_fecha(campo.valor) if campo.tipo == "fecha" else str(campo.valor))
        return control

    def _marcar_error(self, campo):
        control = self._controles[campo.clave]
        control.configure(style="Error.TCombobox" if isinstance(control, ttk.Combobox) else "Error.TEntry")
        control.focus_set()

    @staticmethod
    def _quitar_error(control):
        if str(control.cget("style")).startswith("Error."):
            control.configure(style="TCombobox" if isinstance(control, ttk.Combobox) else "TEntry")

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
                    self._marcar_error(campo)
                    avisar(f"Complete el dato '{campo.etiqueta}'.", self)
                    return
                datos[campo.clave] = None
                continue
            try:
                datos[campo.clave] = self._convertir(campo, texto)
            except ValueError:
                self._marcar_error(campo)
                avisar(f"'{texto}' no es un valor válido para '{campo.etiqueta}'.", self)
                return
        self.resultado = datos
        self.destroy()


def opcionales_vacios_para_borrar(datos, campos):
    """En un formulario de modificación, un dato opcional que el usuario dejó vacío se tiene que borrar.

    pedir_datos devuelve None para los campos vacíos, y los servicios de modificación
    interpretan None como "no cambiar". Por eso acá se pasan como "" (texto vacío).
    """
    if datos is None:
        return None
    opcionales = {campo.clave for campo in campos if not campo.obligatorio and campo.tipo in ("texto", "entero")}
    return {clave: ("" if valor is None and clave in opcionales else valor) for clave, valor in datos.items()}


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
    ventana.configure(background=tema.FONDO)
    marco = ttk.Frame(ventana, padding=(18, 14))
    marco.pack(fill="both", expand=True)
    ttk.Label(marco, text=titulo, style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 10))
    tabla = Tabla(marco, columnas, alto=max(3, min(len(filas), 10)), anchos=anchos)
    tabla.pack(fill="both", expand=True)
    tabla.cargar(filas)
    ttk.Button(marco, text="Cerrar", command=ventana.destroy, style=PRIMARIO).pack(anchor="e", pady=(12, 0))
    ventana.bind("<Escape>", lambda evento: ventana.destroy())
    centrar_sobre(ventana, padre)
    return ventana
