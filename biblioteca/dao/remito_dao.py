"""Acceso a datos de remitos."""
from sqlalchemy import func, or_

from biblioteca.modelos import Remito
from biblioteca.modelos.enumeraciones import SentidoRemito

ESTADOS_FINALES = ("Anulado", "Cerrado")


class RemitoDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def crear(self, remito):
        self.sesion.add(remito)
        self.sesion.flush()
        return remito

    def actualizar(self, remito):
        self.sesion.flush()
        return remito

    def obtener_por_id(self, id_remito):
        return self.sesion.get(Remito, id_remito)

    def obtener_por_numero(self, numero):
        return self.sesion.query(Remito).filter_by(numero=numero).first()

    def siguiente_numero(self):
        """Número correlativo con el formato R-000001."""
        ultimo = self.sesion.query(func.max(Remito.id)).scalar() or 0
        return f"R-{ultimo + 1:06d}"

    def listar(self, nombres_estado=None):
        consulta = self.sesion.query(Remito)
        if nombres_estado:
            consulta = consulta.filter(Remito.nombre_estado.in_(nombres_estado))
        return consulta.order_by(Remito.id).all()

    def hay_retornos_en_curso(self, id_sede):
        """Indica si algún remito de retorno sin finalizar sale de la sede o va hacia ella."""
        return (
            self.sesion.query(Remito)
            .filter(
                Remito.sentido == SentidoRemito.RETORNO,
                Remito.nombre_estado.notin_(ESTADOS_FINALES),
                or_(Remito.sede_origen_id == id_sede, Remito.sede_destino_id == id_sede),
            )
            .count()
            > 0
        )

    def listar_por_prestamo(self, id_prestamo):
        return self.sesion.query(Remito).filter_by(prestamo_id=id_prestamo).order_by(Remito.id).all()
