"""Opciones para las listas desplegables de los formularios y textos de apoyo para los
mensajes, armados a partir de los servicios.

Se muestran también los registros que no cumplen las reglas (socios inhabilitados,
sedes dadas de baja, ejemplares no disponibles) para que sea el servicio el que
rechace la operación y explique el motivo.
"""
from biblioteca.modelos.enumeraciones import EstadoEjemplar
from biblioteca.servicios import ServicioCatalogo, ServicioRemitos, ServicioReservas, ServicioSedes, ServicioSocios


def opciones_socios():
    return [
        (f"{s.nombre_completo} - DNI {s.dni}" + ("" if s.esta_habilitado else " (inhabilitado)"), s.id)
        for s in ServicioSocios().listar_socios()
    ]


def opciones_sedes():
    return [(s.nombre + ("" if s.esta_activa else " (dada de baja)"), s.id) for s in ServicioSedes().listar_sedes()]


def opciones_libros():
    return [(f"{l.titulo} - {l.autor} (ISBN {l.isbn})", l.id) for l in ServicioCatalogo().listar_libros()]


def opciones_ejemplares(id_sede=None):
    """Ejemplares que no están dados de baja; con id_sede, solo los que pertenecen a esa sede."""
    return [
        (f"{e.codigo_inventario} - {e.libro.titulo} ({e.sede.nombre}, {e.estado.value.lower()})", e.id)
        for e in ServicioCatalogo().listar_ejemplares()
        if e.estado != EstadoEjemplar.BAJA and (id_sede is None or e.sede_id == id_sede)
    ]


def opciones_enum(tipo_enum):
    return [(valor.value, valor) for valor in tipo_enum]


def destino_del_ejemplar(ejemplar):
    """Qué pasó con un ejemplar que se liberó: disponible, apartado para una reserva o en reparación."""
    if ejemplar.estado == EstadoEjemplar.DISPONIBLE:
        return "volvió a estar disponible"
    if ejemplar.estado == EstadoEjemplar.RESERVADO:
        for reserva in ServicioReservas().listar_reservas(solo_activas=True):
            if reserva.ejemplar_id == ejemplar.id:
                return (f"quedó apartado para la reserva de {reserva.socio.nombre_completo}, "
                        "que tiene 3 días para retirarlo")
        return "quedó apartado para la reserva pendiente más antigua"
    if ejemplar.estado == EstadoEjemplar.EN_REPARACION:
        return "quedó en reparación"
    return f"quedó {ejemplar.estado.value.lower()}"


def numero_de_remito(id_prestamo, sentido):
    """Número del último remito del préstamo en ese sentido (ida o retorno), o None."""
    remitos = [r for r in ServicioRemitos().listar_remitos_de_prestamo(id_prestamo) if r.sentido == sentido]
    return remitos[-1].numero if remitos else None
