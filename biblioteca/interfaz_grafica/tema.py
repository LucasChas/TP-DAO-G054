"""Tema visual de la interfaz gráfica: colores, fuentes y estilos de ttk.

Todo el aspecto se define acá, así las pestañas solo eligen un estilo por nombre
("Primario.TButton", "Peligro.TButton", ...) y no repiten colores ni fuentes.
"""
from tkinter import font, ttk

# --- Paleta -------------------------------------------------------------------------------

FONDO = "#f3f5f8"          # fondo de la ventana
SUPERFICIE = "#ffffff"     # tablas, campos y tarjetas
BORDE = "#d5dbe3"
BORDE_SUAVE = "#e6eaf0"
TEXTO = "#1f2937"
TEXTO_SUAVE = "#64748b"
PRIMARIO = "#1d4f86"       # azul institucional
PRIMARIO_ACTIVO = "#163d68"
PRIMARIO_CLARO = "#e3edf8"
SELECCION = "#cfe0f3"
CABECERA = "#15304f"       # banda superior
CABECERA_TEXTO = "#ffffff"
CABECERA_SUAVE = "#a9bdd6"
PELIGRO = "#b42318"
PELIGRO_CLARO = "#fdecea"
FILA_ALTERNA = "#f7f9fc"

# Color del texto de una fila según el valor de su columna "Estado". Solo se destacan los
# problemas (rojo) y los registros cerrados o dados de baja (gris), para no recargar la tabla.
ERROR = PELIGRO
APAGADO = "#8a94a6"

COLOR_POR_ESTADO = {
    # Rojo: problemas que requieren atención.
    "Inhabilitado": ERROR, "Extraviado": ERROR, "Dañado": ERROR, "Vencida": ERROR,
    # Gris: registros cerrados o dados de baja.
    "Dada de baja": APAGADO, "Dado de baja": APAGADO, "Cancelado": APAGADO, "Cancelada": APAGADO,
    "Anulado": APAGADO, "Devuelto": APAGADO,
}

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
        ("FuenteTitulo", 16, "bold"),
        ("FuenteSubtitulo", 12, "bold"),
        ("FuenteNegrita", 10, "bold"),
        ("FuenteChica", 9, "normal"),
        ("FuenteIndicador", 18, "bold"),
    ):
        if nombre in font.names(raiz):
            fuente = font.nametofont(nombre, raiz)
            fuente.configure(family=base["family"], size=tamanio, weight=peso)
        else:
            fuente = font.Font(raiz, name=nombre, family=base["family"], size=tamanio, weight=peso)
        raiz.fuentes_del_tema.append(fuente)


# --- Estilos ttk --------------------------------------------------------------------------


def aplicar(raiz):
    """Configura fuentes y estilos de ttk sobre la ventana principal."""
    _configurar_fuentes(raiz)
    estilo = ttk.Style(raiz)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")
    raiz.configure(background=FONDO)
    raiz.option_add("*TCombobox*Listbox.background", SUPERFICIE)
    raiz.option_add("*TCombobox*Listbox.selectBackground", SELECCION)
    raiz.option_add("*TCombobox*Listbox.selectForeground", TEXTO)
    raiz.option_add("*Menu.background", SUPERFICIE)
    raiz.option_add("*Menu.activeBackground", PRIMARIO_CLARO)
    raiz.option_add("*Menu.activeForeground", TEXTO)

    estilo.configure(".", background=FONDO, foreground=TEXTO, bordercolor=BORDE,
                     lightcolor=FONDO, darkcolor=FONDO, focuscolor=PRIMARIO, troughcolor=BORDE_SUAVE,
                     selectbackground=SELECCION, selectforeground=TEXTO, font="TkDefaultFont")
    estilo.configure("TFrame", background=FONDO)
    estilo.configure("TLabel", background=FONDO, foreground=TEXTO)
    estilo.configure("Suave.TLabel", foreground=TEXTO_SUAVE)
    estilo.configure("Titulo.TLabel", font="FuenteTitulo", foreground=TEXTO)
    estilo.configure("Subtitulo.TLabel", font="FuenteSubtitulo", foreground=PRIMARIO)
    estilo.configure("Negrita.TLabel", font="FuenteNegrita")
    estilo.configure("Vacio.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE)

    # Banda superior con el nombre del sistema y los indicadores.
    estilo.configure("Cabecera.TFrame", background=CABECERA)
    estilo.configure("Cabecera.TLabel", background=CABECERA, foreground=CABECERA_TEXTO, font="FuenteTitulo")
    estilo.configure("CabeceraSuave.TLabel", background=CABECERA, foreground=CABECERA_SUAVE, font="FuenteChica")
    estilo.configure("Indicador.TFrame", background=CABECERA)
    estilo.configure("IndicadorValor.TLabel", background=CABECERA, foreground=CABECERA_TEXTO, font="FuenteIndicador")
    estilo.configure("IndicadorValorAlerta.TLabel", background=CABECERA, foreground="#ffb4a8", font="FuenteIndicador")
    estilo.configure("IndicadorTexto.TLabel", background=CABECERA, foreground=CABECERA_SUAVE, font="FuenteChica")

    # Barra de estado inferior.
    estilo.configure("Estado.TFrame", background=SUPERFICIE)
    estilo.configure("Estado.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE, font="FuenteChica")

    # Tarjetas (resúmenes de los reportes).
    estilo.configure("Tarjeta.TFrame", background=SUPERFICIE, bordercolor=BORDE, relief="solid", borderwidth=1)
    estilo.configure("TarjetaValor.TLabel", background=SUPERFICIE, foreground=PRIMARIO, font="FuenteIndicador")
    estilo.configure("TarjetaTexto.TLabel", background=SUPERFICIE, foreground=TEXTO_SUAVE, font="FuenteChica")

    # Grupos con título.
    estilo.configure("TLabelframe", background=FONDO, bordercolor=BORDE, lightcolor=FONDO, darkcolor=FONDO,
                     relief="solid", borderwidth=1)
    estilo.configure("TLabelframe.Label", background=FONDO, foreground=PRIMARIO, font="FuenteNegrita")

    # Botones: secundario (por defecto), primario y de peligro.
    estilo.configure("TButton", background=SUPERFICIE, foreground=TEXTO, bordercolor=BORDE,
                     lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, padding=(12, 5), relief="flat")
    estilo.map("TButton",
               background=[("pressed", BORDE_SUAVE), ("active", PRIMARIO_CLARO)],
               bordercolor=[("focus", PRIMARIO), ("active", PRIMARIO)],
               lightcolor=[("active", PRIMARIO_CLARO)], darkcolor=[("active", PRIMARIO_CLARO)])
    estilo.configure("Primario.TButton", background=PRIMARIO, foreground="#ffffff", bordercolor=PRIMARIO,
                     lightcolor=PRIMARIO, darkcolor=PRIMARIO, font="FuenteNegrita")
    estilo.map("Primario.TButton",
               background=[("pressed", PRIMARIO_ACTIVO), ("active", PRIMARIO_ACTIVO)],
               lightcolor=[("active", PRIMARIO_ACTIVO)], darkcolor=[("active", PRIMARIO_ACTIVO)],
               bordercolor=[("focus", PRIMARIO_ACTIVO), ("active", PRIMARIO_ACTIVO)])
    estilo.configure("Peligro.TButton", foreground=PELIGRO)
    estilo.map("Peligro.TButton",
               background=[("pressed", "#f9d7d3"), ("active", PELIGRO_CLARO)],
               bordercolor=[("focus", PELIGRO), ("active", PELIGRO)],
               lightcolor=[("active", PELIGRO_CLARO)], darkcolor=[("active", PELIGRO_CLARO)])
    # Botón de la lista de reportes: el elegido queda resaltado.
    estilo.configure("Menu.TButton", anchor="w", padding=(12, 7))
    estilo.configure("MenuElegido.TButton", anchor="w", padding=(12, 7), background=PRIMARIO_CLARO,
                     foreground=PRIMARIO, bordercolor=PRIMARIO, lightcolor=PRIMARIO_CLARO, darkcolor=PRIMARIO_CLARO,
                     font="FuenteNegrita")

    # Campos de entrada.
    for nombre in ("TEntry", "TCombobox"):
        estilo.configure(nombre, fieldbackground=SUPERFICIE, background=SUPERFICIE, bordercolor=BORDE,
                         lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, padding=4, arrowcolor=TEXTO_SUAVE)
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

    # Pestañas.
    estilo.configure("TNotebook", background=FONDO, bordercolor=BORDE, tabmargins=(8, 6, 8, 0))
    estilo.configure("TNotebook.Tab", background=FONDO, foreground=TEXTO_SUAVE, bordercolor=FONDO,
                     lightcolor=FONDO, padding=(14, 7))
    estilo.map("TNotebook.Tab",
               background=[("selected", SUPERFICIE), ("active", BORDE_SUAVE)],
               foreground=[("selected", PRIMARIO), ("active", TEXTO)],
               bordercolor=[("selected", BORDE)], lightcolor=[("selected", SUPERFICIE)])

    # Tablas.
    alto_fila = font.nametofont("TkDefaultFont", raiz).metrics("linespace") + 10
    estilo.configure("Treeview", background=SUPERFICIE, fieldbackground=SUPERFICIE, foreground=TEXTO,
                     bordercolor=BORDE, lightcolor=SUPERFICIE, darkcolor=SUPERFICIE, rowheight=alto_fila, borderwidth=1)
    estilo.map("Treeview", background=[("selected", SELECCION)], foreground=[("selected", TEXTO)])
    estilo.configure("Treeview.Heading", background="#eaeff5", foreground=TEXTO, font="FuenteNegrita",
                     bordercolor=BORDE, lightcolor="#eaeff5", darkcolor="#eaeff5", relief="flat", padding=(6, 5))
    estilo.map("Treeview.Heading", background=[("active", PRIMARIO_CLARO)])
    estilo.configure("Vertical.TScrollbar", background=BORDE_SUAVE, troughcolor=FONDO, bordercolor=FONDO,
                     arrowcolor=TEXTO_SUAVE, lightcolor=BORDE_SUAVE, darkcolor=BORDE_SUAVE)
    estilo.configure("Horizontal.TScrollbar", background=BORDE_SUAVE, troughcolor=FONDO, bordercolor=FONDO,
                     arrowcolor=TEXTO_SUAVE, lightcolor=BORDE_SUAVE, darkcolor=BORDE_SUAVE)
    estilo.configure("TSeparator", background=BORDE)
    return estilo
