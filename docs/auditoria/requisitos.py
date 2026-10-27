"""Requisitos atómicos de la consigna (docs/consigna.md), su estado verificado y los hallazgos de la auditoría.

Estado: "Cumple", "Parcial", "No cumple" o "No implementado" (para lo opcional). La columna de casos E2E
se completa sola desde e2e/casos.py; acá van solo los tests unitarios que suman evidencia.
"""
from dataclasses import dataclass, field


@dataclass
class Requisito:
    id: str
    grupo: str
    descripcion: str
    estado: str
    donde: list
    observaciones: str = ""
    unitarios: list = field(default_factory=list)
    obligatorio: bool = True


PROC, VAL, OBL, ENT, SUG, OPC = ("Proceso obligatorio", "Validación de negocio", "Exigencia de la cátedra",
                                 "Entrega", "Reporte sugerido", "Proceso opcional")

REQUISITOS = [
    Requisito("R01", PROC, "Administrar sedes: alta y modificación con dirección, datos de contacto y horarios", "Cumple",
              ["biblioteca/servicios/servicio_sedes.py:21", "biblioteca/servicios/servicio_sedes.py:40",
               "biblioteca/interfaz_grafica/pestania_sedes.py:38"],
              "Defecto menor D2: desde la GUI no se puede borrar un dato opcional (teléfono, email, horario) al modificar; "
              "el sistema informa \"Sede modificada.\" pero conserva el valor (CN-45, xfail)."),
    Requisito("R02", PROC, "Sedes con estado activo / baja (baja lógica y reactivación)", "Cumple",
              ["biblioteca/servicios/servicio_sedes.py:62", "biblioteca/servicios/servicio_sedes.py:74",
               "biblioteca/modelos/sede.py:20"]),
    Requisito("R03", PROC, "Administrar socios (alta, modificación, búsqueda, inhabilitación con motivo)", "Cumple",
              ["biblioteca/servicios/servicio_socios.py:28", "biblioteca/servicios/servicio_socios.py:58",
               "biblioteca/servicios/servicio_socios.py:86"],
              "La búsqueda por DNI existe en consola; la GUI no tiene buscador (lista completa)."),
    Requisito("R04", PROC, "Administrar el catálogo de libros (alta, modificación, búsqueda)", "Cumple",
              ["biblioteca/servicios/servicio_catalogo.py:52", "biblioteca/servicios/servicio_catalogo.py:73",
               "biblioteca/servicios/servicio_catalogo.py:139"],
              "El ISBN se valida por formato (10/13 dígitos) pero no por dígito verificador. La búsqueda por texto solo está en consola."),
    Requisito("R05", PROC, "Administrar ejemplares físicos indicando la sede a la que pertenece cada uno", "Cumple",
              ["biblioteca/modelos/ejemplar.py:17", "biblioteca/servicios/servicio_catalogo.py:91",
               "biblioteca/servicios/servicio_catalogo.py:106", "biblioteca/servicios/servicio_catalogo.py:121"]),
    Requisito("R06", PROC, "Registrar préstamos locales", "Cumple", ["biblioteca/servicios/servicio_prestamos.py:64"]),
    Requisito("R07", PROC, "Registrar solicitudes de préstamo interbibliotecario indicando sede origen y destino", "Cumple",
              ["biblioteca/servicios/servicio_prestamos.py:91", "biblioteca/servicios/servicio_prestamos.py:124",
               "biblioteca/servicios/servicio_prestamos.py:141"]),
    Requisito("R08", PROC, "Empaquetar ejemplares", "Cumple",
              ["biblioteca/servicios/servicio_remitos.py:80", "biblioteca/patrones/estados_remito.py:69"]),
    Requisito("R09", PROC, "Despachar ejemplares", "Cumple",
              ["biblioteca/servicios/servicio_remitos.py:83", "biblioteca/patrones/estados_remito.py:81"]),
    Requisito("R10", PROC, "Recibir ejemplares (con estado físico)", "Cumple",
              ["biblioteca/servicios/servicio_remitos.py:89", "biblioteca/patrones/estados_remito.py:103"]),
    Requisito("R11", PROC, "Asignar un remito a cada envío", "Cumple",
              ["biblioteca/servicios/servicio_remitos.py:18", "biblioteca/dao/remito_dao.py:26"],
              "Numeración correlativa R-000001 calculada como max(id)+1; columna UNIQUE. No hay exportación ni impresión del remito como documento."),
    Requisito("R12", PROC, "Trazabilidad del remito a lo largo del trayecto (estados)", "Cumple",
              ["biblioteca/modelos/remito.py:100", "biblioteca/modelos/remito.py:143",
               "biblioteca/interfaz_grafica/pestania_remitos.py:49"]),
    Requisito("R13", PROC, "Consultar disponibilidad", "Cumple",
              ["biblioteca/servicios/servicio_disponibilidad.py:26", "biblioteca/interfaz_grafica/pestania_catalogo.py:79"]),
    Requisito("R14", PROC, "Gestionar reservas", "Cumple",
              ["biblioteca/servicios/servicio_reservas.py:25", "biblioteca/servicios/servicio_reservas.py:58",
               "biblioteca/servicios/servicio_reservas.py:72", "biblioteca/servicios/asignacion_reservas.py:11"]),
    Requisito("R15", PROC, "Registrar devoluciones", "Cumple", ["biblioteca/servicios/servicio_devoluciones.py:30"]),
    Requisito("R16", PROC, "Registrar el estado físico del material devuelto", "Cumple",
              ["biblioteca/modelos/devolucion.py:22", "biblioteca/servicios/servicio_devoluciones.py:66"]),
    Requisito("V01", VAL, "No prestar ejemplares no disponibles", "Cumple", ["biblioteca/servicios/servicio_prestamos.py:51"],
              unitarios=["test_servicio_prestamos.py::test_no_se_presta_un_ejemplar_no_disponible"]),
    Requisito("V02", VAL, "No prestar material a socios inhabilitados", "Cumple",
              ["biblioteca/servicios/reglas.py:5", "biblioteca/servicios/servicio_prestamos.py:37"],
              "También se valida al reservar y al entregar."),
    Requisito("V03", VAL, "Controlar fechas de vencimiento de préstamos", "Cumple",
              ["biblioteca/modelos/prestamo.py:46", "biblioteca/modelos/prestamo.py:52",
               "biblioteca/dao/prestamo_dao.py:40", "biblioteca/servicios/servicio_prestamos.py:38"],
              "Vence a 14 días de la entrega; se bloquea al socio con vencidos o con multas impagas."),
    Requisito("V04", VAL, "Mantener la trazabilidad del remito en todo el trayecto", "Parcial",
              ["biblioteca/servicios/servicio_prestamos.py:138", "biblioteca/servicios/servicio_prestamos.py:121",
               "biblioteca/servicios/servicio_devoluciones.py:71"],
              "Defecto D1: cuando la operación recibe una fecha (datos de ejemplo), la hora del movimiento sale del reloj real "
              "(datetime.combine(fecha, datetime.now().time())). Antes de las 10:00 el remito R-000001 de ejemplo muestra "
              "\"Cerrado\" antes que \"Recibido\" y falla el test unitario test_el_historial_de_cada_remito_de_ejemplo_esta_en_orden_cronologico.",
              unitarios=["test_datos_de_ejemplo.py::test_el_historial_de_cada_remito_de_ejemplo_esta_en_orden_cronologico (FALLA)"]),
    Requisito("V05", VAL, "Evitar socios duplicados", "Cumple", ["biblioteca/servicios/servicio_socios.py:37", "biblioteca/modelos/socio.py:17"]),
    Requisito("V06", VAL, "Evitar duplicados en el catálogo", "Cumple", ["biblioteca/servicios/servicio_catalogo.py:61", "biblioteca/modelos/libro.py:15"]),
    Requisito("V07", VAL, "Evitar ejemplares duplicados", "Cumple", ["biblioteca/servicios/servicio_catalogo.py:101", "biblioteca/modelos/ejemplar.py:15"]),
    Requisito("V08", VAL, "No prestar ejemplares que no pertenezcan a la sede de origen del préstamo", "Cumple",
              ["biblioteca/servicios/servicio_prestamos.py:46", "biblioteca/interfaz_grafica/opciones.py:26"],
              "La GUI filtra los ejemplares por sede, así que el rechazo del servicio solo se ve desde código.",
              unitarios=["test_servicio_prestamos.py::test_no_se_presta_un_ejemplar_de_otra_sede"]),
    Requisito("V09", VAL, "No iniciar préstamos hacia o desde una sede dada de baja", "Cumple",
              ["biblioteca/servicios/reglas.py:11", "biblioteca/servicios/servicio_prestamos.py:44"]),
    Requisito("V10", VAL, "No iniciar reservas en una sede dada de baja", "Cumple", ["biblioteca/servicios/servicio_reservas.py:38"]),
    Requisito("V11", VAL, "No iniciar envíos hacia o desde una sede dada de baja", "Cumple", ["biblioteca/patrones/estados_remito.py:83"]),
    Requisito("P01", OBL, "Aplicar al menos dos patrones de diseño", "Cumple",
              ["biblioteca/patrones/estados_remito.py:24", "biblioteca/patrones/estrategias_multa.py:21",
               "biblioteca/patrones/iterador_catalogo.py:11", "biblioteca/dao/__init__.py:1"],
              "Cuatro: State, Strategy, Iterator y DAO."),
    Requisito("P02", OBL, "Implementar al menos cuatro reportes no triviales", "Cumple",
              ["biblioteca/reportes/prestamos_activos_y_transito.py:62", "biblioteca/reportes/prestamos_vencidos_y_multas.py:56",
               "biblioteca/reportes/libros_mas_solicitados.py:29", "biblioteca/reportes/movimiento_entre_sedes.py:45",
               "biblioteca/reportes/tasa_de_envios.py:68", "biblioteca/reportes/exportacion.py:10"],
              "Cinco reportes, exportables a PDF (con gráfico) y CSV."),
    Requisito("P03", OBL, "Ciclo de vida del remito y sus estados (evaluado críticamente)", "Cumple",
              ["biblioteca/patrones/estados_remito.py:24", "docs/ciclo_de_vida_remito.md:1"],
              "Nueve estados con justificación. Observación de diseño: servicio_remitos.py:45-59 decide consecuencias "
              "comparando nombre_estado con strings, fuera de las clases de estado."),
    Requisito("P04", OBL, "Investigar el dominio y definir entidades, atributos y reglas", "Cumple",
              ["docs/modelo_de_dominio.md:1", "biblioteca/modelos/__init__.py:1"]),
    Requisito("E01", ENT, "Documento de presentación según la plantilla (grupo, objetivos, alcances, DER/UML)", "Parcial",
              ["docs/Presentacion-grupo-G054.docx"],
              "Antes de esta auditoría no existía en el repositorio. Se generó con los datos verificables; "
              "faltan los legajos y la confirmación de los integrantes (el README solo nombra a Lucas Chas)."),
    Requisito("S01", SUG, "Reporte: préstamos activos y material en tránsito", "Cumple",
              ["biblioteca/reportes/prestamos_activos_y_transito.py:62"], obligatorio=False),
    Requisito("S02", SUG, "Reporte: préstamos vencidos y multas acumuladas", "Cumple",
              ["biblioteca/reportes/prestamos_vencidos_y_multas.py:56"], obligatorio=False),
    Requisito("S03", SUG, "Reporte: libros más solicitados inter-sedes", "Cumple",
              ["biblioteca/reportes/libros_mas_solicitados.py:29"], obligatorio=False),
    Requisito("S04", SUG, "Reporte: disponibilidad de catálogo por sede", "Parcial",
              ["biblioteca/servicios/servicio_disponibilidad.py:26"],
              "Existe como consulta por libro, no como reporte de todo el catálogo ni exportable.", obligatorio=False),
    Requisito("S05", SUG, "Reporte: tasa de envíos exitosos e incidencias", "Cumple",
              ["biblioteca/reportes/tasa_de_envios.py:68"], obligatorio=False),
    Requisito("S06", SUG, "Reporte: movimiento entre sedes y tiempo promedio de tránsito", "Cumple",
              ["biblioteca/reportes/movimiento_entre_sedes.py:45"], obligatorio=False),
    Requisito("O01", OPC, "Envío de notificaciones", "No implementado", [], obligatorio=False),
    Requisito("O02", OPC, "Historial de lecturas", "No implementado", ["biblioteca/servicios/servicio_prestamos.py:165"],
              "Solo se pueden listar los préstamos de un socio (consola).", obligatorio=False),
    Requisito("O03", OPC, "Recomendaciones", "No implementado", [], obligatorio=False),
    Requisito("O04", OPC, "Inventario con códigos", "Parcial", ["biblioteca/modelos/ejemplar.py:15"],
              "Código de inventario único por ejemplar; no hay procesos de inventario.", obligatorio=False),
    Requisito("O05", OPC, "Revisión del estado de recepción (extravío, daño, destrucción)", "Cumple",
              ["biblioteca/patrones/estados_remito.py:123", "biblioteca/patrones/estados_remito.py:148"],
              "Extravío y daño implementados; \"destrucción\" no es un estado propio (se resuelve con daño + baja del ejemplar).",
              obligatorio=False),
]


@dataclass
class Hallazgo:
    id: str
    prioridad: str  # Alta / Media / Baja
    titulo: str
    detalle: str
    evidencia: list
    arreglo: str


HALLAZGOS = [
    Hallazgo("D1", "Alta", "El test unitario de datos de ejemplo falla antes de las 10:00 y el remito de ejemplo muestra el cierre antes de la recepción",
             "Al recibir una fecha, préstamos y devoluciones completan la hora con datetime.now(). En los datos de ejemplo la "
             "recepción es a las 10:00 y la entrega toma la hora real; antes de esa hora el trayecto de R-000001 queda fuera de "
             "orden. En una defensa a la mañana, `pytest` muestra 1 fallo (227 de 228 pasan) y la pestaña Remitos muestra el desorden.",
             ["biblioteca/servicios/servicio_prestamos.py:138", "biblioteca/servicios/servicio_prestamos.py:121",
              "biblioteca/servicios/servicio_prestamos.py:147", "biblioteca/servicios/servicio_devoluciones.py:71",
              "docs/pruebas/resultados_unitarios.txt", "docs/auditoria/evidencia_hora_del_reloj.py",
              "docs/capturas/CP-26_02_trayecto_R-000001.png"],
             "Que entregar_prestamo, solicitar_prestamo_interbibliotecario, cancelar_prestamo y registrar_devolucion acepten "
             "fecha_hora (datetime) en lugar de combinar con el reloj, y que datos_de_ejemplo.py pase horas explícitas "
             "(por ejemplo _momento(23, 11) para la entrega). Alternativa mínima: usar max(fecha_hora, último movimiento)."),
    Hallazgo("E01", "Alta", "La presentación del grupo no estaba hecha y faltan legajos",
             "La plantilla Presentacion-grupo.docx estaba vacía y no había ninguna versión en el repositorio. El README solo nombra "
             "a un integrante y sin legajo.",
             ["README.md:9"], "Completar legajos y nombres en docs/Presentacion-grupo-G054.docx (sección 1) antes de entregar."),
    Hallazgo("D2", "Media", "Al modificar, vaciar un dato opcional no lo borra",
             "La GUI envía None cuando el campo queda vacío y los servicios interpretan None como \"no modificar\". El usuario "
             "ve \"Sede modificada.\" pero el teléfono/email siguen guardados. Afecta sedes, socios y libros.",
             ["biblioteca/interfaz_grafica/componentes.py:258", "biblioteca/servicios/servicio_sedes.py:53",
              "biblioteca/servicios/servicio_socios.py:51", "biblioteca/servicios/servicio_catalogo.py:82",
              "e2e/test_e2e_sedes.py (CN-45, xfail)"],
             "En los formularios de modificación enviar \"\" en lugar de None para los campos opcionales vacíos "
             "(texto_opcional ya convierte \"\" en None al guardar), o usar un valor centinela distinto de None para \"sin cambios\"."),
    Hallazgo("F1", "Media", "El remito no se puede exportar ni imprimir como documento",
             "El remito existe como entidad con número, sedes, sentido y trayecto, y se ve en pantalla, pero no hay salida en "
             "PDF/CSV del remito. Si en la defensa se pide \"mostrar el remito\" solo se puede mostrar la pantalla o un reporte.",
             ["biblioteca/reportes/exportacion.py:7", "biblioteca/interfaz_grafica/pestania_remitos.py:19"],
             "Agregar un exportador de remito (DocumentoReporte con cabecera: número, sentido, sedes, ejemplar, socio; "
             "y una tabla con el trayecto) reutilizando exportar_pdf/exportar_csv, con un botón \"Exportar remito\" en la pestaña."),
    Hallazgo("P1", "Media", "Las consecuencias del State se deciden comparando strings fuera de los estados",
             "_resolver_consecuencias pregunta remito.nombre_estado == \"Daniado\" / \"Cerrado\". Es una cadena de if por estado, "
             "justo lo que el patrón evita, y un error de tipeo no lo detecta nadie.",
             ["biblioteca/servicios/servicio_remitos.py:43-60"],
             "Que cada estado devuelva o registre las consecuencias pendientes (por ejemplo, un método hook en EstadoRemito), "
             "o comparar con las clases (isinstance(remito.estado, Daniado)) en lugar de strings."),
    Hallazgo("P2", "Baja", "La política de multas elegida no se guarda",
             "La Strategy vigente vive en memoria: al reiniciar vuelve a \"Por tipo de material\", y consola y GUI tienen "
             "instancias separadas.", ["biblioteca/interfaz_grafica/aplicacion.py:33", "biblioteca/servicios/servicio_devoluciones.py:23"],
             "Persistir el nombre de la estrategia vigente (tabla de configuración) y reconstruirla al iniciar."),
    Hallazgo("P3", "Baja", "El ciclo de vida del ejemplar no usa State",
             "El ejemplar tiene 7 estados con transiciones repartidas entre servicios y estados del remito "
             "(asignaciones ejemplar.estado = ...). No hay una clase que diga qué transiciones son válidas.",
             ["biblioteca/patrones/estados_remito.py:86", "biblioteca/servicios/servicio_devoluciones.py:69",
              "biblioteca/servicios/asignacion_reservas.py:21", "biblioteca/servicios/servicio_catalogo.py:117"],
             "No es obligatorio (ya hay 4 patrones). Si se pregunta en la defensa: es el candidato natural a un segundo State."),
    Hallazgo("S4", "Baja", "Reporte sugerido de disponibilidad por sede no está como reporte",
             "La consigna lo sugiere; hay una consulta por libro, no un reporte exportable de todo el catálogo.",
             ["biblioteca/servicios/servicio_disponibilidad.py:26"],
             "Opcional: reporte con libros × sedes reutilizando CatalogoEjemplares."),
    Hallazgo("C1", "Baja", "Detalles menores de validación e interfaz",
             "ISBN sin dígito verificador; la GUI no tiene buscador de libros ni de socios por DNI (sí la consola); "
             "los estados del remito se muestran con su nombre interno (\"EnTransito\", \"Daniado\").",
             ["biblioteca/servicios/servicio_catalogo.py:21", "biblioteca/interfaz_grafica/pestania_remitos.py:44"],
             "Validar el dígito verificador; agregar un campo de búsqueda; mapear nombre_estado a un texto visible."),
]
