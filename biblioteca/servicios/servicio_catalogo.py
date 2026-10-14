"""Casos de uso de administración del catálogo: libros y ejemplares."""
import re
from datetime import date

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import EjemplarDAO, LibroDAO, SedeDAO
from biblioteca.excepciones import (
    DatoInvalido,
    EntidadDuplicada,
    EntidadNoEncontrada,
    OperacionNoPermitida,
    SedeDadaDeBaja,
)
from biblioteca.modelos import Ejemplar, Libro
from biblioteca.modelos.enumeraciones import EstadoEjemplar, EstadoFisico, TipoMaterial
from biblioteca.servicios.asignacion_reservas import liberar_ejemplar
from biblioteca.servicios.servicio_sedes import obtener_sede_o_error
from biblioteca.servicios.validaciones import texto_obligatorio, texto_opcional


def normalizar_isbn(isbn):
    """Quita guiones y espacios y controla que sea un ISBN-10 o ISBN-13."""
    limpio = re.sub(r"[-\s]", "", isbn or "").upper()
    if not re.fullmatch(r"\d{9}[\dX]|\d{13}", limpio):
        raise DatoInvalido(f"El ISBN '{isbn}' no es válido: debe tener 10 o 13 dígitos.")
    return limpio


def validar_anio(anio_publicacion):
    if anio_publicacion is None:
        return None
    if not 1450 <= anio_publicacion <= date.today().year:
        raise DatoInvalido(f"El año de publicación {anio_publicacion} no es válido.")
    return anio_publicacion


def obtener_libro_o_error(dao, id_libro):
    libro = dao.obtener_por_id(id_libro)
    if libro is None:
        raise EntidadNoEncontrada(f"No existe el libro con id {id_libro}.")
    return libro


def obtener_ejemplar_o_error(dao, id_ejemplar):
    ejemplar = dao.obtener_por_id(id_ejemplar)
    if ejemplar is None:
        raise EntidadNoEncontrada(f"No existe el ejemplar con id {id_ejemplar}.")
    return ejemplar


class ServicioCatalogo:
    def registrar_libro(self, isbn, titulo, autor, editorial=None, anio_publicacion=None, tipo_material=TipoMaterial.LIBRO):
        """Agrega una obra al catálogo. El ISBN no puede repetirse."""
        isbn = normalizar_isbn(isbn)
        titulo = texto_obligatorio(titulo, "título")
        autor = texto_obligatorio(autor, "autor")
        anio_publicacion = validar_anio(anio_publicacion)
        with obtener_sesion() as sesion:
            dao = LibroDAO(sesion)
            if dao.obtener_por_isbn(isbn) is not None:
                raise EntidadDuplicada(f"Ya existe un libro con ISBN {isbn}.")
            libro = Libro(
                isbn=isbn,
                titulo=titulo,
                autor=autor,
                editorial=texto_opcional(editorial),
                anio_publicacion=anio_publicacion,
                tipo_material=tipo_material,
            )
            dao.crear(libro)
        return libro

    def modificar_libro(self, id_libro, titulo=None, autor=None, editorial=None, anio_publicacion=None, tipo_material=None):
        """Modifica los datos indicados. El ISBN no se modifica porque identifica la obra."""
        with obtener_sesion() as sesion:
            dao = LibroDAO(sesion)
            libro = obtener_libro_o_error(dao, id_libro)
            if titulo is not None:
                libro.titulo = texto_obligatorio(titulo, "título")
            if autor is not None:
                libro.autor = texto_obligatorio(autor, "autor")
            if editorial is not None:
                libro.editorial = texto_opcional(editorial)
            if anio_publicacion is not None:
                libro.anio_publicacion = validar_anio(anio_publicacion)
            if tipo_material is not None:
                libro.tipo_material = tipo_material
            dao.actualizar(libro)
        return libro

    def registrar_ejemplar(self, id_libro, id_sede, codigo_inventario):
        """Agrega un ejemplar físico a una sede activa. El código de inventario no puede repetirse."""
        codigo_inventario = texto_obligatorio(codigo_inventario, "código de inventario").upper()
        with obtener_sesion() as sesion:
            libro = obtener_libro_o_error(LibroDAO(sesion), id_libro)
            sede = obtener_sede_o_error(SedeDAO(sesion), id_sede)
            if not sede.esta_activa:
                raise SedeDadaDeBaja(f"No se pueden incorporar ejemplares a la sede '{sede.nombre}' porque está dada de baja.")
            dao = EjemplarDAO(sesion)
            if dao.obtener_por_codigo(codigo_inventario) is not None:
                raise EntidadDuplicada(f"Ya existe un ejemplar con código {codigo_inventario}.")
            ejemplar = Ejemplar(codigo_inventario=codigo_inventario, libro=libro, sede=sede)
            dao.crear(ejemplar)
        return ejemplar

    def dar_de_baja_ejemplar(self, id_ejemplar):
        """Retira un ejemplar de circulación. Solo se permite si está en su sede y sin uso
        (disponible o en reparación, por ejemplo cuando el daño no tiene arreglo)."""
        with obtener_sesion() as sesion:
            dao = EjemplarDAO(sesion)
            ejemplar = obtener_ejemplar_o_error(dao, id_ejemplar)
            if ejemplar.estado not in (EstadoEjemplar.DISPONIBLE, EstadoEjemplar.EN_REPARACION):
                raise OperacionNoPermitida(
                    f"El ejemplar {ejemplar.codigo_inventario} está {ejemplar.estado.value.lower()} "
                    "y no se puede dar de baja."
                )
            ejemplar.estado = EstadoEjemplar.BAJA
            dao.actualizar(ejemplar)
        return ejemplar

    def finalizar_reparacion(self, id_ejemplar, fecha=None):
        """El ejemplar reparado vuelve a prestarse; si había reservas, pasa a la más antigua."""
        with obtener_sesion() as sesion:
            ejemplar = obtener_ejemplar_o_error(EjemplarDAO(sesion), id_ejemplar)
            if ejemplar.estado != EstadoEjemplar.EN_REPARACION:
                raise OperacionNoPermitida(f"El ejemplar {ejemplar.codigo_inventario} no está en reparación.")
            ejemplar.estado_fisico = EstadoFisico.REGULAR
            liberar_ejemplar(sesion, ejemplar, fecha or date.today())
        return ejemplar

    def obtener_libro(self, id_libro):
        with obtener_sesion() as sesion:
            return obtener_libro_o_error(LibroDAO(sesion), id_libro)

    def listar_libros(self):
        with obtener_sesion() as sesion:
            return LibroDAO(sesion).listar()

    def buscar_libros(self, texto):
        texto = texto_obligatorio(texto, "texto de búsqueda")
        with obtener_sesion() as sesion:
            return LibroDAO(sesion).buscar(texto)

    def listar_ejemplares(self, id_libro=None, id_sede=None):
        with obtener_sesion() as sesion:
            return EjemplarDAO(sesion).listar(id_libro=id_libro, id_sede=id_sede)
