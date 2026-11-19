"""Pestaña de remitos: lista arriba y, debajo, el recorrido del remito elegido.

El recorrido se muestra como una línea de tiempo horizontal: una columna por cada movimiento,
con su fecha, la duración desde el anterior y la observación, y al final los pasos que
todavía faltan. Las acciones del ciclo de vida (patrón State) se ofrecen según el estado.
"""
import tkinter as tk
from datetime import datetime
from tkinter import font, ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica import tema
from biblioteca.interfaz_grafica.opciones import destino_del_ejemplar, opciones_enum
from biblioteca.modelos.enumeraciones import EstadoFisico, SentidoRemito
from biblioteca.patrones.estados_remito import EstadoRemito
from biblioteca.servicios import ServicioRemitos

# Botones del ciclo de vida: (texto, método del estado que lo habilita, método de la pestaña, estilo).
ACCIONES = (
    ("Empaquetar", "empaquetar", "empaquetar", c.PRIMARIO),
    ("Despachar", "despachar", "despachar", c.PRIMARIO),
    ("Recibir", "recibir", "recibir", c.PRIMARIO),
    ("Punto de control", "registrar_punto_de_control", "punto_de_control", "TButton"),
    ("Registrar daño", "registrar_danio", "registrar_danio", c.PELIGRO),
    ("Reportar extravío", "reportar_extravio", "reportar_extravio", c.PELIGRO),
    ("Anular", "anular", "anular", c.PELIGRO),
)

# Pasos que faltan después de cada estado, con la explicación del primero.
PENDIENTES = {
    "Generado": ["Empaquetado", "Despachado", "Recibido", "Cerrado"],
    "Empaquetado": ["Despachado", "Recibido", "Cerrado"],
    "Despachado": ["Recibido", "Cerrado"],
    "EnTransito": ["Recibido", "Cerrado"],
    "Recibido": ["Cerrado"],
}


def acciones_validas(remito):
    """Textos de los botones que el estado actual del remito admite."""
    estado = remito.estado
    validas = []
    for texto, metodo, _, _ in ACCIONES:
        if getattr(type(estado), metodo) is getattr(EstadoRemito, metodo):
            continue
        if metodo == "anular" and remito.sentido == SentidoRemito.RETORNO:
            continue  # los remitos de retorno no se anulan
        validas.append(texto)
    return validas


def duracion(desde, hasta):
    minutos = int((hasta - desde).total_seconds() // 60)
    if minutos < 1:
        return ""
    dias, resto = divmod(minutos, 24 * 60)
    horas, minutos = divmod(resto, 60)
    partes = []
    if dias:
        partes.append(f"{dias} día{'s' if dias > 1 else ''}")
    if horas:
        partes.append(f"{horas} h")
    if minutos and not dias:
        partes.append(f"{minutos} min")
    return "+" + " ".join(partes)


class Recorrido(ttk.Frame):
    """Recorrido de un remito como línea de tiempo horizontal, dibujada en un Canvas.

    Cada paso es una columna: el punto sobre la línea y, debajo, el título, la fecha con la
    duración desde el paso anterior y la observación. Las columnas se reparten el ancho
    disponible; solo si son muchas aparece la barra horizontal.
    """

    ANCHO_MINIMO_COLUMNA = 150
    LINEAS_DE_OBSERVACION = 3
    MARGEN = 16
    ALTURA_LINEA = 20
    COLORES = {
        "hecho": tema.PRIMARIO, "actual": tema.ALERTA_PUNTO, "problema": "#c62828",
        "cerrado": "#1f8f44", "pendiente": "#9aa6b5",
    }

    def __init__(self, padre):
        super().__init__(padre, style="Panel.TFrame")
        self.lienzo = tk.Canvas(self, background=tema.SUPERFICIE, highlightthickness=0, borderwidth=0, height=170)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.lienzo.xview)
        vertical = ttk.Scrollbar(self, orient="vertical", command=self.lienzo.yview)
        self.lienzo.configure(xscrollcommand=c._barra_automatica(horizontal), yscrollcommand=c._barra_automatica(vertical))
        self.lienzo.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._remito = None
        self._ancho = 0
        self.lienzo.bind("<Configure>", self._al_cambiar_tamanio)
        for secuencia in ("<Shift-Button-4>", "<Shift-Button-5>", "<Shift-MouseWheel>"):
            self.lienzo.bind(secuencia, self._rueda)

    def _rueda(self, evento):
        paso = -1 if getattr(evento, "num", None) == 4 or getattr(evento, "delta", 0) > 0 else 1
        self.lienzo.xview_scroll(paso * 3, "units")

    def _al_cambiar_tamanio(self, evento):
        if abs(evento.width - self._ancho) > 4:
            self._ancho = evento.width
            self.dibujar(self._remito)

    def pasos(self, remito):
        """Lista de (hora, título, detalle, tipo, extra) en orden cronológico, con los pendientes al final."""
        pasos = []
        anterior = None
        actual = None if remito.esta_finalizado else remito.movimientos[-1] if remito.movimientos else None
        for movimiento in remito.movimientos:
            nuevo = movimiento.estado_nuevo
            titulo = {
                "Generado": f"Remito de {remito.sentido.value.lower()} generado",
                "Empaquetado": "Empaquetado",
                "Despachado": f"Despachado desde {remito.sede_origen.nombre}",
                "EnTransito": "En tránsito · punto de control",
                "Recibido": f"Recibido en {remito.sede_destino.nombre}",
                "Daniado": "Llegó dañado",
                "Extraviado": "Extraviado",
                "Anulado": "Anulado",
                "Cerrado": "Cerrado",
            }.get(nuevo, movimiento.estado_nuevo_visible)
            tipo = "hecho"
            if nuevo in ("Daniado", "Extraviado", "Anulado"):
                tipo = "problema"
            elif nuevo == "Cerrado":
                tipo = "cerrado"
            extra = None
            if movimiento is actual:
                tipo = "actual"
                despacho = remito.fecha_de("Despachado")
                if nuevo in ("Despachado", "EnTransito") and despacho:
                    horas = (datetime.now() - despacho).total_seconds() / 3600
                    extra = f"Última ubicación · {horas:.0f} h de viaje"
                else:
                    extra = "Estado actual"
            detalle = movimiento.observacion
            if nuevo == "Generado" and not detalle:
                detalle = f"Préstamo de {remito.prestamo.socio.nombre_completo}"
            pasos.append((movimiento.fecha_hora.strftime("%d/%m %H:%M"), movimiento.fecha_hora, titulo, detalle, tipo, extra,
                          duracion(anterior, movimiento.fecha_hora) if anterior else ""))
            anterior = movimiento.fecha_hora
        if actual is not None:
            for numero, nombre in enumerate(PENDIENTES.get(remito.nombre_estado, [])):
                titulo, detalle = {
                    "Empaquetado": ("Empaquetado", "Preparar el ejemplar para el envío"),
                    "Despachado": (f"Despachado desde {remito.sede_origen.nombre}", "Entregarlo al transporte"),
                    "Recibido": (f"Recibido en {remito.sede_destino.nombre}", "Registrar la recepción"),
                    "Cerrado": ("Cerrado", f"Cuando se entregue a {remito.prestamo.socio.nombre_completo}"
                                if remito.sentido == SentidoRemito.IDA else "Al recibirlo en la sede propietaria"),
                }[nombre]
                if numero == 0:
                    detalle = f"Próximo paso: {detalle[0].lower()}{detalle[1:]}"
                pasos.append(("pendiente", None, titulo, detalle, "pendiente", None, ""))
        return pasos

    def _recortar(self, texto, ancho, lineas):
        """Acorta el texto para que ocupe como mucho 'lineas' renglones del ancho dado (la vista Tabla lo muestra completo)."""
        fuente = font.nametofont("TkDefaultFont")
        maximo = max(int(ancho / max(fuente.measure("n"), 1)) * lineas, 20)
        return texto if len(texto) <= maximo else texto[: maximo - 1].rstrip() + "…"

    def dibujar(self, remito):
        self._remito = remito
        lienzo = self.lienzo
        lienzo.delete("all")
        ancho = max(self.lienzo.winfo_width(), 400)
        if remito is None:
            lienzo.create_text(ancho / 2, 60, text="Elija un remito de la lista para ver su recorrido.",
                               fill=tema.TEXTO_SUAVE, font="TkDefaultFont")
            lienzo.configure(scrollregion=(0, 0, ancho, 120))
            return
        pasos = self.pasos(remito)
        columna = max(self.ANCHO_MINIMO_COLUMNA, (ancho - 2 * self.MARGEN) / len(pasos))
        texto_ancho = columna - 18
        y_linea = 14
        centros = [self.MARGEN + columna * indice + columna / 2 for indice in range(len(pasos))]
        alto = 0
        for centro, (fecha, _, titulo, detalle, tipo, extra, demora) in zip(centros, pasos):
            pendiente = tipo == "pendiente"
            y = y_linea + 16
            color_titulo = "#a4161a" if tipo == "problema" else (tema.NEUTRO if pendiente else tema.TEXTO)
            item = lienzo.create_text(centro, y, text=titulo, anchor="n", width=texto_ancho, justify="center",
                                      font="FuenteNegrita", fill=color_titulo)
            y = lienzo.bbox(item)[3] + 2
            cuando = fecha if not demora else f"{fecha}  ·  {demora}"
            item = lienzo.create_text(centro, y, text=cuando, anchor="n", width=texto_ancho, justify="center",
                                      font="FuenteChica", fill=tema.TEXTO_SUAVE)
            y = lienzo.bbox(item)[3] + 4
            texto_detalle = detalle or ("Sin observaciones" if not pendiente else "")
            if texto_detalle:
                item = lienzo.create_text(centro, y, text=self._recortar(texto_detalle, texto_ancho, self.LINEAS_DE_OBSERVACION),
                                          anchor="n", width=texto_ancho, justify="center", font="TkDefaultFont",
                                          fill=tema.TEXTO if detalle and not pendiente else tema.TEXTO_SUAVE)
                y = lienzo.bbox(item)[3]
            if extra:
                item = lienzo.create_text(centro, y + 8, text=extra, anchor="n", justify="center",
                                          font="FuenteChica", fill=tema.ALERTA)
                x1, y1, x2, y2 = lienzo.bbox(item)
                caja = lienzo.create_rectangle(x1 - 6, y1 - 3, x2 + 6, y2 + 3, fill="#fff1cc", outline="")
                lienzo.tag_lower(caja, item)
                y = y2 + 3
            alto = max(alto, y)
        # Línea horizontal entre los puntos y los puntos encima.
        for (x1, paso1), (x2, paso2) in zip(zip(centros, pasos), list(zip(centros, pasos))[1:]):
            punteada = paso2[4] == "pendiente"
            lienzo.create_line(x1, y_linea, x2, y_linea, width=2,
                               fill=self.COLORES["pendiente"] if punteada or paso1[4] == "actual" else tema.PRIMARIO,
                               dash=(3, 4) if punteada else None)
        for centro, paso in zip(centros, pasos):
            tipo, color = paso[4], self.COLORES[paso[4]]
            if tipo == "actual":
                lienzo.create_oval(centro - 9, y_linea - 9, centro + 9, y_linea + 9, fill=tema.SUPERFICIE, outline=color, width=3)
            elif tipo == "pendiente":
                lienzo.create_oval(centro - 7, y_linea - 7, centro + 7, y_linea + 7, fill=tema.SUPERFICIE, outline=color, width=2)
            else:
                lienzo.create_oval(centro - 7, y_linea - 7, centro + 7, y_linea + 7, fill=color, outline=tema.SUPERFICIE, width=2)
        lienzo.configure(scrollregion=(0, 0, self.MARGEN * 2 + columna * len(pasos), alto + 4))
        lienzo.xview_moveto(0)
        lienzo.yview_moveto(0)


class PestaniaRemitos(ttk.Frame):
    COLUMNAS = ("Id", "Número", "Sentido", "Ejemplar", "Libro", "Origen", "Destino", "Generado", "Estado")
    COLUMNAS_TRAYECTO = ("Fecha y hora", "Estado anterior", "Estado nuevo", "Observación")
    FILTROS = ("Todos", "En curso", "Con incidencia", "Cerrados")
    VISTAS = ("Línea de tiempo", "Tabla")

    def __init__(self, padre):
        super().__init__(padre, padding=(20, 16), style="Panel.TFrame")
        self.servicio = ServicioRemitos()
        c.encabezado_de_pestania(
            self, "Remitos",
            "Se generan solos al pedir un préstamo interbibliotecario y al devolverlo. Acá se registra su viaje.",
        ).pack(fill="x")

        barra = c.barra_de_filtros(self)
        barra.pack(fill="x", pady=(14, 10))
        self.busqueda = c.CampoDeBusqueda(barra.izquierda, "Buscar por número, libro, ejemplar o socio", self.actualizar, ancho=38)
        self.busqueda.pack(side="left")
        # solo_en_curso se mantiene como variable: equivale a elegir el filtro "En curso".
        self.solo_en_curso = tk.BooleanVar(value=False)
        self.filtro = c.FiltroSegmentado(barra.izquierda, self.FILTROS, self._al_elegir_filtro)
        self.filtro.pack(side="left", padx=(12, 0))

        division, self.tabla, self.marco_trayecto = c.division_vertical(
            self,
            lambda padre: c.Tabla(padre, self.COLUMNAS, alto=4, columna_estado="Estado",
                                  anchos={"Libro": 190, "Origen": 150, "Destino": 150, "Generado": 140},
                                  mensaje_vacio="No hay remitos para mostrar."),
            lambda padre: ttk.LabelFrame(padre, text="Trayecto del remito seleccionado", padding=(14, 8),
                                         style="Detalle.TLabelframe"),
            proporcion=0.38,
        )
        division.pack(fill="both", expand=True)
        self.tabla.al_seleccionar(self.actualizar_trayecto)

        cabecera = ttk.Frame(self.marco_trayecto, style="Panel.TFrame")
        cabecera.pack(fill="x")
        self.resumen = ttk.Label(cabecera, text="", style="PanelSuave.TLabel")
        self.resumen.pack(side="left")
        self.vista = c.FiltroSegmentado(cabecera, self.VISTAS, self._mostrar_vista)
        self.vista.pack(side="right")
        # Fila de acciones: se muestra solo si el estado del remito admite alguna.
        self.fila_acciones = ttk.Frame(self.marco_trayecto, style="Panel.TFrame")
        self.botones = c.barra_de_botones(self.fila_acciones, [
            (texto, getattr(self, metodo), estilo) for texto, _, metodo, estilo in ACCIONES
        ])
        self.botones.pack(side="left")
        self.recorrido = Recorrido(self.marco_trayecto)
        self.tabla_trayecto = c.Tabla(self.marco_trayecto, self.COLUMNAS_TRAYECTO, alto=5, ocultas=(),
                                      anchos={"Fecha y hora": 150, "Observación": 420},
                                      mensaje_vacio="Elija un remito de la lista para ver su trayecto.")
        self._mostrar_vista()

    def _al_elegir_filtro(self):
        self.solo_en_curso.set(self.filtro.get() == "En curso")
        self.actualizar()

    def _mostrar_vista(self):
        """El recorrido se ve como línea de tiempo; la vista Tabla muestra los mismos movimientos con las observaciones completas."""
        linea = self.vista.get() == "Línea de tiempo"
        (self.tabla_trayecto if linea else self.recorrido).pack_forget()
        (self.recorrido if linea else self.tabla_trayecto).pack(fill="both", expand=True, pady=(8, 0))

    def _vista_visible(self):
        return self.recorrido if self.vista.get() == "Línea de tiempo" else self.tabla_trayecto

    def actualizar(self):
        if self.solo_en_curso.get() and self.filtro.get() != "En curso":
            self.filtro.set("En curso")
        elif not self.solo_en_curso.get() and self.filtro.get() == "En curso":
            self.filtro.set("Todos")
        remitos = self.servicio.listar_remitos()
        grupos = {
            "Todos": remitos,
            "En curso": [r for r in remitos if not r.esta_finalizado],
            "Con incidencia": [r for r in remitos if r.paso_por("Daniado") or r.paso_por("Extraviado")],
            "Cerrados": [r for r in remitos if r.esta_finalizado],
        }
        self.filtro.mostrar_cantidades({nombre: len(lista) for nombre, lista in grupos.items()})
        texto = self.busqueda.get()
        self.tabla.cargar([
            (r.id, r.numero, r.sentido.value, r.ejemplar.codigo_inventario, r.ejemplar.libro.titulo,
             r.sede_origen.nombre, r.sede_destino.nombre, c.formatear_fecha(r.fecha_generacion, con_hora=True), r.estado_visible)
            for r in grupos[self.filtro.get()]
            if c.coincide(texto, r.numero, r.ejemplar.libro.titulo, r.ejemplar.codigo_inventario,
                          r.prestamo.socio.nombre_completo)
        ])
        self.actualizar_trayecto()

    def actualizar_trayecto(self):
        id_remito = self.tabla.id_seleccionado()
        if id_remito is None:
            self.marco_trayecto.configure(text="Trayecto del remito seleccionado")
            self.resumen.configure(text="Elija un remito de la lista.")
            self.tabla_trayecto.cargar([])
            self.recorrido.dibujar(None)
            self._mostrar_acciones([])
            return
        remito = self.servicio.obtener_remito(id_remito)
        self.marco_trayecto.configure(
            text=f"Trayecto del remito {remito.numero}: {remito.sede_origen.nombre} → {remito.sede_destino.nombre}"
        )
        self.resumen.configure(text=f"{remito.ejemplar.libro.titulo}  ·  {remito.ejemplar.codigo_inventario}  ·  "
                                    f"{remito.sentido.value} para {remito.prestamo.socio.nombre_completo}")
        self.tabla_trayecto.cargar([
            (c.formatear_fecha(m.fecha_hora, con_hora=True), m.estado_anterior_visible, m.estado_nuevo_visible, m.observacion)
            for m in remito.movimientos
        ])
        self.recorrido.dibujar(remito)
        self._mostrar_acciones(acciones_validas(remito))

    def _mostrar_acciones(self, validas):
        """Muestra solo las acciones que el estado admite; la primera de avance queda como principal."""
        principal = next((t for t, _, _, estilo in ACCIONES if estilo == c.PRIMARIO and t in validas), None)
        for boton in self.botones.botones.values():
            boton.pack_forget()
        if validas:
            self.fila_acciones.pack(fill="x", pady=(8, 0), before=self._vista_visible())
        else:
            self.fila_acciones.pack_forget()
        for texto, _, _, estilo in ACCIONES:
            if texto not in validas:
                continue
            boton = self.botones.botones[texto]
            if estilo == c.PRIMARIO and texto != principal:
                estilo = "TButton"
            boton.configure(style=estilo)
            boton.pack(side="left", padx=(0, 8))

    def _accion(self, accion, mensaje, campos=None, titulo=None):
        """Pide los datos (si hacen falta) y aplica la acción al remito seleccionado.

        mensaje recibe el remito ya actualizado y arma el aviso con lo que cambió y el paso siguiente.
        """
        id_remito = c.id_seleccionado_o_aviso(self.tabla, self, "un remito")
        if id_remito is None:
            return
        datos = {}
        if campos:
            datos = c.pedir_datos(self, titulo, campos)
            if datos is None:
                return
        if c.ejecutar(lambda: accion(id_remito, **datos), self, mensaje):
            self.actualizar()

    def empaquetar(self):
        self._accion(self.servicio.empaquetar, lambda r: "Remito empaquetado. Siguiente paso: despacharlo.",
                     [c.Campo("observacion", "Observación")], "Empaquetar")

    def despachar(self):
        self._accion(self.servicio.despachar, mensaje_despacho,
                     [c.Campo("observacion", "Observación")], "Despachar")

    def punto_de_control(self):
        self._accion(self.servicio.registrar_punto_de_control,
                     lambda r: f"Punto de control registrado: {r.ultima_ubicacion}.\n"
                               f"Siguiente paso: otro punto de control o recibirlo en {r.sede_destino.nombre}.",
                     [c.Campo("ubicacion", "Ubicación", obligatorio=True)], "Punto de control")

    def recibir(self):
        self._accion(self.servicio.recibir, mensaje_recepcion, [
            c.Campo("estado_fisico", "Estado físico del ejemplar", tipo="opcion", obligatorio=True,
                    valor=EstadoFisico.BUENO, opciones=opciones_enum(EstadoFisico)),
            c.Campo("observacion", "Observación"),
        ], "Recibir")

    def registrar_danio(self):
        self._accion(self.servicio.registrar_danio, lambda r: f"Daño registrado: {consecuencia_del_danio(r)}",
                     [c.Campo("observacion", "Descripción del daño", obligatorio=True)], "Registrar daño")

    def reportar_extravio(self):
        self._accion(self.servicio.reportar_extravio, mensaje_extravio,
                     [c.Campo("observacion", "Observación", obligatorio=True)], "Reportar extravío")

    def anular(self):
        self._accion(self.servicio.anular,
                     lambda r: f"Remito anulado: el préstamo se canceló y el ejemplar "
                               f"{r.ejemplar.codigo_inventario} {destino_del_ejemplar(r.ejemplar)}.",
                     [c.Campo("motivo", "Motivo", obligatorio=True)], "Anular")


def mensaje_despacho(remito):
    efecto = "el ejemplar quedó en tránsito"
    if remito.sentido == SentidoRemito.IDA:
        efecto += " y el préstamo en envío"
    return (f"Remito despachado: {efecto}.\n"
            f"Siguiente paso: registrar puntos de control (opcional) o recibirlo en {remito.sede_destino.nombre}.")


def consecuencia_del_danio(remito):
    """Un remito de ida con daño cancela el préstamo y genera el retorno; el sistema lo anota en el último movimiento."""
    return f"el préstamo se canceló. {remito.movimientos[-1].observacion} para devolver el ejemplar a su sede."


def mensaje_recepcion(remito):
    destino = remito.sede_destino.nombre
    if remito.paso_por("Daniado"):
        if remito.sentido == SentidoRemito.IDA:
            return f"Remito recibido en {destino} con daño: {consecuencia_del_danio(remito)}"
        return f"Remito recibido en {destino} con daño: el ejemplar quedó en reparación y el remito se cerró."
    if remito.sentido == SentidoRemito.IDA:
        return (f"Remito recibido en {destino}: el préstamo quedó listo para retiro.\n"
                "Siguiente paso: en Préstamos, 'Entregar (interbibliotecario)'.")
    ejemplar = remito.ejemplar
    return (f"Remito recibido: el ejemplar {ejemplar.codigo_inventario} volvió a {destino} "
            f"y {destino_del_ejemplar(ejemplar)}. El remito quedó cerrado.")


def mensaje_extravio(remito):
    efecto = "el ejemplar quedó extraviado"
    if remito.sentido == SentidoRemito.IDA:
        efecto += ", el préstamo se canceló"
    return f"Extravío registrado: {efecto} y el remito se cerró."
