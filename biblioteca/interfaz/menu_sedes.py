"""Menú de administración de sedes."""
from biblioteca.interfaz.consola import (
    confirmar,
    ejecutar_menu,
    mostrar_exito,
    mostrar_tabla,
    pedir_entero,
    pedir_texto,
)
from biblioteca.servicios import ServicioSedes

servicio = ServicioSedes()


def listar_sedes():
    filas = [
        (s.id, s.nombre, s.direccion, s.telefono, s.email, s.horario_atencion, s.estado.value)
        for s in servicio.listar_sedes()
    ]
    mostrar_tabla("Sedes de la red", ["Id", "Nombre", "Dirección", "Teléfono", "Email", "Horario", "Estado"], filas)


def registrar_sede():
    nombre = pedir_texto("Nombre", obligatorio=True)
    direccion = pedir_texto("Dirección", obligatorio=True)
    telefono = pedir_texto("Teléfono (opcional)")
    email = pedir_texto("Email (opcional)")
    horario = pedir_texto("Horario de atención (opcional)")
    sede = servicio.registrar_sede(nombre, direccion, telefono, email, horario)
    mostrar_exito(f"Sede '{sede.nombre}' registrada con id {sede.id}.")


def modificar_sede():
    listar_sedes()
    id_sede = pedir_entero("Id de la sede a modificar")
    sede = servicio.obtener_sede(id_sede)
    print("Deje vacío un dato para no modificarlo.")
    servicio.modificar_sede(
        id_sede,
        nombre=pedir_texto(f"Nombre [{sede.nombre}]"),
        direccion=pedir_texto(f"Dirección [{sede.direccion}]"),
        telefono=pedir_texto(f"Teléfono [{sede.telefono or '-'}]"),
        email=pedir_texto(f"Email [{sede.email or '-'}]"),
        horario_atencion=pedir_texto(f"Horario [{sede.horario_atencion or '-'}]"),
    )
    mostrar_exito("Sede modificada.")


def dar_de_baja_sede():
    listar_sedes()
    id_sede = pedir_entero("Id de la sede a dar de baja")
    sede = servicio.obtener_sede(id_sede)
    if confirmar(f"¿Confirma la baja de '{sede.nombre}'?"):
        servicio.dar_de_baja_sede(id_sede)
        mostrar_exito(f"La sede '{sede.nombre}' fue dada de baja.")


def reactivar_sede():
    listar_sedes()
    sede = servicio.reactivar_sede(pedir_entero("Id de la sede a reactivar"))
    mostrar_exito(f"La sede '{sede.nombre}' está activa nuevamente.")


def menu_sedes():
    ejecutar_menu("Administración de sedes", [
        ("Listar sedes", listar_sedes),
        ("Registrar sede", registrar_sede),
        ("Modificar sede", modificar_sede),
        ("Dar de baja sede", dar_de_baja_sede),
        ("Reactivar sede", reactivar_sede),
    ])
