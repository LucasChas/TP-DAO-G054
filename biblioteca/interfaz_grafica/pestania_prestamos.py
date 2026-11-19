"""Pestaña de préstamos locales e interbibliotecarios."""
from datetime import date, timedelta

from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import (
    destino_del_ejemplar, numero_de_remito, opciones_ejemplares, opciones_sedes, opciones_socios,
)
from biblioteca.modelos.enumeraciones import EstadoPrestamo, SentidoRemito
from biblioteca.servicios import ServicioPrestamos

EN_CURSO = [EstadoPrestamo.SOLICITADO, EstadoPrestamo.EN_ENVIO, EstadoPrestamo.LISTO_PARA_RETIRO, EstadoPrestamo.ACTIVO]


class PestaniaPrestamos(ttk.Frame):
    COLUMNAS = ("Id", "Tipo", "Socio", "Ejemplar", "Libro", "Origen", "Destino", "Solicitud", "Vence", "Estado")
    FILTROS = ("En curso", "Por vencer", "Vencidos", "Todos")
    DIAS_POR_VENCER = 3

    def __init__(self, padre):
        super().__init__(padre, padding=(20, 16), style="Panel.TFrame")
        self.servicio = ServicioPrestamos()
        c.encabezado_de_pestania(
            self, "Préstamos", "Locales e interbibliotecarios. Los interbibliotecarios generan su remito de ida.", [
                ("Préstamo local", self.prestamo_local, c.PRIMARIO),
                ("Préstamo interbibliotecario", self.prestamo_interbibliotecario),
            ]).pack(fill="x")

        barra = c.barra_de_filtros(self)
        barra.pack(fill="x", pady=(14, 10))
        self.busqueda = c.CampoDeBusqueda(barra, "Buscar por socio, libro o ejemplar", self.actualizar, ancho=26)
        self.busqueda.pack(side="left")
        self.filtro = c.FiltroSegmentado(barra, self.FILTROS, self.actualizar)
        self.filtro.pack(side="left", padx=(12, 0))
        acciones = c.barra_de_botones(barra, [
            ("Entregar (interbibliotecario)", self.entregar),
            ("Cancelar solicitud (interbibliotecario)", self.cancelar, c.PELIGRO),
        ])
        acciones.pack(side="right")
        self.tabla = c.Tabla(self, self.COLUMNAS, columna_estado="Estado",
                             anchos={"Tipo": 130, "Socio": 150, "Libro": 190, "Origen": 140, "Destino": 140},
                             mensaje_vacio="No hay préstamos para el filtro elegido.")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.arbol.heading("Destino", text="Retira en")

    def actualizar(self):
        todos = self.servicio.listar_prestamos()
        hoy = date.today()
        vencidos = {p.id for p in self.servicio.listar_vencidos()}
        limite = hoy + timedelta(days=self.DIAS_POR_VENCER)
        por_vencer = {
            p.id for p in todos
            if p.estado == EstadoPrestamo.ACTIVO and p.id not in vencidos
            and p.fecha_vencimiento is not None and p.fecha_vencimiento <= limite
        }
        grupos = {
            "En curso": {p.id for p in todos if p.estado in EN_CURSO},
            "Por vencer": por_vencer,
            "Vencidos": vencidos,
            "Todos": {p.id for p in todos},
        }
        self.filtro.mostrar_cantidades({nombre: len(ids) for nombre, ids in grupos.items()})
        elegidos, texto = grupos[self.filtro.get()], self.busqueda.get()
        self.tabla.cargar([
            (p.id, p.tipo.value, p.socio.nombre_completo, p.ejemplar.codigo_inventario, p.ejemplar.libro.titulo,
             p.sede_origen.nombre, p.sede_destino.nombre, c.formatear_fecha(p.fecha_solicitud),
             c.formatear_fecha(p.fecha_vencimiento), p.estado.value)
            for p in todos
            if p.id in elegidos and c.coincide(texto, p.socio.nombre_completo, p.ejemplar.libro.titulo,
                                                p.ejemplar.codigo_inventario)
        ])

    def prestamo_local(self):
        datos = c.pedir_datos(self, "Préstamo local", [
            c.Campo("id_socio", "Socio", tipo="opcion", obligatorio=True, opciones=opciones_socios()),
            c.Campo("id_sede", "Sede", tipo="opcion", obligatorio=True, opciones=opciones_sedes()),
            c.Campo("id_ejemplar", "Ejemplar de la sede", tipo="opcion", obligatorio=True,
                    depende_de="id_sede", opciones_segun=opciones_ejemplares),
        ])
        if datos and c.ejecutar(
            lambda: self.servicio.registrar_prestamo_local(**datos), self,
            lambda p: f"Préstamo local registrado y entregado al socio. Vence el {c.formatear_fecha(p.fecha_vencimiento)} (14 días).",
        ):
            self.actualizar()

    def prestamo_interbibliotecario(self):
        datos = c.pedir_datos(self, "Préstamo interbibliotecario", [
            c.Campo("id_socio", "Socio", tipo="opcion", obligatorio=True, opciones=opciones_socios()),
            c.Campo("id_sede_origen", "Sede de origen (dueña del ejemplar)", tipo="opcion", obligatorio=True, opciones=opciones_sedes()),
            c.Campo("id_sede_destino", "Sede de destino (retiro)", tipo="opcion", obligatorio=True, opciones=opciones_sedes()),
            c.Campo("id_ejemplar", "Ejemplar de la sede de origen", tipo="opcion", obligatorio=True,
                    depende_de="id_sede_origen", opciones_segun=opciones_ejemplares),
        ])
        if datos and c.ejecutar(
            lambda: self.servicio.solicitar_prestamo_interbibliotecario(**datos), self,
            lambda p: f"Solicitud registrada. Se generó el remito de ida {numero_de_remito(p.id, SentidoRemito.IDA)}.\n"
                      "Siguiente paso: en Remitos, empaquetarlo y despacharlo.",
        ):
            self.actualizar()

    def entregar(self):
        id_prestamo = c.id_seleccionado_o_aviso(self.tabla, self, "un préstamo")
        if id_prestamo is not None and c.ejecutar(
            lambda: self.servicio.entregar_prestamo(id_prestamo), self,
            lambda p: f"Préstamo entregado. Vence el {c.formatear_fecha(p.fecha_vencimiento)}.",
        ):
            self.actualizar()

    def cancelar(self):
        id_prestamo = c.id_seleccionado_o_aviso(self.tabla, self, "un préstamo")
        if id_prestamo is not None and c.confirmar("¿Cancelar la solicitud seleccionada?", self):
            if c.ejecutar(
                lambda: self.servicio.cancelar_prestamo(id_prestamo), self,
                lambda p: f"Solicitud cancelada: se anuló el remito de ida {numero_de_remito(p.id, SentidoRemito.IDA)} "
                          f"y el ejemplar {p.ejemplar.codigo_inventario} {destino_del_ejemplar(p.ejemplar)}.",
            ):
                self.actualizar()
