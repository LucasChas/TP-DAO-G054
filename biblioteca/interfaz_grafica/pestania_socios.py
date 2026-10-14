"""Pestaña de administración de socios."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.servicios import ServicioSocios


class PestaniaSocios(ttk.Frame):
    COLUMNAS = ("Id", "DNI", "Apellido y nombre", "Email", "Teléfono", "Alta", "Estado", "Motivo")

    def __init__(self, padre):
        super().__init__(padre, padding=10)
        self.servicio = ServicioSocios()
        c.barra_de_botones(self, [
            ("Nuevo socio", self.nuevo),
            ("Modificar", self.modificar),
            ("Inhabilitar", self.inhabilitar),
            ("Habilitar", self.habilitar),
        ]).pack(fill="x")
        self.tabla = c.Tabla(self, self.COLUMNAS, anchos={"Id": 50, "Apellido y nombre": 180, "Email": 210, "Motivo": 260})
        self.tabla.pack(fill="both", expand=True, pady=(10, 0))

    def actualizar(self):
        self.tabla.cargar([
            (s.id, s.dni, s.nombre_completo, s.email, s.telefono, c.formatear_fecha(s.fecha_alta),
             s.estado.value, s.motivo_inhabilitacion)
            for s in self.servicio.listar_socios()
        ])

    def nuevo(self):
        datos = c.pedir_datos(self, "Nuevo socio", [
            c.Campo("dni", "DNI", obligatorio=True),
            c.Campo("nombre", "Nombre", obligatorio=True),
            c.Campo("apellido", "Apellido", obligatorio=True),
            c.Campo("email", "Email"),
            c.Campo("telefono", "Teléfono"),
        ])
        if datos and c.ejecutar(lambda: self.servicio.registrar_socio(**datos), self, "Socio registrado."):
            self.actualizar()

    def modificar(self):
        id_socio = c.id_seleccionado_o_aviso(self.tabla, self, "un socio")
        if id_socio is None:
            return
        socio = self.servicio.obtener_socio(id_socio)
        datos = c.pedir_datos(self, f"Modificar {socio.nombre_completo}", [
            c.Campo("nombre", "Nombre", obligatorio=True, valor=socio.nombre),
            c.Campo("apellido", "Apellido", obligatorio=True, valor=socio.apellido),
            c.Campo("email", "Email", valor=socio.email),
            c.Campo("telefono", "Teléfono", valor=socio.telefono),
        ])
        if datos and c.ejecutar(lambda: self.servicio.modificar_socio(id_socio, **datos), self, "Socio modificado."):
            self.actualizar()

    def inhabilitar(self):
        id_socio = c.id_seleccionado_o_aviso(self.tabla, self, "un socio")
        if id_socio is None:
            return
        datos = c.pedir_datos(self, "Inhabilitar socio", [c.Campo("motivo", "Motivo", obligatorio=True)])
        if datos and c.ejecutar(lambda: self.servicio.inhabilitar_socio(id_socio, datos["motivo"]), self, "Socio inhabilitado."):
            self.actualizar()

    def habilitar(self):
        id_socio = c.id_seleccionado_o_aviso(self.tabla, self, "un socio")
        if id_socio is not None and c.ejecutar(lambda: self.servicio.habilitar_socio(id_socio), self, "Socio habilitado."):
            self.actualizar()
