"""Pestaña del catálogo: libros arriba y los ejemplares del libro elegido abajo."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import destino_del_ejemplar, opciones_enum, opciones_sedes
from biblioteca.modelos.enumeraciones import TipoMaterial
from biblioteca.servicios import ServicioCatalogo, ServicioDisponibilidad


class PestaniaCatalogo(ttk.Frame):
    COLUMNAS_LIBROS = ("Id", "ISBN", "Título", "Autor", "Editorial", "Año", "Tipo", "Disponibles")
    COLUMNAS_EJEMPLARES = ("Id", "Código", "Sede propietaria", "Estado", "Estado físico")
    TITULO_EJEMPLARES = "Elija un libro para ver sus ejemplares"
    FILTROS = ("Todos", "Libros", "Revistas", "Consulta")
    TIPO_POR_FILTRO = {"Libros": TipoMaterial.LIBRO, "Revistas": TipoMaterial.REVISTA, "Consulta": TipoMaterial.CONSULTA}

    def __init__(self, padre):
        super().__init__(padre, padding=(20, 16), style="Panel.TFrame")
        self.servicio = ServicioCatalogo()
        c.encabezado_de_pestania(self, "Catálogo", "Libros de la red y sus ejemplares en cada sede.", [
            ("Nuevo libro", self.nuevo_libro, c.PRIMARIO),
        ]).pack(fill="x")

        barra = c.barra_de_filtros(self)
        barra.pack(fill="x", pady=(14, 10))
        self.campo_busqueda = c.CampoDeBusqueda(barra, "Buscar por título o autor", self._al_escribir)
        self.campo_busqueda.pack(side="left")
        self.busqueda = self.campo_busqueda.entrada
        self.busqueda.bind("<Return>", lambda evento: self.buscar())
        self.texto_buscado = None
        self.filtro = c.FiltroSegmentado(barra, self.FILTROS, self.actualizar)
        self.filtro.pack(side="left", padx=(12, 0))
        c.acciones_de_seleccion(barra, [
            ("Modificar libro", self.modificar_libro),
            ("Ver disponibilidad", self.ver_disponibilidad),
        ])

        division, self.tabla_libros, self.detalle = c.division_vertical(
            self,
            lambda padre: c.Tabla(padre, self.COLUMNAS_LIBROS, alto=7, ocultas=("Id", "ISBN"),
                                  anchos={"Título": 260, "Autor": 200, "Año": 60, "Disponibles": 100},
                                  mensaje_vacio="No hay libros para mostrar."),
            lambda padre: c.PanelDeDetalle(padre, self.TITULO_EJEMPLARES),
            proporcion=0.55,
        )
        division.pack(fill="both", expand=True)
        self.tabla_libros.al_seleccionar(self.actualizar_ejemplares)
        self.tabla_libros.al_doble_clic(self.modificar_libro)
        c.barra_de_botones(self.detalle.acciones, [
            ("Nuevo ejemplar", self.nuevo_ejemplar),
            ("Finalizar reparación", self.finalizar_reparacion),
            ("Dar de baja ejemplar", self.dar_de_baja_ejemplar, c.PELIGRO),
        ], estilo_marco="DetalleCabecera.TFrame").pack(side="right")
        self.tabla_ejemplares = c.Tabla(self.detalle.cuerpo, self.COLUMNAS_EJEMPLARES, alto=3, columna_estado="Estado",
                                        anchos={"Sede propietaria": 200},
                                        mensaje_vacio="Elija un libro de la lista para ver sus ejemplares.")
        self.tabla_ejemplares.pack(fill="both", expand=True)

    def _al_escribir(self):
        """Filtra mientras se escribe; Enter hace la búsqueda con aviso si no hay resultados."""
        self.texto_buscado = self.campo_busqueda.get() or None
        self.actualizar()

    def actualizar(self):
        if self.texto_buscado:
            libros = self.servicio.buscar_libros(self.texto_buscado)
        else:
            libros = self.servicio.listar_libros()
        cantidades = {"Todos": len(libros)}
        for filtro, tipo in self.TIPO_POR_FILTRO.items():
            cantidades[filtro] = sum(l.tipo_material == tipo for l in libros)
        self.filtro.mostrar_cantidades(cantidades)
        tipo = self.TIPO_POR_FILTRO.get(self.filtro.get())
        disponibilidad = ServicioDisponibilidad()
        filas = []
        for libro in libros:
            if tipo is not None and libro.tipo_material != tipo:
                continue
            por_sede = disponibilidad.consultar_disponibilidad(libro.id)
            disponibles = f"{sum(r.disponibles for r in por_sede)} de {sum(r.total for r in por_sede)}"
            filas.append((libro.id, libro.isbn, libro.titulo, libro.autor, libro.editorial, libro.anio_publicacion,
                          libro.tipo_material.value, disponibles))
        self.tabla_libros.cargar(filas)
        self.actualizar_ejemplares()

    def buscar(self):
        """Muestra solo los libros cuyo título o autor contienen el texto ingresado."""
        texto = self.busqueda.get().strip()
        if not texto:
            c.avisar("Escriba parte del título o del autor para buscar.", self)
            return
        self.texto_buscado = texto
        self.actualizar()
        if not self.tabla_libros.filas():
            c.informar(f"No hay libros cuyo título o autor contenga '{texto}'.", self)

    def ver_todos(self):
        self.campo_busqueda.limpiar()
        self.texto_buscado = None
        self.filtro.set("Todos")
        self.actualizar()

    def actualizar_ejemplares(self):
        id_libro = self.tabla_libros.id_seleccionado()
        ejemplares = self.servicio.listar_ejemplares(id_libro=id_libro) if id_libro else []
        fila = next((f for f in self.tabla_libros.filas() if id_libro and str(f[0]) == str(id_libro)), None)
        if fila:
            sedes = len({e.sede_id for e in ejemplares})
            self.detalle.mostrar(f"Ejemplares de '{fila[2]}'",
                                 f"{len(ejemplares)} ejemplar{'es' if len(ejemplares) != 1 else ''} en "
                                 f"{sedes} sede{'s' if sedes != 1 else ''}")
        else:
            self.detalle.mostrar(self.TITULO_EJEMPLARES)
        self.tabla_ejemplares.cargar([
            (e.id, e.codigo_inventario, e.sede.nombre, e.estado.value, e.estado_fisico.value) for e in ejemplares
        ])

    def _campos_libro(self, libro=None):
        campos = [] if libro else [c.Campo("isbn", "ISBN", obligatorio=True)]
        return campos + [
            c.Campo("titulo", "Título", obligatorio=True, valor=libro and libro.titulo),
            c.Campo("autor", "Autor", obligatorio=True, valor=libro and libro.autor),
            c.Campo("editorial", "Editorial", valor=libro and libro.editorial),
            c.Campo("anio_publicacion", "Año de publicación", tipo="entero", valor=libro and libro.anio_publicacion),
            c.Campo("tipo_material", "Tipo de material", tipo="opcion", obligatorio=True,
                    valor=libro.tipo_material if libro else TipoMaterial.LIBRO, opciones=opciones_enum(TipoMaterial)),
        ]

    def nuevo_libro(self):
        datos = c.pedir_datos(self, "Nuevo libro", self._campos_libro())
        if datos and c.ejecutar(lambda: self.servicio.registrar_libro(**datos), self, "Libro registrado."):
            self.actualizar()

    def modificar_libro(self):
        id_libro = c.id_seleccionado_o_aviso(self.tabla_libros, self, "un libro")
        if id_libro is None:
            return
        libro = self.servicio.obtener_libro(id_libro)
        campos = self._campos_libro(libro)
        datos = c.opcionales_vacios_para_borrar(c.pedir_datos(self, f"Modificar {libro.titulo}", campos), campos)
        if datos and c.ejecutar(lambda: self.servicio.modificar_libro(id_libro, **datos), self, "Libro modificado."):
            self.actualizar()

    def ver_disponibilidad(self):
        id_libro = c.id_seleccionado_o_aviso(self.tabla_libros, self, "un libro")
        if id_libro is None:
            return
        libro = self.servicio.obtener_libro(id_libro)
        filas = [
            (r.sede if r.sede_activa else f"{r.sede} (baja)", r.total, r.disponibles, r.reservados, r.prestados, r.en_transito)
            for r in ServicioDisponibilidad().consultar_disponibilidad(id_libro)
        ]
        c.mostrar_tabla_en_ventana(
            self, f"Disponibilidad de '{libro.titulo}'",
            ("Sede", "Total", "Disponibles", "Reservados", "Prestados", "En tránsito"), filas,
            anchos={"Sede": 200, "Total": 70},
        )

    def nuevo_ejemplar(self):
        id_libro = c.id_seleccionado_o_aviso(self.tabla_libros, self, "un libro")
        if id_libro is None:
            return
        datos = c.pedir_datos(self, "Nuevo ejemplar", [
            c.Campo("id_sede", "Sede propietaria", tipo="opcion", obligatorio=True, opciones=opciones_sedes()),
            c.Campo("codigo_inventario", "Código de inventario", obligatorio=True),
        ])
        if datos and c.ejecutar(lambda: self.servicio.registrar_ejemplar(id_libro, **datos), self, "Ejemplar registrado."):
            self.actualizar()

    def finalizar_reparacion(self):
        id_ejemplar = c.id_seleccionado_o_aviso(self.tabla_ejemplares, self, "un ejemplar")
        if id_ejemplar is not None and c.ejecutar(
            lambda: self.servicio.finalizar_reparacion(id_ejemplar), self,
            lambda e: f"Reparación finalizada: el ejemplar {e.codigo_inventario} queda con estado físico Regular "
                      f"y {destino_del_ejemplar(e)}.",
        ):
            self.actualizar()

    def dar_de_baja_ejemplar(self):
        id_ejemplar = c.id_seleccionado_o_aviso(self.tabla_ejemplares, self, "un ejemplar")
        if id_ejemplar is not None and c.confirmar("¿Confirma la baja del ejemplar seleccionado?", self):
            if c.ejecutar(lambda: self.servicio.dar_de_baja_ejemplar(id_ejemplar), self, "Ejemplar dado de baja."):
                self.actualizar()
