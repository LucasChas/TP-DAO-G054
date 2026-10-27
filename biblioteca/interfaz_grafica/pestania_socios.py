"""Pestaña de administración de socios."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.servicios import ServicioSocios


class PestaniaSocios(ttk.Frame):
    COLUMNAS = ("Id", "DNI", "Apellido y nombre", "Email", "Teléfono", "Alta", "Estado", "Motivo")

    def __init__(self, padre):
        super().__init__(padre, padding=10)
        self.servicio = ServicioSocios()
        barra = c.barra_de_botones(self, [
            ("Nuevo socio", self.nuevo),
            ("Modificar", self.modificar),
            ("Inhabilitar", self.inhabilitar),
            ("Habilitar", self.habilitar),
        ])
        barra.pack(fill="x")
        ttk.Label(barra, text="DNI:").pack(side="left", padx=(20, 4))
        self.busqueda_dni = ttk.Entry(barra, width=14)
        self.busqueda_dni.pack(side="left")
        self.busqueda_dni.bind("<Return>", lambda evento: self.buscar_por_dni())
        ttk.Button(barra, text="Buscar por DNI", command=self.buscar_por_dni).pack(side="left", padx=(6, 0))
        self.tabla = c.Tabla(self, self.COLUMNAS, anchos={"Id": 50, "Apellido y nombre": 180, "Email": 210, "Motivo": 260})
        self.tabla.pack(fill="both", expand=True, pady=(10, 0))

    def actualizar(self):
        self.tabla.cargar([
            (s.id, s.dni, s.nombre_completo, s.email, s.telefono, c.formatear_fecha(s.fecha_alta),
             s.estado.value, s.motivo_inhabilitacion)
            for s in self.servicio.listar_socios()
        ])

    def buscar_por_dni(self):
        """Busca el socio y deja seleccionada su fila, así se le pueden aplicar las acciones."""
        socio = c.ejecutar(lambda: self.servicio.buscar_por_dni(self.busqueda_dni.get()), self)
        if socio is None:
            return
        self.actualizar()
        self.tabla.seleccionar_id(socio.id)

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
        campos = [
            c.Campo("nombre", "Nombre", obligatorio=True, valor=socio.nombre),
            c.Campo("apellido", "Apellido", obligatorio=True, valor=socio.apellido),
            c.Campo("email", "Email", valor=socio.email),
            c.Campo("telefono", "Teléfono", valor=socio.telefono),
        ]
        datos = c.opcionales_vacios_para_borrar(c.pedir_datos(self, f"Modificar {socio.nombre_completo}", campos), campos)
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
