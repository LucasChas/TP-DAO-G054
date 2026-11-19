"""Pestaña de reportes: se elige un reporte a la izquierda y se muestran sus tablas a la derecha."""
from datetime import datetime
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes as c
from biblioteca.reportes import (
    exportacion,
    libros_mas_solicitados,
    movimiento_entre_sedes,
    prestamos_activos_y_transito,
    prestamos_vencidos_y_multas,
    tasa_de_envios,
)


def _horas(horas):
    return "-" if horas is None else f"{horas:.1f} h"


def _porcentaje(valor):
    return "-" if valor is None else f"{valor:.1f} %"


class PestaniaReportes(ttk.Frame):
    def __init__(self, padre, servicio_devoluciones):
        super().__init__(padre, padding=12)
        self.servicio_devoluciones = servicio_devoluciones

        lateral = ttk.Frame(self, width=270)
        lateral.pack(side="left", fill="y", padx=(0, 14))
        ttk.Label(lateral, text="Reportes", style="Subtitulo.TLabel").pack(anchor="w", pady=(0, 6))
        self.reportes = [
            ("1. Préstamos activos y tránsito", self.reporte_activos),
            ("2. Vencidos y multas", self.reporte_vencidos),
            ("3. Libros más solicitados", self.reporte_mas_solicitados),
            ("4. Movimiento entre sedes", self.reporte_movimientos),
            ("5. Tasa de envíos e incidencias", self.reporte_tasa),
        ]
        self.botones_reportes = {}
        for texto, comando in self.reportes:
            boton = ttk.Button(lateral, text=texto, command=comando, width=32, style="Menu.TButton")
            boton.pack(fill="x", pady=2)
            self.botones_reportes[comando.__name__] = boton

        filtro = ttk.LabelFrame(lateral, text="Rango de fechas (reportes 3 y 4)", padding=8)
        filtro.pack(fill="x", pady=(14, 0))
        ttk.Label(filtro, text="Desde (dd/mm/aaaa)").pack(anchor="w")
        self.desde = ttk.Entry(filtro)
        self.desde.pack(fill="x")
        ttk.Label(filtro, text="Hasta (dd/mm/aaaa)").pack(anchor="w", pady=(6, 0))
        self.hasta = ttk.Entry(filtro)
        self.hasta.pack(fill="x")

        exportar = ttk.LabelFrame(lateral, text="Exportar el reporte mostrado", padding=8)
        exportar.pack(fill="x", pady=(14, 0))
        ttk.Label(filtro, text="Vacío = sin límite.", style="Suave.TLabel").pack(anchor="w", pady=(6, 0))
        ttk.Button(exportar, text="Exportar a PDF (con gráfico)", command=lambda: self.exportar("pdf"),
                   style=c.PRIMARIO).pack(fill="x", pady=2)
        ttk.Button(exportar, text="Exportar a CSV", command=lambda: self.exportar("csv")).pack(fill="x", pady=2)
        self.etiqueta_exportado = ttk.Label(exportar, text="", style="Suave.TLabel", wraplength=230)
        self.etiqueta_exportado.pack(anchor="w", pady=(6, 0))

        desplazable = c.MarcoDesplazable(self)
        desplazable.pack(side="left", fill="both", expand=True)
        self.desplazable = desplazable
        self.contenido = desplazable.interior
        self.titulo_actual = None
        self.clave_actual = None
        self.ultimo_archivo = None

    def actualizar(self):
        if self.titulo_actual is None:
            self.reporte_activos()

    def _resaltar(self, comando):
        for nombre, boton in self.botones_reportes.items():
            boton.configure(style="MenuElegido.TButton" if nombre == comando else "Menu.TButton")

    def _mostrar(self, titulo, secciones, pie=None, indicadores=None):
        """secciones es una lista de (subtítulo, columnas, filas); indicadores, una lista de (valor, texto)."""
        self.titulo_actual = titulo
        self.desplazable.limpiar()
        ttk.Label(self.contenido, text=titulo, style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(self.contenido, text=f"Generado el {datetime.now():%d/%m/%Y a las %H:%M}", style="Suave.TLabel").pack(anchor="w")
        if indicadores:
            fila = ttk.Frame(self.contenido)
            fila.pack(fill="x", pady=(10, 0))
            for valor, texto in indicadores:
                c.tarjeta(fila, valor, texto).pack(side="left", padx=(0, 10))
        for subtitulo, columnas, filas in secciones:
            marco = ttk.LabelFrame(self.contenido, text=subtitulo, padding=6)
            marco.pack(fill="both", expand=True, pady=(10, 0))
            if filas:
                tabla = c.Tabla(marco, columnas, alto=max(2, min(len(filas), 7)))
                tabla.pack(fill="both", expand=True)
                tabla.cargar(filas)
            else:
                ttk.Label(marco, text="No hay datos para mostrar.", style="Suave.TLabel").pack(anchor="w")
        if pie:
            ttk.Label(self.contenido, text=pie, style="Negrita.TLabel").pack(anchor="w", pady=(10, 0))

    def _rango(self):
        """Lee las fechas del filtro; si alguna es inválida avisa y devuelve None."""
        fechas = []
        for entrada in (self.desde, self.hasta):
            texto = entrada.get().strip()
            if not texto:
                fechas.append(None)
                continue
            try:
                fechas.append(datetime.strptime(texto, "%d/%m/%Y").date())
            except ValueError:
                c.avisar(f"'{texto}' no es una fecha válida (dd/mm/aaaa).", self)
                return None
        return fechas

    def reporte_activos(self):
        self.clave_actual = "activos"
        self._resaltar("reporte_activos")
        reporte = prestamos_activos_y_transito.generar()
        self._mostrar("Préstamos activos y material en tránsito", [
            ("Préstamos en curso",
             ("Id", "Socio", "Libro", "Ejemplar", "Tipo", "Sede de retiro", "Estado", "Vence", "Días restantes"),
             [(f.id_prestamo, f.socio, f.libro, f.ejemplar, f.tipo, f.sede_retiro, f.estado,
               c.formatear_fecha(f.vencimiento), f.dias_restantes) for f in reporte.prestamos]),
            ("Material en tránsito",
             ("Remito", "Sentido", "Libro", "Origen", "Destino", "Despachado", "Última ubicación", "En viaje"),
             [(f.numero, f.sentido, f.libro, f.origen, f.destino, c.formatear_fecha(f.despachado, con_hora=True),
               f.ultima_ubicacion, _horas(f.horas_en_viaje)) for f in reporte.en_transito]),
            ("Resumen por sede",
             ("Sede", "Préstamos activos", "Por llegar", "Listos para retiro", "Enviando", "Recibiendo"),
             [(f.sede, f.prestamos_activos, f.pendientes_de_llegada, f.listos_para_retiro, f.enviando, f.recibiendo)
              for f in reporte.resumen_por_sede]),
        ], indicadores=[(len(reporte.prestamos), "Préstamos en curso"), (len(reporte.en_transito), "Ejemplares en tránsito")])

    def reporte_vencidos(self):
        self.clave_actual = "vencidos"
        self._resaltar("reporte_vencidos")
        reporte = prestamos_vencidos_y_multas.generar(calculadora=self.servicio_devoluciones.calculadora)
        self._mostrar("Préstamos vencidos y multas acumuladas", [
            (f"Préstamos vencidos (política: {reporte.politica})",
             ("Id", "Socio", "Libro", "Sede de retiro", "Venció", "Días de atraso", "Multa estimada"),
             [(f.id_prestamo, f.socio, f.libro, f.sede_retiro, c.formatear_fecha(f.vencimiento), f.dias_atraso,
               c.formatear_pesos(f.multa_estimada)) for f in reporte.vencidos]),
            ("Multas acumuladas por socio",
             ("Socio", "DNI", "Cobrado", "Adeudado", "Estimado (vencidos)", "Total"),
             [(f.socio, f.dni, c.formatear_pesos(f.cobrado), c.formatear_pesos(f.adeudado),
               c.formatear_pesos(f.estimado), c.formatear_pesos(f.total)) for f in reporte.multas_por_socio]),
        ], pie=f"Total cobrado: {c.formatear_pesos(reporte.total_cobrado)}   ·   "
               f"Total a cobrar: {c.formatear_pesos(reporte.total_adeudado)}",
           indicadores=[(len(reporte.vencidos), "Préstamos vencidos"),
                        (c.formatear_pesos(reporte.total_cobrado), "Total cobrado"),
                        (c.formatear_pesos(reporte.total_adeudado), "Total a cobrar")])

    def reporte_mas_solicitados(self):
        self.clave_actual = "solicitados"
        self._resaltar("reporte_mas_solicitados")
        rango = self._rango()
        if rango is None:
            return
        filas = libros_mas_solicitados.generar(*rango)
        self._mostrar("Libros más solicitados para préstamos inter-sedes", [
            ("Ranking (empates por título)",
             ("Puesto", "Título", "Autor", "Solicitudes", "Concretadas", "Sedes que lo pidieron"),
             [(f.posicion, f.titulo, f.autor, f.solicitudes, f.concretadas, f.sedes_destino) for f in filas]),
        ])

    def reporte_movimientos(self):
        self.clave_actual = "movimientos"
        self._resaltar("reporte_movimientos")
        rango = self._rango()
        if rango is None:
            return
        reporte = movimiento_entre_sedes.generar(*rango)
        self._mostrar("Movimiento de ejemplares entre sedes", [
            ("Envíos por ruta", ("Origen", "Destino", "Envíos", "Recibidos", "Tránsito promedio"),
             [(f.origen, f.destino, f.envios, f.recibidos, _horas(f.horas_promedio)) for f in reporte.rutas]),
            ("Envíos y recepciones por sede", ("Sede", "Enviados", "Recibidos"),
             [(f.sede, f.enviados, f.recibidos) for f in reporte.por_sede]),
        ], pie=f"Tiempo promedio de tránsito en la red: {_horas(reporte.horas_promedio_general)}",
           indicadores=[(sum(f.envios for f in reporte.rutas), "Envíos"),
                        (_horas(reporte.horas_promedio_general), "Tránsito promedio")])

    def reporte_tasa(self):
        self.clave_actual = "tasa"
        self._resaltar("reporte_tasa")
        reporte = tasa_de_envios.generar()
        columnas = ("Grupo", "Exitosos", "Con daño", "Extraviados", "Anulados", "En curso", "Tasa de éxito")

        def filas(grupos):
            return [(f.grupo, f.exitosos, f.con_danio, f.extraviados, f.anulados, f.en_curso, _porcentaje(f.tasa_exito))
                    for f in grupos]

        self._mostrar("Tasa de envíos exitosos e incidencias", [
            ("Toda la red y por sentido", columnas, filas([reporte.general] + reporte.por_sentido)),
            ("Por sede de origen", columnas, filas(reporte.por_sede_origen)),
            ("Incidencias", ("Remito", "Sentido", "Libro", "Origen", "Destino", "Tipo", "Fecha", "Observación"),
             [(f.numero, f.sentido, f.libro, f.origen, f.destino, f.tipo, c.formatear_fecha(f.fecha, con_hora=True),
               f.observacion) for f in reporte.incidencias]),
        ], indicadores=[(_porcentaje(reporte.general.tasa_exito), "Tasa de éxito de la red"),
                        (len(reporte.incidencias), "Incidencias")])

    def exportar(self, formato):
        """Exporta el reporte que se está mostrando, con el mismo rango de fechas y política de multas."""
        if self.clave_actual is None:
            c.avisar("Primero elija un reporte para mostrar.", self)
            return
        desde, hasta = None, None
        if self.clave_actual in ("solicitados", "movimientos"):
            rango = self._rango()
            if rango is None:
                return
            desde, hasta = rango
        try:
            ruta = exportacion.exportar(
                self.clave_actual, formato, desde=desde, hasta=hasta,
                calculadora=self.servicio_devoluciones.calculadora,
            )
        except OSError as error:
            c.mostrar_error(f"No se pudo guardar el archivo: {error}", self)
            return
        self.ultimo_archivo = ruta
        self.etiqueta_exportado.configure(text=f"Último archivo: {ruta.name}")
        c.notificar_ventana(self, f"Reporte exportado en {ruta.resolve()}")
        c.informar(f"Reporte exportado en:\n{ruta.resolve()}", self)
