"""Pestaña de devoluciones y multas, con la política de multas vigente (patrón Strategy)."""
import tkinter as tk
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import destino_del_ejemplar, numero_de_remito, opciones_enum
from biblioteca.modelos.enumeraciones import EstadoFisico, EstadoPrestamo, SentidoRemito
from biblioteca.patrones.estrategias_multa import ESTRATEGIAS_DISPONIBLES
from biblioteca.servicios import ServicioPrestamos


class PestaniaDevoluciones(ttk.Frame):
    COLUMNAS = ("Id", "Préstamo", "Socio", "Libro", "Fecha", "Estado físico", "Días de atraso", "Por atraso", "Por daño",
                "Total", "Pagada", "Pago")
    FILTROS = ("Todas", "Impagas", "Pagadas")

    def __init__(self, padre, servicio):
        """servicio es el ServicioDevoluciones compartido con la pestaña de reportes,
        así ambos usan la misma política de multas."""
        super().__init__(padre, padding=(20, 16), style="Panel.TFrame")
        self.servicio = servicio
        c.encabezado_de_pestania(
            self, "Devoluciones y multas", "La multa se calcula al registrar la devolución, con la política vigente.", [
                ("Registrar devolución", self.registrar_devolucion, c.PRIMARIO),
            ]).pack(fill="x")

        politica = ttk.Frame(self, style="Tarjeta.TFrame", padding=(12, 8))
        politica.pack(fill="x", pady=(14, 0))
        ttk.Label(politica, text="Política de multas vigente", style="PanelNegrita.TLabel").grid(row=0, column=0, sticky="w")
        self.estrategias = {clase().descripcion: clase for clase in ESTRATEGIAS_DISPONIBLES}
        self.selector_politica = ttk.Combobox(politica, values=list(self.estrategias), state="readonly", width=64)
        self.selector_politica.set(self.servicio.calculadora.estrategia.descripcion)
        self.selector_politica.grid(row=0, column=1, sticky="w", padx=10)
        self.selector_politica.bind("<<ComboboxSelected>>", lambda evento: self.cambiar_politica())
        cargo = getattr(self.servicio.calculadora, "CARGO_POR_DANIO", None)
        aclaracion = "Se aplica a las devoluciones que se registren desde ahora; las ya registradas no cambian."
        if cargo:
            aclaracion = f"Además, {c.formatear_pesos(cargo)} si el material vuelve dañado. " + aclaracion
        ttk.Label(politica, text=aclaracion, style="PanelSuave.TLabel").grid(row=1, column=1, sticky="w", padx=10, pady=(4, 0))

        barra = c.barra_de_filtros(self)
        barra.pack(fill="x", pady=(12, 10))
        self.busqueda = c.CampoDeBusqueda(barra, "Buscar por socio o libro", self.actualizar, ancho=30)
        self.busqueda.pack(side="left")
        # solo_impagas se mantiene como variable: equivale a elegir el filtro "Impagas".
        self.solo_impagas = tk.BooleanVar(value=False)
        self.filtro = c.FiltroSegmentado(barra, self.FILTROS, self._al_elegir_filtro)
        self.filtro.pack(side="left", padx=(12, 0))
        self.acciones = c.acciones_de_seleccion(barra, [("Registrar pago de multa", self.registrar_pago)])
        self.tabla = c.Tabla(self, self.COLUMNAS, columna_estado="Pago", ocultas=("Id", "Préstamo", "Pagada"),
                             anchos={"Socio": 150, "Libro": 170},
                             mensaje_vacio="No hay devoluciones para mostrar.")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.al_seleccionar(self._actualizar_acciones)

    def _al_elegir_filtro(self):
        self.solo_impagas.set(self.filtro.get() == "Impagas")
        self.actualizar()

    @staticmethod
    def _pago(devolucion):
        if devolucion.monto_multa <= 0:
            return "Sin multa"
        return "Pagada" if devolucion.multa_pagada else "Impaga"

    def actualizar(self):
        if self.solo_impagas.get() and self.filtro.get() != "Impagas":
            self.filtro.set("Impagas")
        elif not self.solo_impagas.get() and self.filtro.get() == "Impagas":
            self.filtro.set("Todas")
        devoluciones = self.servicio.listar_devoluciones()
        grupos = {
            "Todas": devoluciones,
            "Impagas": [d for d in devoluciones if self._pago(d) == "Impaga"],
            "Pagadas": [d for d in devoluciones if self._pago(d) == "Pagada"],
        }
        self.filtro.mostrar_cantidades({nombre: len(lista) for nombre, lista in grupos.items()})
        texto = self.busqueda.get()
        self.tabla.cargar([
            (d.id, d.prestamo_id, d.prestamo.socio.nombre_completo, d.prestamo.ejemplar.libro.titulo,
             c.formatear_fecha(d.fecha), d.estado_fisico.value, d.dias_atraso, c.formatear_pesos(d.multa_por_atraso),
             c.formatear_pesos(d.cargo_por_danio), c.formatear_pesos(d.monto_multa), "Sí" if d.multa_pagada else "No",
             self._pago(d))
            for d in grupos[self.filtro.get()]
            if c.coincide(texto, d.prestamo.socio.nombre_completo, d.prestamo.ejemplar.libro.titulo)
        ])
        self._actualizar_acciones()

    def _actualizar_acciones(self):
        """«Registrar pago de multa» se destaca cuando la devolución elegida tiene la multa impaga."""
        fila = next((f for f in self.tabla.filas() if str(f[0]) == str(self.tabla.id_seleccionado())), None)
        impaga = fila is not None and fila[-1] == "Impaga"
        self.acciones.botones["Registrar pago de multa"].configure(style=c.PRIMARIO if impaga else "TButton")

    def cambiar_politica(self):
        self.servicio.cambiar_estrategia_de_multa(self.estrategias[self.selector_politica.get()]())
        c.informar(f"Política de multas cambiada a: {self.servicio.calculadora.estrategia.descripcion}.\n"
                  "Se aplica a las próximas devoluciones; las ya registradas no cambian.", self)

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
        if devolucion.multa_por_atraso > 0:
            mensaje += f"\n{devolucion.dias_atraso} días de atraso: multa de {c.formatear_pesos(devolucion.multa_por_atraso)}."
        if devolucion.cargo_por_danio > 0:
            mensaje += f"\nMaterial devuelto dañado: cargo de {c.formatear_pesos(devolucion.cargo_por_danio)}."
        if devolucion.monto_multa > 0:
            mensaje += f"\nTotal a pagar: {c.formatear_pesos(devolucion.monto_multa)}."
        prestamo = devolucion.prestamo
        if prestamo.es_interbibliotecario:
            numero = numero_de_remito(prestamo.id, SentidoRemito.RETORNO)
            mensaje += (f"\nSe generó el remito de retorno {numero} a la sede propietaria."
                        "\nSiguiente paso: en Remitos, empaquetarlo y despacharlo.")
        else:
            ejemplar = prestamo.ejemplar
            mensaje += f"\nEl ejemplar {ejemplar.codigo_inventario} {destino_del_ejemplar(ejemplar)}."
        return mensaje

    def registrar_pago(self):
        id_devolucion = c.id_seleccionado_o_aviso(self.tabla, self, "una devolución")
        if id_devolucion is not None and c.ejecutar(
            lambda: self.servicio.registrar_pago_de_multa(id_devolucion), self, "Pago registrado."
        ):
            self.actualizar()
