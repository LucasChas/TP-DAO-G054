"""Pestaña de administración de socios, con la situación de cada uno y sus préstamos debajo."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.servicios import ServicioDevoluciones, ServicioPrestamos, ServicioReservas, ServicioSocios


class PestaniaSocios(ttk.Frame):
    COLUMNAS = ("Id", "DNI", "Apellido y nombre", "Email", "Teléfono", "Alta", "Estado", "Motivo", "Situación")
    COLUMNAS_PRESTAMOS = ("Id", "Libro", "Ejemplar", "Tipo", "Solicitado", "Vence", "Estado")
    FILTROS = ("Todos", "Habilitados", "Inhabilitados", "Con deuda")

    def __init__(self, padre):
        super().__init__(padre, padding=(20, 16), style="Panel.TFrame")
        self.servicio = ServicioSocios()
        self._situacion = {}
        c.encabezado_de_pestania(self, "Socios", "Personas habilitadas para pedir préstamos y reservas.", [
            ("Nuevo socio", self.nuevo, c.PRIMARIO),
        ]).pack(fill="x")

        barra = c.barra_de_filtros(self)
        barra.pack(fill="x", pady=(14, 10))
        busqueda = c.CampoDeBusqueda(barra.izquierda, "Buscar por nombre o DNI", self.actualizar, ancho=30)
        busqueda.pack(side="left")
        self.busqueda = busqueda
        self.busqueda_dni = busqueda.entrada
        self.busqueda_dni.bind("<Return>", lambda evento: self.buscar_por_dni())
        ttk.Button(barra.izquierda, text="Buscar por DNI", command=self.buscar_por_dni).pack(side="left", padx=(8, 0))
        self.filtro = c.FiltroSegmentado(barra.izquierda, self.FILTROS, self.actualizar)
        self.filtro.pack(side="left", padx=(12, 0))

        division, self.tabla, self.detalle = c.division_vertical(
            self,
            lambda padre: c.Tabla(padre, self.COLUMNAS, alto=5, columna_estado="Estado", ocultas=("Id", "Alta", "Motivo"),
                                  anchos={"Apellido y nombre": 170, "Email": 200, "Situación": 260},
                                  mensaje_vacio="No hay socios para mostrar."),
            lambda padre: c.PanelDeDetalle(padre, "Elija un socio para ver sus préstamos"),
            proporcion=0.5,
        )
        division.pack(fill="both", expand=True)
        self.tabla.al_seleccionar(self.actualizar_detalle)
        self.tabla.al_doble_clic(self.modificar)
        self.acciones = c.barra_de_botones(self.detalle.acciones, [
            ("Modificar", self.modificar),
            ("Habilitar", self.habilitar),
            ("Inhabilitar", self.inhabilitar, c.PELIGRO),
        ], estilo_marco="DetalleCabecera.TFrame")
        self.acciones.pack(side="right")

    # --- Listado ---------------------------------------------------------------------------

    def actualizar(self):
        socios = self.servicio.listar_socios()
        self._situacion = self._calcular_situacion()
        con_deuda = {id_socio for id_socio, datos in self._situacion.items() if datos["vencidos"] or datos["deuda"]}
        self.filtro.mostrar_cantidades({
            "Todos": len(socios),
            "Habilitados": sum(s.esta_habilitado for s in socios),
            "Inhabilitados": sum(not s.esta_habilitado for s in socios),
            "Con deuda": len(con_deuda),
        })
        filtro, texto = self.filtro.get(), self.busqueda.get()
        visibles = [
            s for s in socios
            if c.coincide(texto, s.nombre_completo, s.dni) and (
                filtro == "Todos"
                or (filtro == "Habilitados" and s.esta_habilitado)
                or (filtro == "Inhabilitados" and not s.esta_habilitado)
                or (filtro == "Con deuda" and s.id in con_deuda))
        ]
        self.tabla.cargar([
            (s.id, s.dni, s.nombre_completo, s.email, s.telefono, c.formatear_fecha(s.fecha_alta),
             s.estado.value, s.motivo_inhabilitacion, self._texto_situacion(s))
            for s in visibles
        ])
        self.actualizar_detalle()

    @staticmethod
    def _calcular_situacion():
        """Préstamos vencidos, multas impagas y reservas activas de cada socio, en tres consultas."""
        situacion = {}

        def de(id_socio):
            return situacion.setdefault(id_socio, {"vencidos": [], "deuda": 0.0, "reservas": 0})

        for prestamo in ServicioPrestamos().listar_vencidos():
            de(prestamo.socio_id)["vencidos"].append(prestamo)
        for devolucion in ServicioDevoluciones().listar_multas_impagas():
            de(devolucion.prestamo.socio_id)["deuda"] += devolucion.monto_multa
        for reserva in ServicioReservas().listar_reservas(solo_activas=True):
            de(reserva.socio_id)["reservas"] += 1
        return situacion

    def _texto_situacion(self, socio):
        if not socio.esta_habilitado:
            return socio.motivo_inhabilitacion or "Inhabilitado"
        datos = self._situacion.get(socio.id)
        if not datos:
            return "Al día"
        partes = []
        if datos["vencidos"]:
            cantidad = len(datos["vencidos"])
            partes.append(f"{cantidad} préstamo{'s' if cantidad > 1 else ''} vencido{'s' if cantidad > 1 else ''}")
        if datos["deuda"]:
            partes.append(f"multa impaga {c.formatear_pesos(datos['deuda'])}")
        if datos["reservas"]:
            partes.append(f"{datos['reservas']} reserva{'s' if datos['reservas'] > 1 else ''} activa{'s' if datos['reservas'] > 1 else ''}")
        return ", ".join(partes).capitalize() if partes else "Al día"

    # --- Detalle del socio elegido ----------------------------------------------------------

    def actualizar_detalle(self):
        id_socio = self.tabla.id_seleccionado()
        self.detalle.vaciar()
        if id_socio is None:
            return
        socio = self.servicio.obtener_socio(id_socio)
        self.acciones.botones["Habilitar"].configure(style=c.ATENUADO if socio.esta_habilitado else "TButton")
        self.acciones.botones["Inhabilitar"].configure(style=c.PELIGRO if socio.esta_habilitado else c.ATENUADO)
        prestamos = ServicioPrestamos().listar_prestamos_de_socio(id_socio)
        datos = self._situacion.get(id_socio, {"vencidos": [], "deuda": 0.0, "reservas": 0})
        self.detalle.mostrar(f"Préstamos de {socio.nombre_completo}",
                             f"DNI {socio.dni}  ·  socio desde el {c.formatear_fecha(socio.fecha_alta)}")

        historial = c.Tabla(self.detalle.cuerpo, self.COLUMNAS_PRESTAMOS, alto=3, columna_estado="Estado",
                            mensaje_vacio="El socio todavía no tuvo préstamos.")
        historial.pack(fill="both", expand=True)
        ids_vencidos = {p.id for p in datos["vencidos"]}
        historial.cargar([
            (p.id, p.ejemplar.libro.titulo, p.ejemplar.codigo_inventario, p.tipo.value,
             c.formatear_fecha(p.fecha_solicitud), c.formatear_fecha(p.fecha_vencimiento),
             "Vencido" if p.id in ids_vencidos else p.estado.value)
            for p in prestamos
        ])

    # --- Acciones --------------------------------------------------------------------------

    def buscar_por_dni(self):
        """Busca el socio y deja seleccionada su fila, así se le pueden aplicar las acciones."""
        socio = c.ejecutar(lambda: self.servicio.buscar_por_dni(self.busqueda_dni.get()), self)
        if socio is None:
            return
        self.filtro.set("Todos")
        self.actualizar()
        self.tabla.seleccionar_id(socio.id)
        self.actualizar_detalle()

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
