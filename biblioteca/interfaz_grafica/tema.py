"""Tema visual de la interfaz gráfica: colores, fuentes y estilos de ttk.

Todo el aspecto se define acá, así las pestañas solo eligen un estilo por nombre
("Primario.TButton", "Peligro.TButton", ...) y no repiten colores ni fuentes.

Los colores cumplen el nivel AA de WCAG 2.2: todo texto tiene un contraste de al
menos 4,5:1 con su fondo y los bordes de botones y campos, de al menos 3:1.
"""
import tkinter as tk
from tkinter import font, ttk

# --- Paleta -------------------------------------------------------------------------------

FONDO = "#f4f6f9"          # fondo de la ventana
SUPERFICIE = "#ffffff"     # paneles, tablas y campos
SUPERFICIE_SUAVE = "#f8fafc"
BORDE = "#c9d1db"          # separadores y contornos de paneles
BORDE_SUAVE = "#e3e8ee"    # líneas entre filas
BORDE_CONTROL = "#7b889a"  # contorno de botones y campos (3,2:1 sobre blanco)
TEXTO = "#1b2430"          # 15,6:1 sobre blanco
TEXTO_SUAVE = "#4b5768"    # 7,3:1 sobre blanco
TEXTO_ATENUADO = "#6b7686" # botones que no aplican a la selección (4,6:1)
PRIMARIO = "#1d4f86"       # azul institucional (8,4:1 con texto blanco)
PRIMARIO_ACTIVO = "#163d68"
PRIMARIO_CLARO = "#e3edf8"
SELECCION = "#dce9f7"
ENCABEZADO_TABLA = "#eef2f6"
CABECERA = "#15304f"       # banda superior
CABECERA_TEXTO = "#ffffff"
CABECERA_SUAVE = "#c9d6e6"
PELIGRO = "#a4161a"
PELIGRO_BORDE = "#c4524b"
PELIGRO_CLARO = "#fde8e7"
EXITO = "#146c2e"
ALERTA = "#7a4f00"
ALERTA_PUNTO = "#b7791f"
INFO = PRIMARIO
NEUTRO = "#3f4a5a"

# --- Estados ------------------------------------------------------------------------------
# Cada estado se muestra como un punto de color y su nombre, en la primera columna de la
# tabla. El texto de la fila siempre queda oscuro: el color está solo en el punto.

COLOR_DE_CATEGORIA = {
    "ok": "#1f8f44",       # en regla o terminado bien
    "info": "#1d4f86",     # en curso
    "alerta": "#d08a00",   # requiere atención
    "problema": "#c62828", # problema
    "neutro": "#8a94a6",   # cerrado o dado de baja
}

CATEGORIA_POR_ESTADO = {
    # Sedes y socios
    "Activa": "ok", "Dada de baja": "neutro", "Habilitado": "ok", "Inhabilitado": "problema",
    # Ejemplares
    "Disponible": "ok", "Reservado": "alerta", "Prestado": "info", "En tránsito": "info",
    "En reparación": "alerta", "Extraviado": "problema", "Dado de baja": "neutro",
    # Préstamos
    "Solicitado": "info", "En envío": "info", "Listo para retiro": "alerta", "Activo": "info",
    "Vencido": "problema", "Devuelto": "neutro", "Cancelado": "neutro",
    # Reservas
    "Pendiente": "alerta", "Disponible para retiro": "ok", "Cumplida": "neutro",
    "Cancelada": "neutro", "Vencida": "problema",
    # Remitos
    "Generado": "info", "Empaquetado": "info", "Despachado": "info", "Recibido": "ok",
    "Cerrado": "neutro", "Dañado": "problema", "Anulado": "neutro",
    # Pago de multas
    "Impaga": "alerta", "Pagada": "ok", "Sin multa": "neutro",
}


def color_de_estado(estado):
    return COLOR_DE_CATEGORIA[CATEGORIA_POR_ESTADO.get(str(estado), "neutro")]


def punto(raiz, color, diametro=10, lienzo=14):
    """Imagen de un punto de color, centrado en un cuadro de 'lienzo' píxeles de lado."""
    imagen = tk.PhotoImage(master=raiz, width=lienzo, height=lienzo)
    radio = diametro / 2
    centro = (lienzo - 1) / 2
    for y in range(lienzo):
        dy = y - centro
        if abs(dy) > radio:
            continue
        mitad = (radio ** 2 - dy ** 2) ** 0.5
        desde, hasta = round(centro - mitad), round(centro + mitad) + 1
        if hasta > desde:
            imagen.put(color, to=(desde, y, hasta, y + 1))
    return imagen


# --- Fuentes ------------------------------------------------------------------------------

FAMILIAS_PREFERIDAS = ("Segoe UI", "Inter", "Cantarell", "Ubuntu", "Noto Sans", "DejaVu Sans", "Helvetica")


def _familia_disponible(raiz):
    disponibles = set(font.families(raiz))
    return next((familia for familia in FAMILIAS_PREFERIDAS if familia in disponibles), None)


def _configurar_fuentes(raiz):
    familia = _familia_disponible(raiz)
    for nombre in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        fuente = font.nametofont(nombre, raiz)
        if familia:
            fuente.configure(family=familia)
        fuente.configure(size=10)
    base = font.nametofont("TkDefaultFont", raiz).actual()
    # Se guardan en la ventana: si el objeto Font se libera, Tk borra la fuente con nombre.
    raiz.fuentes_del_tema = []
    for nombre, tamanio, peso in (
        ("FuenteTitulo", 15, "bold"),
        ("FuenteMarca", 12, "bold"),
        ("FuenteSubtitulo", 11, "bold"),
        ("FuenteNegrita", 10, "bold"),
        ("FuenteChica", 9, "normal"),
        ("FuenteIndicador", 16, "bold"),
    ):
        if nombre in font.names(raiz):
            fuente = font.nametofont(nombre, raiz)
            fuente.configure(family=base["family"], size=tamanio, weight=peso)
        else:
            fuente = font.Font(raiz, name=nombre, family=base["family"], size=tamanio, weight=peso)
        raiz.fuentes_del_tema.append(fuente)


# --- Estilos ttk --------------------------------------------------------------------------


def _boton(estilo, nombre, fondo, texto, borde, fondo_activo, borde_activo=None, fuente="TkDefaultFont"):
    estilo.configure(nombre, background=fondo, foreground=texto, bordercolor=borde, lightcolor=fondo,
                     darkcolor=fondo, focuscolor=borde_activo or borde, padding=(14, 6), relief="solid",
                     borderwidth=1, font=fuente, anchor="center")
    estilo.map(nombre,
               background=[("pressed", fondo_activo), ("active", fondo_activo)],
               lightcolor=[("pressed", fondo_activo), ("active", fondo_activo)],
               darkcolor=[("pressed", fondo_activo), ("active", fondo_activo)],
               bordercolor=[("focus", borde_activo or borde), ("active", borde_activo or borde)])


def aplicar(raiz):
    """Configura fuentes y estilos de ttk sobre la ventana principal."""
    _configurar_fuentes(raiz)
    estilo = ttk.Style(raiz)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")
    raiz.configure(background=FONDO)
    raiz.option_add("*TCombobox*Listbox.background", SUPERFICIE)
    raiz.option_add("*TCombobox*Listbox.foreground", TEXTO)
    raiz.option_add("*TCombobox*Listbox.selectBackground", SELECCION)
    raiz.option_add("*TCombobox*Listbox.selectForeground", TEXTO)
    raiz.option_add("*Menu.background", SUPERFICIE)
    raiz.option_add("*Menu.foreground", TEXTO)
    raiz.option_add("*Menu.activeBackground", PRIMARIO_CLARO)
    raiz.option_add("*Menu.activeForeground", TEXTO)

    estilo.configure(".", background=FONDO, foreground=TEXTO, bordercolor=BORDE,
                     lightcolor=FONDO, darkcolor=FONDO, focuscolor=PRIMARIO, troughcolor=FONDO,
                     selectbackground=SELECCION, selectforeground=TEXTO, font="TkDefaultFont")
    estilo.configure("TFrame", background=FONDO)
    estilo.configure("TLabel", background=FONDO, foreground=TEXTO)
    estilo.configure("Suave.TLabel", foreground=TEXTO_SUAVE)
    estilo.configure("Titulo.TLabel", font="FuenteTitulo", foreground=TEXTO)
    estilo.configure("Subtitulo.TLabel", font="FuenteSubtitulo", foreground=TEXTO)
    estilo.configure("Negrita.TLabel", font="FuenteNegrita")
    estilo.configure("Vacio.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE)

    # Panel blanco de cada pestaña y sus textos.
    estilo.configure("Panel.TFrame", background=SUPERFICIE)
    estilo.configure("Panel.TLabel", background=SUPERFICIE, foreground=TEXTO)
    estilo.configure("PanelSuave.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE)
    estilo.configure("PanelTitulo.TLabel", background=SUPERFICIE, foreground=TEXTO, font="FuenteTitulo")
    estilo.configure("PanelSubtitulo.TLabel", background=SUPERFICIE, foreground=TEXTO, font="FuenteSubtitulo")
    estilo.configure("PanelNegrita.TLabel", background=SUPERFICIE, foreground=TEXTO, font="FuenteNegrita")
    estilo.configure("PanelChica.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE, font="FuenteChica")
    estilo.configure("Panel.TSeparator", background=BORDE)
    estilo.configure("Panel.TCheckbutton", background=SUPERFICIE)

    # Detalle del registro elegido (debajo de la tabla).
    estilo.configure("Detalle.TFrame", background=SUPERFICIE, bordercolor=BORDE, relief="solid", borderwidth=1)
    estilo.configure("DetalleCabecera.TFrame", background=SUPERFICIE_SUAVE)
    estilo.configure("DetalleCabecera.TLabel", background=SUPERFICIE_SUAVE, foreground=TEXTO)
    estilo.configure("DetalleTitulo.TLabel", background=SUPERFICIE_SUAVE, foreground=TEXTO, font="FuenteSubtitulo")
    estilo.configure("DetalleSuave.TLabel", background=SUPERFICIE_SUAVE, foreground=TEXTO_SUAVE)
    estilo.configure("Detalle.TLabelframe", background=SUPERFICIE, bordercolor=BORDE, relief="solid", borderwidth=1)
    estilo.configure("Detalle.TLabelframe.Label", background=SUPERFICIE, foreground=TEXTO, font="FuenteSubtitulo")

    # Banda superior con el nombre del sistema y los indicadores.
    estilo.configure("Cabecera.TFrame", background=CABECERA)
    estilo.configure("Marca.TLabel", background=CABECERA, foreground=CABECERA_TEXTO, font="FuenteMarca")
    estilo.configure("CabeceraSuave.TLabel", background=CABECERA, foreground=CABECERA_SUAVE, font="FuenteChica")
    estilo.configure("Indicador.TButton", background=CABECERA, foreground=CABECERA_TEXTO, bordercolor="#4d6a8c",
                     lightcolor=CABECERA, darkcolor=CABECERA, focuscolor=CABECERA_TEXTO, padding=(12, 4),
                     relief="solid", borderwidth=1)
    estilo.map("Indicador.TButton", background=[("active", "#22426a")], lightcolor=[("active", "#22426a")],
               darkcolor=[("active", "#22426a")])
    estilo.configure("IndicadorAlerta.TButton", background=CABECERA, foreground="#ffd2cc", bordercolor="#c76b62",
                     lightcolor=CABECERA, darkcolor=CABECERA, focuscolor=CABECERA_TEXTO, padding=(12, 4),
                     relief="solid", borderwidth=1, font="FuenteNegrita")
    estilo.map("IndicadorAlerta.TButton", background=[("active", "#22426a")], lightcolor=[("active", "#22426a")],
               darkcolor=[("active", "#22426a")])

    # Barra de estado inferior.
    estilo.configure("Estado.TFrame", background=FONDO)
    estilo.configure("Estado.TLabel", background=FONDO, foreground=TEXTO_SUAVE, font="FuenteChica")

    # Tarjetas (totales de los reportes y datos del socio).
    estilo.configure("Tarjeta.TFrame", background=SUPERFICIE, bordercolor=BORDE_SUAVE, relief="solid", borderwidth=1)
    estilo.configure("TarjetaValor.TLabel", background=SUPERFICIE, foreground=PRIMARIO, font="FuenteIndicador")
    estilo.configure("TarjetaValorAlerta.TLabel", background=SUPERFICIE, foreground=PELIGRO, font="FuenteIndicador")
    estilo.configure("TarjetaTexto.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE, font="FuenteChica")
    estilo.configure("TarjetaDetalle.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE, font="FuenteChica")

    # Grupos con título.
    estilo.configure("TLabelframe", background=SUPERFICIE, bordercolor=BORDE, lightcolor=SUPERFICIE,
                     darkcolor=SUPERFICIE, relief="solid", borderwidth=1)
    estilo.configure("TLabelframe.Label", background=SUPERFICIE, foreground=TEXTO, font="FuenteNegrita")

    # Botones: secundario (por defecto), primario, de peligro y atenuado.
    _boton(estilo, "TButton", SUPERFICIE, TEXTO, BORDE_CONTROL, PRIMARIO_CLARO, PRIMARIO)
    _boton(estilo, "Primario.TButton", PRIMARIO, "#ffffff", PRIMARIO, PRIMARIO_ACTIVO, PRIMARIO_ACTIVO, "FuenteNegrita")
    _boton(estilo, "Peligro.TButton", SUPERFICIE, PELIGRO, PELIGRO_BORDE, PELIGRO_CLARO, PELIGRO)
    _boton(estilo, "Atenuado.TButton", SUPERFICIE, TEXTO_ATENUADO, BORDE, SUPERFICIE_SUAVE, BORDE_CONTROL)
    estilo.configure("Chico.TButton", padding=(10, 3))
    # Filtros segmentados: un botón por opción, el elegido relleno.
    _boton(estilo, "Segmento.TButton", SUPERFICIE, TEXTO, BORDE_CONTROL, PRIMARIO_CLARO, PRIMARIO)
    _boton(estilo, "SegmentoElegido.TButton", PRIMARIO, "#ffffff", PRIMARIO, PRIMARIO_ACTIVO, PRIMARIO_ACTIVO,
           "FuenteNegrita")
    for nombre in ("Segmento.TButton", "SegmentoElegido.TButton"):
        estilo.configure(nombre, padding=(12, 5), width=0)
    # clam fuerza un ancho mínimo de 11 caracteres: se reduce para que los botones se ajusten a su texto.
    for nombre in ("TButton", "Primario.TButton", "Peligro.TButton", "Atenuado.TButton"):
        estilo.configure(nombre, width=-8)

    # Campos de entrada.
    for nombre in ("TEntry", "TCombobox"):
        estilo.configure(nombre, fieldbackground=SUPERFICIE, background=SUPERFICIE, foreground=TEXTO,
                         bordercolor=BORDE_CONTROL, lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, padding=5,
                         arrowcolor=TEXTO_SUAVE, insertcolor=TEXTO)
        estilo.map(nombre, bordercolor=[("focus", PRIMARIO)], lightcolor=[("focus", PRIMARIO)])
    estilo.map("TCombobox", fieldbackground=[("readonly", SUPERFICIE)],
               selectbackground=[("readonly", SUPERFICIE)], selectforeground=[("readonly", TEXTO)])
    for nombre in ("Error.TEntry", "Error.TCombobox"):
        estilo.configure(nombre, bordercolor=PELIGRO, lightcolor=PELIGRO, fieldbackground=PELIGRO_CLARO)
        estilo.map(nombre, bordercolor=[("focus", PELIGRO)], lightcolor=[("focus", PELIGRO)],
                   fieldbackground=[("readonly", PELIGRO_CLARO)])
    estilo.configure("TCheckbutton", background=FONDO, indicatorbackground=SUPERFICIE)
    estilo.map("TCheckbutton", background=[("active", FONDO)], indicatorbackground=[("selected", PRIMARIO)],
               indicatorforeground=[("selected", "#ffffff")])

    # Pestañas: la elegida en blanco y con texto azul.
    estilo.configure("TNotebook", background=FONDO, bordercolor=BORDE, tabmargins=(12, 8, 12, 0))
    estilo.configure("TNotebook.Tab", background=FONDO, foreground=NEUTRO, bordercolor=FONDO,
                     lightcolor=FONDO, padding=(16, 8))
    estilo.map("TNotebook.Tab",
               background=[("selected", SUPERFICIE), ("active", BORDE_SUAVE)],
               foreground=[("selected", PRIMARIO), ("active", TEXTO)],
               bordercolor=[("selected", BORDE)], lightcolor=[("selected", SUPERFICIE)])

    # Tablas.
    alto_fila = font.nametofont("TkDefaultFont", raiz).metrics("linespace") + 14
    estilo.configure("Treeview", background=SUPERFICIE, fieldbackground=SUPERFICIE, foreground=TEXTO,
                     bordercolor=BORDE, lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, rowheight=alto_fila, borderwidth=1)
    estilo.map("Treeview", background=[("selected", SELECCION)], foreground=[("selected", TEXTO)])
    estilo.configure("Treeview.Heading", background=ENCABEZADO_TABLA, foreground=TEXTO, font="FuenteNegrita",
                     bordercolor=BORDE, lightcolor=ENCABEZADO_TABLA, darkcolor=ENCABEZADO_TABLA, relief="flat",
                     padding=(8, 6))
    estilo.map("Treeview.Heading", background=[("active", PRIMARIO_CLARO)])
    for orientacion in ("Vertical", "Horizontal"):
        estilo.configure(f"{orientacion}.TScrollbar", background="#d5dbe3", troughcolor=SUPERFICIE,
                         bordercolor=SUPERFICIE, arrowcolor=TEXTO_SUAVE, lightcolor="#d5dbe3", darkcolor="#d5dbe3",
                         gripcount=0)
        estilo.map(f"{orientacion}.TScrollbar", background=[("active", "#b6c0cc")])
    estilo.configure("TSeparator", background=BORDE)
    estilo.configure("TPanedwindow", background=SUPERFICIE)
    estilo.configure("Sash", sashthickness=10, gripcount=0, background=SUPERFICIE)
    return estilo
