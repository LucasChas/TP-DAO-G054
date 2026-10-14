"""Pestaña de administración de sedes."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.servicios import ServicioSedes


class PestaniaSedes(ttk.Frame):
    COLUMNAS = ("Id", "Nombre", "Dirección", "Teléfono", "Email", "Horario", "Estado")

    def __init__(self, padre):
        super().__init__(padre, padding=10)
        self.servicio = ServicioSedes()
        c.barra_de_botones(self, [
            ("Nueva sede", self.nueva),
            ("Modificar", self.modificar),
            ("Dar de baja", self.dar_de_baja),
            ("Reactivar", self.reactivar),
        ]).pack(fill="x")
        self.tabla = c.Tabla(self, self.COLUMNAS, anchos={"Id": 50, "Nombre": 170, "Dirección": 280, "Email": 200})
        self.tabla.pack(fill="both", expand=True, pady=(10, 0))

    def actualizar(self):
        self.tabla.cargar([
            (s.id, s.nombre, s.direccion, s.telefono, s.email, s.horario_atencion, s.estado.value)
            for s in self.servicio.listar_sedes()
        ])

    def _campos(self, sede=None):
        return [
            c.Campo("nombre", "Nombre", obligatorio=True, valor=sede and sede.nombre),
            c.Campo("direccion", "Dirección", obligatorio=True, valor=sede and sede.direccion),
            c.Campo("telefono", "Teléfono", valor=sede and sede.telefono),
            c.Campo("email", "Email", valor=sede and sede.email),
            c.Campo("horario_atencion", "Horario de atención", valor=sede and sede.horario_atencion),
        ]

    def nueva(self):
        datos = c.pedir_datos(self, "Nueva sede", self._campos())
        if datos and c.ejecutar(lambda: self.servicio.registrar_sede(**datos), self, "Sede registrada."):
            self.actualizar()

    def modificar(self):
        id_sede = c.id_seleccionado_o_aviso(self.tabla, self, "una sede")
        if id_sede is None:
            return
        sede = self.servicio.obtener_sede(id_sede)
        datos = c.pedir_datos(self, f"Modificar {sede.nombre}", self._campos(sede))
        if datos and c.ejecutar(lambda: self.servicio.modificar_sede(id_sede, **datos), self, "Sede modificada."):
            self.actualizar()

    def dar_de_baja(self):
        id_sede = c.id_seleccionado_o_aviso(self.tabla, self, "una sede")
        if id_sede is not None and c.confirmar("¿Confirma la baja de la sede seleccionada?", self):
            if c.ejecutar(lambda: self.servicio.dar_de_baja_sede(id_sede), self, "Sede dada de baja."):
                self.actualizar()

    def reactivar(self):
        id_sede = c.id_seleccionado_o_aviso(self.tabla, self, "una sede")
        if id_sede is not None and c.ejecutar(lambda: self.servicio.reactivar_sede(id_sede), self, "Sede reactivada."):
            self.actualizar()
