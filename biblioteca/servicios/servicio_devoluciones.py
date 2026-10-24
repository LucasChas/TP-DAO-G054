"""Casos de uso de devoluciones y multas."""
from datetime import date, datetime

from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.dao import DevolucionDAO, PrestamoDAO
from biblioteca.excepciones import DatoInvalido, EntidadNoEncontrada, OperacionNoPermitida
from biblioteca.modelos import Devolucion
from biblioteca.modelos.enumeraciones import EstadoEjemplar, EstadoFisico, EstadoPrestamo, SentidoRemito
from biblioteca.patrones.estrategias_multa import CalculadoraDeMultas, estrategia_por_defecto
from biblioteca.servicios.asignacion_reservas import liberar_ejemplar
from biblioteca.servicios.servicio_prestamos import obtener_prestamo_o_error
from biblioteca.servicios.servicio_remitos import generar_remito


def obtener_devolucion_o_error(dao, id_devolucion):
    devolucion = dao.obtener_por_id(id_devolucion)
    if devolucion is None:
        raise EntidadNoEncontrada(f"No existe la devolución con id {id_devolucion}.")
    return devolucion


class ServicioDevoluciones:
    def __init__(self, calculadora=None):
        """La calculadora de multas se puede recibir ya configurada; si no, usa la estrategia por defecto."""
        self.calculadora = calculadora or CalculadoraDeMultas(estrategia_por_defecto())

    def cambiar_estrategia_de_multa(self, estrategia):
        self.calculadora.cambiar_estrategia(estrategia)

    def registrar_devolucion(self, id_prestamo, estado_fisico, observaciones=None, fecha=None):
        """El socio devuelve el ejemplar en la sede donde lo retiró.

        Se registra el estado físico del material y se calcula la multa por atraso
        con la estrategia vigente, más el cargo por daño si el material se devuelve
        dañado. Después:
        - préstamo local: el ejemplar vuelve a circular (o queda en reparación si está dañado);
        - préstamo interbibliotecario: se genera el remito de retorno a su sede propietaria.
        """
        fecha = fecha or date.today()
        with obtener_sesion() as sesion:
            prestamo = obtener_prestamo_o_error(PrestamoDAO(sesion), id_prestamo)
            if prestamo.estado != EstadoPrestamo.ACTIVO:
                raise OperacionNoPermitida(
                    f"El préstamo está {prestamo.estado.value.lower()}: solo se devuelven préstamos activos."
                )
            if fecha < prestamo.fecha_entrega:
                raise DatoInvalido("La fecha de devolución no puede ser anterior a la entrega.")

            dias_atraso, monto = self.calculadora.calcular(prestamo, fecha)
            cargo_por_danio = self.calculadora.cargo_por_danio(prestamo.ejemplar.estado_fisico, estado_fisico)
            total = monto + cargo_por_danio
            devolucion = Devolucion(
                prestamo=prestamo,
                fecha=fecha,
                estado_fisico=estado_fisico,
                dias_atraso=dias_atraso,
                monto_multa=total,
                cargo_por_danio=cargo_por_danio,
                multa_pagada=total == 0,
                observaciones=(observaciones or "").strip() or None,
            )
            DevolucionDAO(sesion).crear(devolucion)
            prestamo.estado = EstadoPrestamo.DEVUELTO

            ejemplar = prestamo.ejemplar
            ejemplar.estado_fisico = estado_fisico
            if prestamo.es_interbibliotecario:
                # Sigue fuera de su sede hasta que el remito de retorno lo reintegre.
                ejemplar.estado = EstadoEjemplar.EN_TRANSITO
                generar_remito(
                    sesion, prestamo, SentidoRemito.RETORNO, datetime.combine(fecha, datetime.now().time()),
                    "Retorno por devolución del socio",
                )
            elif estado_fisico == EstadoFisico.DANIADO:
                ejemplar.estado = EstadoEjemplar.EN_REPARACION
            else:
                liberar_ejemplar(sesion, ejemplar, fecha)
        return devolucion

    def registrar_pago_de_multa(self, id_devolucion):
        with obtener_sesion() as sesion:
            dao = DevolucionDAO(sesion)
            devolucion = obtener_devolucion_o_error(dao, id_devolucion)
            if not devolucion.tiene_multa_impaga:
                raise OperacionNoPermitida("Esa devolución no tiene una multa pendiente de pago.")
            devolucion.multa_pagada = True
            dao.actualizar(devolucion)
        return devolucion

    def listar_devoluciones(self):
        with obtener_sesion() as sesion:
            return DevolucionDAO(sesion).listar()

    def listar_multas_impagas(self, id_socio=None):
        with obtener_sesion() as sesion:
            return DevolucionDAO(sesion).listar_multas_impagas(id_socio)
