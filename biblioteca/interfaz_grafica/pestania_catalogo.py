"""Pestaña del catálogo: libros arriba y los ejemplares del libro elegido abajo."""
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.interfaz_grafica.opciones import opciones_enum, opciones_sedes
from biblioteca.modelos.enumeraciones import TipoMaterial
from biblioteca.servicios import ServicioCatalogo, ServicioDisponibilidad


class PestaniaCatalogo(ttk.Frame):
    COLUMNAS_LIBROS = ("Id", "ISBN", "Título", "Autor", "Editorial", "Año", "Tipo")
    COLUMNAS_EJEMPLARES = ("Id", "Código", "Sede propietaria", "Estado", "Estado físico")

    def __init__(self, padre):
        super().__init__(padre, padding=10)
        self.servicio = ServicioCatalogo()

        libros = ttk.LabelFrame(self, text="Libros", padding=8)
        libros.pack(fill="both", expand=True)
        c.barra_de_botones(libros, [
            ("Nuevo libro", self.nuevo_libro),
            ("Modificar libro", self.modificar_libro),
            ("Ver disponibilidad", self.ver_disponibilidad),
        ]).pack(fill="x")
        self.tabla_libros = c.Tabla(libros, self.COLUMNAS_LIBROS, alto=9,
                                    anchos={"Id": 50, "Título": 280, "Autor": 200, "Año": 60})
        self.tabla_libros.pack(fill="both", expand=True, pady=(8, 0))
        self.tabla_libros.al_seleccionar(self.actualizar_ejemplares)

        ejemplares = ttk.LabelFrame(self, text="Ejemplares del libro seleccionado", padding=8)
        ejemplares.pack(fill="both", expand=True, pady=(10, 0))
        c.barra_de_botones(ejemplares, [
            ("Nuevo ejemplar", self.nuevo_ejemplar),
            ("Finalizar reparación", self.finalizar_reparacion),
            ("Dar de baja ejemplar", self.dar_de_baja_ejemplar),
        ]).pack(fill="x")
        self.tabla_ejemplares = c.Tabla(ejemplares, self.COLUMNAS_EJEMPLARES, alto=6, anchos={"Id": 50, "Sede propietaria": 200})
        self.tabla_ejemplares.pack(fill="both", expand=True, pady=(8, 0))

    def actualizar(self):
        self.tabla_libros.cargar([
            (l.id, l.isbn, l.titulo, l.autor, l.editorial, l.anio_publicacion, l.tipo_material.value)
            for l in self.servicio.listar_libros()
        ])
        self.actualizar_ejemplares()

    def actualizar_ejemplares(self):
        id_libro = self.tabla_libros.id_seleccionado()
        ejemplares = self.servicio.listar_ejemplares(id_libro=id_libro) if id_libro else []
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
        datos = c.pedir_datos(self, f"Modificar {libro.titulo}", self._campos_libro(libro))
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
            self.actualizar_ejemplares()

    def finalizar_reparacion(self):
        id_ejemplar = c.id_seleccionado_o_aviso(self.tabla_ejemplares, self, "un ejemplar")
        if id_ejemplar is not None and c.ejecutar(
            lambda: self.servicio.finalizar_reparacion(id_ejemplar), self, "El ejemplar vuelve a circular."
        ):
            self.actualizar_ejemplares()

    def dar_de_baja_ejemplar(self):
        id_ejemplar = c.id_seleccionado_o_aviso(self.tabla_ejemplares, self, "un ejemplar")
        if id_ejemplar is not None and c.confirmar("¿Confirma la baja del ejemplar seleccionado?", self):
            if c.ejecutar(lambda: self.servicio.dar_de_baja_ejemplar(id_ejemplar), self, "Ejemplar dado de baja."):
                self.actualizar_ejemplares()
