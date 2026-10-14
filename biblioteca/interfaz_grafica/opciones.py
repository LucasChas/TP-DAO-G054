"""Opciones para las listas desplegables de los formularios, armadas a partir de los servicios.

Se muestran también los registros que no cumplen las reglas (socios inhabilitados,
sedes dadas de baja, ejemplares no disponibles) para que sea el servicio el que
rechace la operación y explique el motivo.
"""
from biblioteca.modelos.enumeraciones import EstadoEjemplar
from biblioteca.servicios import ServicioCatalogo, ServicioSedes, ServicioSocios


def opciones_socios():
    return [
        (f"{s.nombre_completo} - DNI {s.dni}" + ("" if s.esta_habilitado else " (inhabilitado)"), s.id)
        for s in ServicioSocios().listar_socios()
    ]


def opciones_sedes():
    return [(s.nombre + ("" if s.esta_activa else " (dada de baja)"), s.id) for s in ServicioSedes().listar_sedes()]


def opciones_libros():
    return [(f"{l.titulo} - {l.autor} (ISBN {l.isbn})", l.id) for l in ServicioCatalogo().listar_libros()]


def opciones_ejemplares():
    return [
        (f"{e.codigo_inventario} - {e.libro.titulo} ({e.sede.nombre}, {e.estado.value.lower()})", e.id)
        for e in ServicioCatalogo().listar_ejemplares()
        if e.estado != EstadoEjemplar.BAJA
    ]


def opciones_enum(tipo_enum):
    return [(valor.value, valor) for valor in tipo_enum]
