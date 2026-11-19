"""Pestaña de administración de sedes."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.servicios import ServicioSedes


class PestaniaSedes(ttk.Frame):
    COLUMNAS = ("Id", "Nombre", "Dirección", "Teléfono", "Email", "Horario", "Estado")
    FILTROS = ("Activas", "Dadas de baja", "Todas")

    def __init__(self, padre):
        super().__init__(padre, padding=(20, 16), style="Panel.TFrame")
        self.servicio = ServicioSedes()
        c.encabezado_de_pestania(self, "Sedes", "Las sedes de la red. La baja es lógica: la sede conserva su historial.", [
            ("Nueva sede", self.nueva, c.PRIMARIO),
        ]).pack(fill="x")

        barra = c.barra_de_filtros(self)
        barra.pack(fill="x", pady=(14, 10))
        self.busqueda = c.CampoDeBusqueda(barra.izquierda, "Buscar por nombre o dirección", self.actualizar)
        self.busqueda.pack(side="left")
        self.filtro = c.FiltroSegmentado(barra.izquierda, self.FILTROS, self.actualizar, inicial="Todas")
        self.filtro.pack(side="left", padx=(12, 0))
        self.acciones = c.acciones_de_seleccion(barra, [
            ("Modificar", self.modificar),
            ("Reactivar", self.reactivar),
            ("Dar de baja", self.dar_de_baja, c.PELIGRO),
        ])

        self.tabla = c.Tabla(self, self.COLUMNAS, columna_estado="Estado",
                             anchos={"Nombre": 170, "Dirección": 280, "Email": 200},
                             mensaje_vacio="No hay sedes para mostrar. Use \"Nueva sede\" o cargue los datos de ejemplo.")
        self.tabla.pack(fill="both", expand=True)
        self.tabla.al_doble_clic(self.modificar)
        self.tabla.al_seleccionar(self._actualizar_acciones)

    def actualizar(self):
        sedes = self.servicio.listar_sedes()
        self.filtro.mostrar_cantidades({
            "Activas": sum(s.esta_activa for s in sedes),
            "Dadas de baja": sum(not s.esta_activa for s in sedes),
            "Todas": len(sedes),
        })
        filtro, texto = self.filtro.get(), self.busqueda.get()
        visibles = [
            s for s in sedes
            if (filtro == "Todas" or s.esta_activa == (filtro == "Activas")) and c.coincide(texto, s.nombre, s.direccion)
        ]
        self.tabla.cargar([
            (s.id, s.nombre, s.direccion, s.telefono, s.email, s.horario_atencion, s.estado.value) for s in visibles
        ])
        self._actualizar_acciones()

    def _actualizar_acciones(self):
        """«Reactivar» solo se destaca si la sede elegida está dada de baja, y «Dar de baja» si está activa."""
        fila = next((f for f in self.tabla.filas() if str(f[0]) == str(self.tabla.id_seleccionado())), None)
        activa = fila is None or fila[-1] == "Activa"
        self.acciones.botones["Reactivar"].configure(style=c.ATENUADO if activa else "TButton")
        self.acciones.botones["Dar de baja"].configure(style=c.PELIGRO if activa else c.ATENUADO)

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
        campos = self._campos(sede)
        datos = c.opcionales_vacios_para_borrar(c.pedir_datos(self, f"Modificar {sede.nombre}", campos), campos)
        if datos and c.ejecutar(lambda: self.servicio.modificar_sede(id_sede, **datos), self, "Sede modificada."):
            self.actualizar()

    def dar_de_baja(self):
        id_sede = c.id_seleccionado_o_aviso(self.tabla, self, "una sede")
        if id_sede is not None and c.confirmar(
            "¿Confirma la baja de la sede seleccionada?\n"
            "Mientras esté dada de baja no podrá iniciar préstamos, reservas ni envíos. Su historial se conserva.", self):
            if c.ejecutar(lambda: self.servicio.dar_de_baja_sede(id_sede), self, "Sede dada de baja."):
                self.actualizar()

    def reactivar(self):
        id_sede = c.id_seleccionado_o_aviso(self.tabla, self, "una sede")
        if id_sede is not None and c.ejecutar(lambda: self.servicio.reactivar_sede(id_sede), self, "Sede reactivada."):
            self.actualizar()
