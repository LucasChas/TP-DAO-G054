"""Pestaña de préstamos locales e interbibliotecarios."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import opciones_ejemplares, opciones_sedes, opciones_socios
from biblioteca.modelos.enumeraciones import EstadoPrestamo
from biblioteca.servicios import ServicioPrestamos

EN_CURSO = [EstadoPrestamo.SOLICITADO, EstadoPrestamo.EN_ENVIO, EstadoPrestamo.LISTO_PARA_RETIRO, EstadoPrestamo.ACTIVO]


class PestaniaPrestamos(ttk.Frame):
    COLUMNAS = ("Id", "Tipo", "Socio", "Ejemplar", "Libro", "Origen", "Destino", "Solicitud", "Vence", "Estado")
    FILTROS = ("En curso", "Vencidos", "Todos")

    def __init__(self, padre):
        super().__init__(padre, padding=10)
        self.servicio = ServicioPrestamos()
        barra = c.barra_de_botones(self, [
            ("Préstamo local", self.prestamo_local),
            ("Préstamo interbibliotecario", self.prestamo_interbibliotecario),
            ("Entregar al socio", self.entregar),
            ("Cancelar solicitud", self.cancelar),
        ])
        barra.pack(fill="x")
        ttk.Label(barra, text="Mostrar:").pack(side="left", padx=(20, 4))
        self.filtro = ttk.Combobox(barra, values=self.FILTROS, state="readonly", width=12)
        self.filtro.set(self.FILTROS[0])
        self.filtro.pack(side="left")
        self.filtro.bind("<<ComboboxSelected>>", lambda evento: self.actualizar())
        self.tabla = c.Tabla(self, self.COLUMNAS, anchos={"Id": 50, "Tipo": 130, "Socio": 150, "Libro": 190, "Origen": 140, "Destino": 140})
        self.tabla.pack(fill="both", expand=True, pady=(10, 0))

    def actualizar(self):
        filtro = self.filtro.get()
        if filtro == "Vencidos":
            prestamos = self.servicio.listar_vencidos()
        else:
            prestamos = self.servicio.listar_prestamos(EN_CURSO if filtro == "En curso" else None)
        self.tabla.cargar([
            (p.id, p.tipo.value, p.socio.nombre_completo, p.ejemplar.codigo_inventario, p.ejemplar.libro.titulo,
             p.sede_origen.nombre, p.sede_destino.nombre, c.formatear_fecha(p.fecha_solicitud),
             c.formatear_fecha(p.fecha_vencimiento), p.estado.value)
            for p in prestamos
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
            lambda p: f"Préstamo registrado. Vence el {c.formatear_fecha(p.fecha_vencimiento)}.",
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
            "Solicitud registrada. Se generó el remito de ida.",
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
            if c.ejecutar(lambda: self.servicio.cancelar_prestamo(id_prestamo), self, "Solicitud cancelada."):
                self.actualizar()
