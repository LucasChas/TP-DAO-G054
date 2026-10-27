"""Evidencia del defecto D1: el orden del trayecto de un remito depende de la hora del reloj.

Ejecutar desde la raíz del repositorio: PYTHONPATH=. python docs/auditoria/evidencia_hora_del_reloj.py
"""
import datetime as dt, sys
from biblioteca.configuracion.base_de_datos import configurar_base_de_datos, crear_tablas
import biblioteca.servicios.servicio_prestamos as sp, biblioteca.servicios.servicio_devoluciones as sd
from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo
from biblioteca.servicios import ServicioRemitos
for hora in (9, 12):
    class Fake(dt.datetime):
        @classmethod
        def now(cls, tz=None): return dt.datetime.combine(dt.date.today(), dt.time(hora, 0))
    sp.datetime = Fake; sd.datetime = Fake
    configurar_base_de_datos("sqlite:///:memory:"); crear_tablas(); cargar_datos_de_ejemplo()
    r = ServicioRemitos().listar_remitos()[0]
    movs = [(m.estado_nuevo, m.fecha_hora.strftime("%d/%m %H:%M")) for m in r.movimientos]
    ordenado = [m.fecha_hora for m in r.movimientos] == sorted(m.fecha_hora for m in r.movimientos)
    print(f"Reloj {hora:02d}:00 -> {r.numero}: {movs} -> orden cronológico: {ordenado}")
