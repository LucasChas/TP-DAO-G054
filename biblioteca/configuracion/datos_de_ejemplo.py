"""Datos de ejemplo para probar el sistema desde la consola."""
from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.modelos import Sede
from biblioteca.modelos.enumeraciones import TipoMaterial
from biblioteca.servicios import ServicioCatalogo, ServicioSedes, ServicioSocios


def cargar_datos_de_ejemplo():
    """Carga sedes, socios, libros y ejemplares si la base está vacía.

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
    socios.registrar_socio("30111222", "Ana", "Pérez", "ana.perez@correo.com", "351-5000001")
    socios.registrar_socio("28999888", "Juan", "Gómez", "juan.gomez@correo.com")
    socios.registrar_socio("35444555", "María", "López", "maria.lopez@correo.com")
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
    for libro, sede, codigo in ejemplares:
        catalogo.registrar_ejemplar(libro.id, sede.id, codigo)
    return True
