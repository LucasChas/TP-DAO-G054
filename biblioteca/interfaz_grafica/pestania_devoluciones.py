"""Pestaña de devoluciones y multas, con la política de multas vigente (patrón Strategy)."""
import tkinter as tk
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import opciones_enum
from biblioteca.modelos.enumeraciones import EstadoFisico, EstadoPrestamo
from biblioteca.patrones.estrategias_multa import ESTRATEGIAS_DISPONIBLES
from biblioteca.servicios import ServicioPrestamos


class PestaniaDevoluciones(ttk.Frame):
    COLUMNAS = ("Id", "Préstamo", "Socio", "Libro", "Fecha", "Estado físico", "Días de atraso", "Multa", "Pagada")

    def __init__(self, padre, servicio):
        """servicio es el ServicioDevoluciones compartido con la pestaña de reportes,
        así ambos usan la misma política de multas."""
        super().__init__(padre, padding=10)
        self.servicio = servicio
        barra = c.barra_de_botones(self, [
            ("Registrar devolución", self.registrar_devolucion),
            ("Registrar pago de multa", self.registrar_pago),
        ])
        barra.pack(fill="x")
        self.solo_impagas = tk.BooleanVar(value=False)
        ttk.Checkbutton(barra, text="Solo multas impagas", variable=self.solo_impagas, command=self.actualizar).pack(side="left", padx=20)

        politica = ttk.Frame(self)
        politica.pack(fill="x", pady=(10, 0))
        ttk.Label(politica, text="Política de multas vigente:").pack(side="left")
        self.estrategias = {clase().descripcion: clase for clase in ESTRATEGIAS_DISPONIBLES}
        self.selector_politica = ttk.Combobox(politica, values=list(self.estrategias), state="readonly", width=80)
        self.selector_politica.set(self.servicio.calculadora.estrategia.descripcion)
        self.selector_politica.pack(side="left", padx=6)
        self.selector_politica.bind("<<ComboboxSelected>>", lambda evento: self.cambiar_politica())

        self.tabla = c.Tabla(self, self.COLUMNAS, anchos={"Id": 50, "Préstamo": 80, "Socio": 160, "Libro": 200})
        self.tabla.pack(fill="both", expand=True, pady=(10, 0))

    def actualizar(self):
        if self.solo_impagas.get():
            devoluciones = self.servicio.listar_multas_impagas()
        else:
            devoluciones = self.servicio.listar_devoluciones()
        self.tabla.cargar([
            (d.id, d.prestamo_id, d.prestamo.socio.nombre_completo, d.prestamo.ejemplar.libro.titulo,
             c.formatear_fecha(d.fecha), d.estado_fisico.value, d.dias_atraso, c.formatear_pesos(d.monto_multa),
             "Sí" if d.multa_pagada else "No")
            for d in devoluciones
        ])

    def cambiar_politica(self):
        self.servicio.cambiar_estrategia_de_multa(self.estrategias[self.selector_politica.get()]())
        c.informar(f"Política de multas: {self.servicio.calculadora.estrategia.descripcion}.", self)

    def registrar_devolucion(self):
        activos = [
            (f"{p.id} - {p.socio.nombre_completo} - {p.ejemplar.libro.titulo} (vence {c.formatear_fecha(p.fecha_vencimiento)})", p.id)
            for p in ServicioPrestamos().listar_prestamos([EstadoPrestamo.ACTIVO])
        ]
        datos = c.pedir_datos(self, "Registrar devolución", [
            c.Campo("id_prestamo", "Préstamo", tipo="opcion", obligatorio=True, opciones=activos),
            c.Campo("estado_fisico", "Estado físico", tipo="opcion", obligatorio=True,
                    valor=EstadoFisico.BUENO, opciones=opciones_enum(EstadoFisico)),
            c.Campo("observaciones", "Observaciones"),
        ])
        if datos and c.ejecutar(lambda: self.servicio.registrar_devolucion(**datos), self, self._mensaje_devolucion):
            self.actualizar()

    @staticmethod
    def _mensaje_devolucion(devolucion):
        mensaje = "Devolución registrada."
        if devolucion.monto_multa > 0:
            mensaje += f"\n{devolucion.dias_atraso} días de atraso: multa de {c.formatear_pesos(devolucion.monto_multa)}."
        if devolucion.prestamo.es_interbibliotecario:
            mensaje += "\nSe generó el remito de retorno a la sede propietaria."
        return mensaje

    def registrar_pago(self):
        id_devolucion = c.id_seleccionado_o_aviso(self.tabla, self, "una devolución")
        if id_devolucion is not None and c.ejecutar(
            lambda: self.servicio.registrar_pago_de_multa(id_devolucion), self, "Pago registrado."
        ):
            self.actualizar()
