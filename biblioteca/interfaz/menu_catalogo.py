"""Menú de administración del catálogo: libros y ejemplares."""
from biblioteca.interfaz.consola import (
    ejecutar_menu,
    mostrar_exito,
    mostrar_tabla,
    pedir_entero,
    pedir_opcion_enum,
    pedir_texto,
)
from biblioteca.interfaz.menu_sedes import listar_sedes
from biblioteca.modelos.enumeraciones import TipoMaterial
from biblioteca.servicios import ServicioCatalogo

servicio = ServicioCatalogo()

COLUMNAS_LIBROS = ["Id", "ISBN", "Título", "Autor", "Editorial", "Año", "Tipo"]


def _filas_libros(libros):
    return [
        (l.id, l.isbn, l.titulo, l.autor, l.editorial, l.anio_publicacion, l.tipo_material.value)
        for l in libros
    ]


def listar_libros():
    mostrar_tabla("Catálogo", COLUMNAS_LIBROS, _filas_libros(servicio.listar_libros()))


def buscar_libros():
    texto = pedir_texto("Texto a buscar en título o autor", obligatorio=True)
    mostrar_tabla(f"Resultados para '{texto}'", COLUMNAS_LIBROS, _filas_libros(servicio.buscar_libros(texto)))


def registrar_libro():
    libro = servicio.registrar_libro(
        isbn=pedir_texto("ISBN", obligatorio=True),
        titulo=pedir_texto("Título", obligatorio=True),
        autor=pedir_texto("Autor", obligatorio=True),
        editorial=pedir_texto("Editorial (opcional)"),
        anio_publicacion=pedir_entero("Año de publicación (opcional)", obligatorio=False),
        tipo_material=pedir_opcion_enum("Tipo de material", TipoMaterial),
    )
    mostrar_exito(f"Libro '{libro.titulo}' registrado con id {libro.id}.")


def modificar_libro():
    libro = servicio.obtener_libro(pedir_entero("Id del libro a modificar"))
    print("Deje vacío un dato para no modificarlo.")
    servicio.modificar_libro(
        libro.id,
        titulo=pedir_texto(f"Título [{libro.titulo}]"),
        autor=pedir_texto(f"Autor [{libro.autor}]"),
        editorial=pedir_texto(f"Editorial [{libro.editorial or '-'}]"),
        anio_publicacion=pedir_entero(f"Año [{libro.anio_publicacion or '-'}]", obligatorio=False),
        tipo_material=pedir_opcion_enum(f"Tipo [{libro.tipo_material.value}]", TipoMaterial, obligatorio=False),
    )
    mostrar_exito("Libro modificado.")


def listar_ejemplares():
    listar_sedes()
    id_sede = pedir_entero("Id de sede (vacío para todas)", obligatorio=False)
    filas = [
        (e.id, e.codigo_inventario, e.libro.titulo, e.sede.nombre, e.estado.value, e.estado_fisico.value)
        for e in servicio.listar_ejemplares(id_sede=id_sede)
    ]
    mostrar_tabla("Ejemplares", ["Id", "Código", "Libro", "Sede", "Estado", "Estado físico"], filas)


def registrar_ejemplar():
    listar_libros()
    id_libro = pedir_entero("Id del libro")
    listar_sedes()
    id_sede = pedir_entero("Id de la sede propietaria")
    codigo = pedir_texto("Código de inventario", obligatorio=True)
    ejemplar = servicio.registrar_ejemplar(id_libro, id_sede, codigo)
    mostrar_exito(f"Ejemplar {ejemplar.codigo_inventario} registrado en '{ejemplar.sede.nombre}'.")


def dar_de_baja_ejemplar():
    ejemplar = servicio.dar_de_baja_ejemplar(pedir_entero("Id del ejemplar a dar de baja"))
    mostrar_exito(f"El ejemplar {ejemplar.codigo_inventario} fue dado de baja.")


def finalizar_reparacion():
    ejemplar = servicio.finalizar_reparacion(pedir_entero("Id del ejemplar reparado"))
    mostrar_exito(f"El ejemplar {ejemplar.codigo_inventario} vuelve a estar en circulación.")


def menu_catalogo():
    ejecutar_menu("Administración del catálogo", [
        ("Listar libros", listar_libros),
        ("Buscar libros", buscar_libros),
        ("Registrar libro", registrar_libro),
        ("Modificar libro", modificar_libro),
        ("Listar ejemplares", listar_ejemplares),
        ("Registrar ejemplar", registrar_ejemplar),
        ("Finalizar reparación de ejemplar", finalizar_reparacion),
        ("Dar de baja ejemplar", dar_de_baja_ejemplar),
    ])
