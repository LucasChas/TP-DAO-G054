"""Pestaña de reservas, con el lugar de cada una en la cola y su situación."""
import tkinter as tk
from datetime import date
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import opciones_libros, opciones_sedes, opciones_socios
from biblioteca.modelos.enumeraciones import EstadoReserva
from biblioteca.servicios import ServicioReservas


class PestaniaReservas(ttk.Frame):
    COLUMNAS = ("Id", "Socio", "Libro", "Sede de retiro", "Fecha", "Ejemplar apartado", "Retirar hasta", "Estado",
                "En la cola", "Situación")
    FILTROS = ("Activas", "Para retirar", "Todas")

    def __init__(self, padre):
        super().__init__(padre, padding=(20, 16), style="Panel.TFrame")
        self.servicio = ServicioReservas()
        c.encabezado_de_pestania(
            self, "Reservas", "Se asignan por orden de llegada cuando se libera un ejemplar en la sede de retiro.", [
                ("Reservar", self.reservar, c.PRIMARIO),
                ("Procesar reservas no retiradas", self.procesar_vencidas),
            ]).pack(fill="x")

        barra = c.barra_de_filtros(self)
        barra.pack(fill="x", pady=(14, 10))
        self.busqueda = c.CampoDeBusqueda(barra.izquierda, "Buscar por socio o libro", self.actualizar, ancho=30)
        self.busqueda.pack(side="left")
        # solo_activas se mantiene como variable: el filtro "Todas" la apaga y los otros dos la encienden.
        self.solo_activas = tk.BooleanVar(value=True)
        self.filtro = c.FiltroSegmentado(barra.izquierda, self.FILTROS, self._al_elegir_filtro)
        self.filtro.pack(side="left", padx=(12, 0))
        self.acciones = c.acciones_de_seleccion(barra, [
            ("Registrar retiro", self.registrar_retiro),
            ("Cancelar reserva", self.cancelar, c.PELIGRO),
        ])
        self.tabla = c.Tabla(self, self.COLUMNAS, columna_estado="Estado", ocultas=("Id", "Ejemplar apartado"),
                             anchos={"Socio": 130, "Libro": 150, "Sede de retiro": 120, "Situación": 260},
                             mensaje_vacio="No hay reservas para mostrar.")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.al_seleccionar(self._actualizar_acciones)

    def _al_elegir_filtro(self):
        self.solo_activas.set(self.filtro.get() != "Todas")
        self.actualizar()

    def actualizar(self):
        if not self.solo_activas.get() and self.filtro.get() != "Todas":
            self.filtro.set("Todas")
        elif self.solo_activas.get() and self.filtro.get() == "Todas":
            self.filtro.set("Activas")
        todas = self.servicio.listar_reservas()
        activas = [r for r in todas if r.esta_activa]
        para_retirar = [r for r in activas if r.estado == EstadoReserva.DISPONIBLE]
        self.filtro.mostrar_cantidades({"Activas": len(activas), "Para retirar": len(para_retirar), "Todas": len(todas)})
        elegidas = {"Activas": activas, "Para retirar": para_retirar, "Todas": todas}[self.filtro.get()]
        cola = self._lugares_en_la_cola(todas)
        texto = self.busqueda.get()
        self.tabla.cargar([
            (r.id, r.socio.nombre_completo, r.libro.titulo, r.sede.nombre, c.formatear_fecha(r.fecha_reserva),
             r.ejemplar.codigo_inventario if r.ejemplar else None, c.formatear_fecha(r.fecha_limite_retiro),
             r.estado.value, cola.get(r.id), self._situacion(r))
            for r in elegidas if c.coincide(texto, r.socio.nombre_completo, r.libro.titulo)
        ])
        self._actualizar_acciones()

    @staticmethod
    def _lugares_en_la_cola(reservas):
        """Orden de llegada de cada reserva pendiente entre las del mismo libro y sede ("1.º de 2")."""
        colas = {}
        for reserva in sorted(reservas, key=lambda r: (r.fecha_reserva, r.id)):
            if reserva.estado == EstadoReserva.PENDIENTE:
                colas.setdefault((reserva.libro_id, reserva.sede_id), []).append(reserva.id)
        lugares = {}
        for ids in colas.values():
            for posicion, id_reserva in enumerate(ids, start=1):
                lugares[id_reserva] = f"{posicion}.º de {len(ids)}"
        return lugares

    @staticmethod
    def _situacion(reserva):
        if reserva.estado == EstadoReserva.PENDIENTE:
            return f"Espera que se libere un ejemplar en {reserva.sede.nombre}"
        if reserva.estado == EstadoReserva.DISPONIBLE:
            dias = (reserva.fecha_limite_retiro - date.today()).days
            if dias < 0:
                return f"Venció el plazo para retirar {reserva.ejemplar.codigo_inventario}"
            plazo = "hoy" if dias == 0 else f"en {dias} día{'s' if dias != 1 else ''}"
            return f"Retirar {reserva.ejemplar.codigo_inventario} {plazo} (hasta el {c.formatear_fecha(reserva.fecha_limite_retiro)})"
        return "-"

    def _actualizar_acciones(self):
        """«Registrar retiro» se destaca cuando la reserva elegida ya tiene un ejemplar apartado."""
        fila = next((f for f in self.tabla.filas() if str(f[0]) == str(self.tabla.id_seleccionado())), None)
        lista = fila is not None and fila[7] == EstadoReserva.DISPONIBLE.value
        self.acciones.botones["Registrar retiro"].configure(style=c.PRIMARIO if lista else "TButton")

    def reservar(self):
        datos = c.pedir_datos(self, "Reservar libro", [
            c.Campo("id_socio", "Socio", tipo="opcion", obligatorio=True, opciones=opciones_socios()),
            c.Campo("id_libro", "Libro", tipo="opcion", obligatorio=True, opciones=opciones_libros()),
            c.Campo("id_sede", "Sede de retiro", tipo="opcion", obligatorio=True, opciones=opciones_sedes()),
        ])
        if datos and c.ejecutar(
            lambda: self.servicio.reservar(**datos), self,
            "Reserva registrada. Cuando se libere un ejemplar en esa sede, se aparta para la reserva más antigua: "
            "pasa a 'Disponible para retiro' y el socio tiene 3 días para retirarlo.",
        ):
            self.actualizar()

    def registrar_retiro(self):
        """El socio de la reserva elegida se lleva el ejemplar apartado: se registra el préstamo local."""
        id_reserva = c.id_seleccionado_o_aviso(self.tabla, self, "una reserva")
        if id_reserva is not None and c.ejecutar(
            lambda: self.servicio.registrar_retiro(id_reserva), self,
            lambda p: f"Retiro registrado: se prestó {p.ejemplar.codigo_inventario} a {p.socio.nombre_completo}. "
                      f"Vence el {c.formatear_fecha(p.fecha_vencimiento)}.",
        ):
            self.actualizar()

    def cancelar(self):
        id_reserva = c.id_seleccionado_o_aviso(self.tabla, self, "una reserva")
        if id_reserva is not None and c.ejecutar(lambda: self.servicio.cancelar_reserva(id_reserva), self, "Reserva cancelada."):
            self.actualizar()

    def procesar_vencidas(self):
        vencidas = c.ejecutar(lambda: self.servicio.procesar_reservas_vencidas(), self)
        if vencidas is not None:
            c.informar(mensaje_vencidas(vencidas), self)
            self.actualizar()


def mensaje_vencidas(vencidas):
    """Detalle de cada reserva vencida y a quién pasó su ejemplar."""
    if not vencidas:
        return "No hay reservas con el plazo de retiro vencido."
    lineas = [f"Reservas vencidas por no retirar: {len(vencidas)}."]
    for reserva in vencidas:
        codigo = reserva.ejemplar_liberado.codigo_inventario
        if reserva.reasignada_a is not None:
            destino = f"pasó a la reserva de {reserva.reasignada_a.socio.nombre_completo}"
        else:
            destino = "volvió a estar disponible"
        lineas.append(f"- {reserva.socio.nombre_completo} ({reserva.libro.titulo}): el ejemplar {codigo} {destino}.")
    return "\n".join(lineas)
