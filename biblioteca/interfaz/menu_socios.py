"""Menú de administración de socios."""
from biblioteca.interfaz.consola import ejecutar_menu, mostrar_exito, mostrar_tabla, pedir_entero, pedir_texto
from biblioteca.servicios import ServicioSocios

servicio = ServicioSocios()

COLUMNAS = ["Id", "DNI", "Apellido y nombre", "Email", "Teléfono", "Estado", "Motivo"]


def _fila(socio):
    return (
        socio.id, socio.dni, socio.nombre_completo, socio.email, socio.telefono,
        socio.estado.value, socio.motivo_inhabilitacion,
    )


def listar_socios():
    mostrar_tabla("Socios", COLUMNAS, [_fila(s) for s in servicio.listar_socios()])


def buscar_socio():
    socio = servicio.buscar_por_dni(pedir_texto("DNI", obligatorio=True))
    mostrar_tabla("Socio encontrado", COLUMNAS, [_fila(socio)])


def registrar_socio():
    socio = servicio.registrar_socio(
        dni=pedir_texto("DNI", obligatorio=True),
        nombre=pedir_texto("Nombre", obligatorio=True),
        apellido=pedir_texto("Apellido", obligatorio=True),
        email=pedir_texto("Email (opcional)"),
        telefono=pedir_texto("Teléfono (opcional)"),
    )
    mostrar_exito(f"Socio {socio.nombre_completo} registrado con id {socio.id}.")


def modificar_socio():
    socio = servicio.obtener_socio(pedir_entero("Id del socio a modificar"))
    print("Deje vacío un dato para no modificarlo.")
    servicio.modificar_socio(
        socio.id,
        nombre=pedir_texto(f"Nombre [{socio.nombre}]"),
        apellido=pedir_texto(f"Apellido [{socio.apellido}]"),
        email=pedir_texto(f"Email [{socio.email or '-'}]"),
        telefono=pedir_texto(f"Teléfono [{socio.telefono or '-'}]"),
    )
    mostrar_exito("Socio modificado.")


def inhabilitar_socio():
    id_socio = pedir_entero("Id del socio a inhabilitar")
    motivo = pedir_texto("Motivo", obligatorio=True)
    socio = servicio.inhabilitar_socio(id_socio, motivo)
    mostrar_exito(f"El socio {socio.nombre_completo} quedó inhabilitado.")


def habilitar_socio():
    socio = servicio.habilitar_socio(pedir_entero("Id del socio a habilitar"))
    mostrar_exito(f"El socio {socio.nombre_completo} quedó habilitado.")


def menu_socios():
    ejecutar_menu("Administración de socios", [
        ("Listar socios", listar_socios),
        ("Buscar socio por DNI", buscar_socio),
        ("Registrar socio", registrar_socio),
        ("Modificar socio", modificar_socio),
        ("Inhabilitar socio", inhabilitar_socio),
        ("Habilitar socio", habilitar_socio),
    ])
