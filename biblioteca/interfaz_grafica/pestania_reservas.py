"""Pestaña de reservas."""
import tkinter as tk
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import opciones_libros, opciones_sedes, opciones_socios
from biblioteca.servicios import ServicioReservas


class PestaniaReservas(ttk.Frame):
    COLUMNAS = ("Id", "Socio", "Libro", "Sede de retiro", "Fecha", "Ejemplar apartado", "Retirar hasta", "Estado")

    def __init__(self, padre):
        super().__init__(padre, padding=12)
        self.servicio = ServicioReservas()
        barra = c.barra_de_botones(self, [
            ("Reservar", self.reservar, c.PRIMARIO),
            ("Registrar retiro", self.registrar_retiro),
            ("Cancelar reserva", self.cancelar, c.PELIGRO),
            ("Procesar reservas no retiradas", self.procesar_vencidas),
        ])
        barra.pack(fill="x")
        c.separador_vertical(barra)
        self.solo_activas = tk.BooleanVar(value=True)
        ttk.Checkbutton(barra, text="Solo activas", variable=self.solo_activas, command=self.actualizar).pack(side="left")
        self.tabla = c.Tabla(self, self.COLUMNAS, anchos={"Id": 50, "Socio": 160, "Libro": 200, "Sede de retiro": 160},
                             mensaje_vacio="No hay reservas para mostrar.")
        self.tabla.pack(fill="both", expand=True, pady=(10, 0))
        self.tabla.mostrar_cantidad(barra, "reserva", "reservas")

    def actualizar(self):
        self.tabla.cargar([
            (r.id, r.socio.nombre_completo, r.libro.titulo, r.sede.nombre, c.formatear_fecha(r.fecha_reserva),
             r.ejemplar.codigo_inventario if r.ejemplar else None, c.formatear_fecha(r.fecha_limite_retiro), r.estado.value)
            for r in self.servicio.listar_reservas(solo_activas=self.solo_activas.get())
        ])

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
