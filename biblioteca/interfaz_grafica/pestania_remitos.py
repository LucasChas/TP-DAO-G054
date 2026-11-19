"""Pestaña de remitos: acciones del ciclo de vida (patrón State) y trayecto del remito elegido."""
import tkinter as tk
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import destino_del_ejemplar, opciones_enum
from biblioteca.modelos.enumeraciones import EstadoFisico, SentidoRemito
from biblioteca.servicios import ServicioRemitos


class PestaniaRemitos(ttk.Frame):
    COLUMNAS = ("Id", "Número", "Sentido", "Ejemplar", "Libro", "Origen", "Destino", "Generado", "Estado")
    COLUMNAS_TRAYECTO = ("Fecha y hora", "Estado anterior", "Estado nuevo", "Observación")

    def __init__(self, padre):
        super().__init__(padre, padding=10)
        self.servicio = ServicioRemitos()
        barra = c.barra_de_botones(self, [
            ("Empaquetar", self.empaquetar),
            ("Despachar", self.despachar),
            ("Punto de control", self.punto_de_control),
            ("Recibir", self.recibir),
            ("Registrar daño", self.registrar_danio),
            ("Reportar extravío", self.reportar_extravio),
            ("Anular", self.anular),
        ])
        barra.pack(fill="x")
        self.solo_en_curso = tk.BooleanVar(value=False)
        ttk.Checkbutton(barra, text="Solo en curso", variable=self.solo_en_curso, command=self.actualizar).pack(side="left", padx=20)

        self.tabla = c.Tabla(self, self.COLUMNAS, alto=9, anchos={"Id": 50, "Libro": 190, "Origen": 150, "Destino": 150, "Generado": 140})
        self.tabla.pack(fill="both", expand=True, pady=(10, 0))
        self.tabla.al_seleccionar(self.actualizar_trayecto)

        self.marco_trayecto = ttk.LabelFrame(self, text="Trayecto del remito seleccionado", padding=8)
        self.marco_trayecto.pack(fill="both", expand=True, pady=(10, 0))
        self.tabla_trayecto = c.Tabla(self.marco_trayecto, self.COLUMNAS_TRAYECTO, alto=7,
                                      anchos={"Fecha y hora": 150, "Observación": 420})
        self.tabla_trayecto.pack(fill="both", expand=True)

    def actualizar(self):
        self.tabla.cargar([
            (r.id, r.numero, r.sentido.value, r.ejemplar.codigo_inventario, r.ejemplar.libro.titulo,
             r.sede_origen.nombre, r.sede_destino.nombre, c.formatear_fecha(r.fecha_generacion, con_hora=True), r.estado_visible)
            for r in self.servicio.listar_remitos(solo_en_curso=self.solo_en_curso.get())
        ])
        self.actualizar_trayecto()

    def actualizar_trayecto(self):
        id_remito = self.tabla.id_seleccionado()
        if id_remito is None:
            self.marco_trayecto.configure(text="Trayecto del remito seleccionado")
            self.tabla_trayecto.cargar([])
            return
        remito = self.servicio.obtener_remito(id_remito)
        self.marco_trayecto.configure(
            text=f"Trayecto del remito {remito.numero}: {remito.sede_origen.nombre} → {remito.sede_destino.nombre}"
        )
        self.tabla_trayecto.cargar([
            (c.formatear_fecha(m.fecha_hora, con_hora=True), m.estado_anterior_visible, m.estado_nuevo_visible, m.observacion)
            for m in remito.movimientos
        ])

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
