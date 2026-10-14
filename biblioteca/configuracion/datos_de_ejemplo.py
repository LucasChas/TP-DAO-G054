"""Datos de ejemplo para probar el sistema desde la consola."""
from datetime import date, datetime, timedelta

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.modelos import Sede
from biblioteca.modelos.enumeraciones import EstadoFisico, TipoMaterial
from biblioteca.servicios import (
    ServicioCatalogo,
    ServicioDevoluciones,
    ServicioPrestamos,
    ServicioRemitos,
    ServicioReservas,
    ServicioSedes,
    ServicioSocios,
)


def cargar_datos_de_ejemplo():
    """Carga sedes, socios, libros, ejemplares y un historial de operaciones si la base está vacía.

    Devuelve True si cargó los datos y False si ya había sedes registradas.
    """
    with obtener_sesion() as sesion:
        if sesion.query(Sede).count() > 0:
            return False

    sedes = ServicioSedes()
    centro = sedes.registrar_sede(
        "Biblioteca Central", "Av. Colón 100, Córdoba", "351-4000100", "central@bibliotecas.org", "Lun a Vie 8 a 20"
    )
    norte = sedes.registrar_sede(
        "Sede Norte", "Av. Monseñor Pablo Cabrera 3000, Córdoba", "351-4000200", "norte@bibliotecas.org", "Lun a Vie 9 a 18"
    )
    sur = sedes.registrar_sede(
        "Sede Sur", "Av. Vélez Sarsfield 2500, Córdoba", "351-4000300", "sur@bibliotecas.org", "Lun a Sáb 9 a 13"
    )

    socios = ServicioSocios()
    ana = socios.registrar_socio("30111222", "Ana", "Pérez", "ana.perez@correo.com", "351-5000001")
    juan = socios.registrar_socio("28999888", "Juan", "Gómez", "juan.gomez@correo.com")
    maria = socios.registrar_socio("35444555", "María", "López", "maria.lopez@correo.com")
    rodriguez = socios.registrar_socio("32777666", "Carlos", "Rodríguez")
    socios.inhabilitar_socio(rodriguez.id, "Devolvió material dañado sin reponerlo")

    catalogo = ServicioCatalogo()
    libros = [
        ("9789500700011", "Rayuela", "Julio Cortázar", "Sudamericana", 1963, TipoMaterial.LIBRO),
        ("9789875666474", "Ficciones", "Jorge Luis Borges", "Debolsillo", 1944, TipoMaterial.LIBRO),
        ("9788437604947", "Cien años de soledad", "Gabriel García Márquez", "Cátedra", 1967, TipoMaterial.LIBRO),
        ("9789870404637", "El Aleph", "Jorge Luis Borges", "Emecé", 1949, TipoMaterial.LIBRO),
        ("9789502801334", "Diccionario de la lengua española", "Real Academia Española", "Espasa", 2014, TipoMaterial.CONSULTA),
        ("9771514298006", "Revista Ñ - Edición aniversario", "Clarín", "AGEA", 2023, TipoMaterial.REVISTA),
    ]
    registrados = [catalogo.registrar_libro(*datos) for datos in libros]

    rayuela, ficciones, cien_anios, aleph, diccionario, revista = registrados
    ejemplares = [
        (rayuela, centro, "CEN-0001"), (rayuela, centro, "CEN-0002"), (rayuela, norte, "NOR-0001"),
        (ficciones, centro, "CEN-0003"), (ficciones, sur, "SUR-0001"),
        (cien_anios, norte, "NOR-0002"), (cien_anios, sur, "SUR-0002"),
        (aleph, sur, "SUR-0003"),
        (diccionario, centro, "CEN-0004"),
        (revista, norte, "NOR-0003"),
    ]
    codigos = {}
    for libro, sede, codigo in ejemplares:
        codigos[codigo] = catalogo.registrar_ejemplar(libro.id, sede.id, codigo)

    _cargar_historial(centro, norte, sur, ana, juan, maria, rayuela, codigos)
    return True


def _momento(dias_atras, hora):
    """Fecha y hora relativa a hoy, para que el historial siempre quede reciente."""
    return datetime.combine(date.today() - timedelta(days=dias_atras), datetime.min.time()) + timedelta(hours=hora)


def _cargar_historial(centro, norte, sur, ana, juan, maria, rayuela, ejemplares):
    """Operaciones pasadas para que los reportes tengan datos. Se cargan con los
    servicios, así que cumplen todas las validaciones del sistema."""
    prestamos, remitos = ServicioPrestamos(), ServicioRemitos()
    hoy = date.today()

    def remitos_de(prestamo):
        return remitos.listar_remitos_de_prestamo(prestamo.id)

    def enviar(remito, dias_atras, punto_de_control=None):
        remitos.empaquetar(remito.id, fecha_hora=_momento(dias_atras, 8))
        remitos.despachar(remito.id, fecha_hora=_momento(dias_atras, 9))
        if punto_de_control:
            remitos.registrar_punto_de_control(remito.id, punto_de_control, fecha_hora=_momento(dias_atras, 13))

    # Ana retiró en la Central un Rayuela de la Sede Norte y está vencida hace 10 días.
    p_ana = prestamos.solicitar_prestamo_interbibliotecario(
        ana.id, ejemplares["NOR-0001"].id, norte.id, centro.id, fecha=hoy - timedelta(days=25)
    )
    enviar(remitos_de(p_ana)[0], 25, "Centro de distribución Alta Córdoba")
    remitos.recibir(remitos_de(p_ana)[0].id, EstadoFisico.BUENO, fecha_hora=_momento(24, 10))
    prestamos.entregar_prestamo(p_ana.id, fecha=hoy - timedelta(days=24))

    # Juan pidió El Aleph a la Sede Sur, llegó dañado y volvió a su sede, que lo tiene en reparación.
    p_aleph = prestamos.solicitar_prestamo_interbibliotecario(
        juan.id, ejemplares["SUR-0003"].id, sur.id, centro.id, fecha=hoy - timedelta(days=15)
    )
    enviar(remitos_de(p_aleph)[0], 15)
    remitos.recibir(remitos_de(p_aleph)[0].id, EstadoFisico.DANIADO, "Lomo despegado", fecha_hora=_momento(14, 11))
    retorno = remitos_de(p_aleph)[1]
    enviar(retorno, 13)
    remitos.recibir(retorno.id, EstadoFisico.DANIADO, fecha_hora=_momento(12, 16))

    # Juan devolvió con 2 días de atraso un préstamo local de Ficciones y no pagó la multa.
    p_ficciones = prestamos.registrar_prestamo_local(
        juan.id, ejemplares["CEN-0003"].id, centro.id, fecha=hoy - timedelta(days=20)
    )
    ServicioDevoluciones().registrar_devolucion(p_ficciones.id, EstadoFisico.REGULAR, fecha=hoy - timedelta(days=4))

    # María pidió Cien años de soledad de la Sede Sur para retirar en la Norte: está en viaje.
    p_maria = prestamos.solicitar_prestamo_interbibliotecario(
        maria.id, ejemplares["SUR-0002"].id, sur.id, norte.id, fecha=hoy - timedelta(days=2)
    )
    enviar(remitos_de(p_maria)[0], 1, "Terminal de ómnibus")

    # María también espera Rayuela en la Sede Norte, cuyo único ejemplar lo tiene Ana.
    ServicioReservas().reservar(maria.id, rayuela.id, norte.id, fecha=hoy - timedelta(days=3))
