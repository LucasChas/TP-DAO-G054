"""E2E de reservas (proceso obligatorio 7). Escenarios en e2e/features/reservas.feature."""
from datetime import timedelta

from biblioteca.modelos.enumeraciones import EstadoFisico
from biblioteca.servicios import ServicioDevoluciones, ServicioPrestamos, ServicioReservas, ServicioSedes
from e2e.conftest import HOY, hace
from e2e.driver import Formulario, Mensaje


def _rayuela_de_centro_prestado(red, fecha=None):
    """El único ejemplar de Rayuela de la Sede Centro (CEN-0001) lo tiene Juan."""
    return ServicioPrestamos().registrar_prestamo_local(red.juan.id, red.ej["CEN-0001"].id, red.centro.id, fecha=fecha)


def test_cp19_reserva_asignacion_por_devolucion_y_retiro_del_titular(gui, red):
    prestamo = _rayuela_de_centro_prestado(red)
    pestania = gui.ir_a("Reservas")
    mensajes = gui.clic("Reservar", Formulario({"Socio": "Pérez, Ana", "Libro": "Rayuela", "Sede de retiro": "Sede Centro"},
                                               captura="01_formulario_reserva"), Mensaje(captura="02_confirmacion"))
    assert mensajes == [("Listo", "Reserva registrada. Los ejemplares se asignan por orden de llegada.")]
    assert gui.filas(pestania.tabla)[0]["Estado"] == "Pendiente"

    gui.ir_a("Devoluciones y multas")
    gui.clic("Registrar devolución", Formulario({"Préstamo": f"{prestamo.id} - Gómez, Juan", "Estado físico": "Bueno"}), Mensaje())
    pestania = gui.ir_a("Reservas")
    fila = gui.filas(pestania.tabla)[0]
    gui.capturar("03_ejemplar_apartado")
    limite = (HOY + timedelta(days=3)).strftime("%d/%m/%Y")
    assert (fila["Estado"], fila["Ejemplar apartado"], fila["Retirar hasta"]) == ("Disponible para retiro", "CEN-0001", limite)

    gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo local", Formulario({"Socio": "Pérez, Ana", "Sede": "Sede Centro",
                                                       "Ejemplar de la sede": "CEN-0001"},
                                                      captura="04_retiro_del_titular"), Mensaje())
    assert mensajes[0][1].startswith("Préstamo registrado.")
    pestania = gui.ir_a("Reservas")
    pestania.solo_activas.set(False)
    pestania.actualizar()
    gui.capturar("05_reserva_cumplida")
    assert gui.filas(pestania.tabla)[0]["Estado"] == "Cumplida"


def test_cp20_cancelar_reserva(gui, red):
    _rayuela_de_centro_prestado(red)
    ServicioReservas().reservar(red.ana.id, red.rayuela.id, red.centro.id)
    pestania = gui.ir_a("Reservas")
    gui.seleccionar(pestania.tabla, "Socio", "Pérez, Ana")
    gui.clic("Cancelar reserva", Mensaje(contiene="Reserva cancelada.", captura="01_cancelada"))
    assert gui.filas(pestania.tabla) == []


def test_cp21_procesar_reservas_no_retiradas(gui, red):
    prestamo = _rayuela_de_centro_prestado(red, fecha=hace(10))
    ServicioReservas().reservar(red.ana.id, red.rayuela.id, red.centro.id, fecha=hace(8))
    ServicioDevoluciones().registrar_devolucion(prestamo.id, EstadoFisico.BUENO, fecha=hace(6))
    pestania = gui.ir_a("Reservas")
    gui.capturar("01_plazo_de_retiro_vencido")
    mensajes = gui.clic("Procesar reservas no retiradas", Mensaje(captura="02_resultado"))
    assert mensajes == [("Listo", "Reservas vencidas por no retirar: 1.")]
    pestania.solo_activas.set(False)
    pestania.actualizar()
    assert gui.filas(pestania.tabla)[0]["Estado"] == "Vencida"


def test_cn33_reservar_cuando_hay_ejemplares_disponibles(gui, red):
    gui.ir_a("Reservas")
    mensajes = gui.clic("Reservar", Formulario({"Socio": "Pérez, Ana", "Libro": "Rayuela", "Sede de retiro": "Sede Centro"}),
                        Mensaje(titulo="Operación rechazada", captura="01_hay_disponibles"))
    assert mensajes == [("Operación rechazada", "Hay ejemplares de 'Rayuela' disponibles en 'Sede Centro'. Solicite el préstamo.")]


def test_cn34_reservar_en_una_sede_sin_ejemplares_del_libro(gui, red):
    gui.ir_a("Reservas")
    mensajes = gui.clic("Reservar", Formulario({"Socio": "Pérez, Ana", "Libro": "Diccionario", "Sede de retiro": "Sede Norte"}),
                        Mensaje(titulo="Operación rechazada", captura="01_sin_ejemplares"))
    assert mensajes == [("Operación rechazada", "La sede 'Sede Norte' no tiene ejemplares de 'Diccionario de la lengua'. "
                                                "Solicite un préstamo interbibliotecario.")]


def test_cn35_reserva_duplicada(gui, red):
    _rayuela_de_centro_prestado(red)
    ServicioReservas().reservar(red.ana.id, red.rayuela.id, red.centro.id)
    gui.ir_a("Reservas")
    mensajes = gui.clic("Reservar", Formulario({"Socio": "Pérez, Ana", "Libro": "Rayuela", "Sede de retiro": "Sede Centro"}),
                        Mensaje(titulo="Operación rechazada", captura="01_duplicada"))
    assert mensajes == [("Operación rechazada", "El socio ya tiene una reserva activa de 'Rayuela'.")]


def test_cn36_reserva_de_socio_inhabilitado(gui, red):
    _rayuela_de_centro_prestado(red)
    gui.ir_a("Reservas")
    mensajes = gui.clic("Reservar", Formulario({"Socio": "Torres, Lía", "Libro": "Rayuela", "Sede de retiro": "Sede Centro"}),
                        Mensaje(titulo="Operación rechazada", captura="01_inhabilitado"))
    assert mensajes == [("Operación rechazada", "El socio Torres, Lía está inhabilitado (Deuda de cuota social).")]


def test_cn37_reserva_en_sede_dada_de_baja(gui, red):
    ServicioSedes().dar_de_baja_sede(red.norte.id)
    gui.ir_a("Reservas")
    mensajes = gui.clic("Reservar", Formulario({"Socio": "Pérez, Ana", "Libro": "Rayuela", "Sede de retiro": "Sede Norte"}),
                        Mensaje(titulo="Operación rechazada", captura="01_sede_de_baja"))
    assert mensajes == [("Operación rechazada", "La sede de retiro 'Sede Norte' está dada de baja.")]


def test_cn38_prestar_un_ejemplar_apartado_para_otro_socio(gui, red):
    prestamo = _rayuela_de_centro_prestado(red)
    ServicioReservas().reservar(red.ana.id, red.rayuela.id, red.centro.id)
    ServicioDevoluciones().registrar_devolucion(prestamo.id, EstadoFisico.BUENO)
    gui.ir_a("Préstamos")
    mensajes = gui.clic("Préstamo local", Formulario({"Socio": "Gómez, Juan", "Sede": "Sede Centro", "Ejemplar de la sede": "CEN-0001"}),
                        Mensaje(titulo="Operación rechazada", captura="01_apartado_para_otro"))
    assert mensajes == [("Operación rechazada", "El ejemplar CEN-0001 está apartado para la reserva de otro socio.")]


def test_cp34_registrar_retiro_desde_la_pestania_de_reservas(gui, red):
    prestamo = _rayuela_de_centro_prestado(red)
    ServicioReservas().reservar(red.ana.id, red.rayuela.id, red.centro.id)
    ServicioDevoluciones().registrar_devolucion(prestamo.id, EstadoFisico.BUENO)
    pestania = gui.ir_a("Reservas")
    gui.seleccionar(pestania.tabla, "Socio", "Pérez, Ana")
    gui.capturar("01_reserva_disponible_para_retiro")
    mensajes = gui.clic("Registrar retiro", Mensaje(captura="02_retiro_registrado"))
    vence = (HOY + timedelta(days=14)).strftime("%d/%m/%Y")
    assert mensajes == [("Listo", f"Retiro registrado: se prestó CEN-0001 a Pérez, Ana. Vence el {vence}.")]
    pestania.solo_activas.set(False)
    pestania.actualizar()
    assert next(f for f in gui.filas(pestania.tabla) if f["Socio"] == "Pérez, Ana")["Estado"] == "Cumplida"
    prestamos = gui.ir_a("Préstamos")
    fila = next(f for f in gui.filas(prestamos.tabla) if f["Socio"] == "Pérez, Ana")
    gui.capturar("03_prestamo_del_retiro")
    assert (fila["Ejemplar"], fila["Tipo"], fila["Estado"]) == ("CEN-0001", "Local", "Activo")


def test_cn48_registrar_retiro_de_una_reserva_pendiente(gui, red):
    _rayuela_de_centro_prestado(red)
    ServicioReservas().reservar(red.ana.id, red.rayuela.id, red.centro.id)
    pestania = gui.ir_a("Reservas")
    gui.seleccionar(pestania.tabla, "Socio", "Pérez, Ana")
    mensajes = gui.clic("Registrar retiro", Mensaje(titulo="Operación rechazada", captura="01_reserva_pendiente"))
    assert mensajes == [("Operación rechazada",
                         "La reserva está pendiente: solo se retiran reservas disponibles para retiro.")]
