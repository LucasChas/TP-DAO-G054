# Reportes

La consigna pide al menos cuatro reportes no triviales. Se implementaron cinco. Cada uno está en su propio módulo de `biblioteca/reportes/`, hace consultas de solo lectura y devuelve dataclasses con los datos ya calculados. El menú **Reportes** los muestra en tablas.

## 1. Préstamos activos y material en tránsito
`prestamos_activos_y_transito.py`

- **Préstamos en curso:** los activos y los interbibliotecarios que todavía no se entregaron (solicitados, en envío o listos para retiro). Para cada uno muestra los días que faltan para el vencimiento; si el número es negativo, el préstamo ya venció.
- **Material en tránsito:** los remitos en estado `Despachado` o `EnTransito`, con la fecha de despacho, la última ubicación registrada y las horas que lleva en viaje.
- **Resumen por sede:** préstamos activos, préstamos por llegar, préstamos listos para retiro, envíos saliendo y envíos llegando.

## 2. Préstamos vencidos y multas acumuladas
`prestamos_vencidos_y_multas.py`

- **Vencidos:** préstamos activos con la fecha de vencimiento pasada, con los días de atraso y la **multa estimada** calculada con la política de multas vigente (patrón Strategy).
- **Multas por socio:**
  - **cobrado:** multas pagadas;
  - **adeudado:** multas registradas en devoluciones y todavía impagas;
  - **estimado:** multa de los préstamos vencidos aún no devueltos.

  Se ordena por total de mayor a menor y, si hay empate, por apellido.

## 3. Libros más solicitados para préstamos inter-sedes
`libros_mas_solicitados.py`

- Cuenta las solicitudes de préstamo interbibliotecario por libro, incluidas las canceladas, porque también reflejan demanda. Además informa cuántas se concretaron (el ejemplar se entregó al socio) y desde cuántas sedes distintas se pidió.
- Se ordena por cantidad de solicitudes; los empates se ordenan **alfabéticamente por título**.
- Acepta un rango opcional de fechas de solicitud.
- Se arma con una sola consulta agrupada en SQLAlchemy (`group_by`, `count`, `case`).

## 4. Movimiento de ejemplares entre sedes
`movimiento_entre_sedes.py`

- Agrupa los envíos por ruta (sede origen → sede destino). Solo cuentan los remitos que se despacharon: los anulados nunca salieron de su sede.
- Para cada ruta muestra los envíos, los recibidos y el **tiempo promedio de tránsito**, medido en horas entre el movimiento `Despachado` y el movimiento `Recibido` del historial del remito.
- También muestra cuántos envíos despachó y cuántos recibió cada sede, y el promedio de tránsito de toda la red.
- Acepta un rango opcional de fechas de despacho.

## 5. Tasa de envíos logísticos exitosos e incidencias
`tasa_de_envios.py`

- Clasifica cada remito según los estados que figuran en su historial:
  - **exitoso:** se cerró sin pasar por `Daniado` ni `Extraviado`;
  - **con daño:** pasó por `Daniado`;
  - **extraviado:** pasó por `Extraviado`;
  - **anulado:** se canceló antes de salir;
  - **en curso:** todavía no terminó.
- La **tasa de éxito** se calcula sobre los envíos terminados. Se muestra para toda la red, por sentido (ida o retorno) y por sede de origen, junto con el detalle de cada incidencia.
- Este reporte depende directamente del ciclo de vida del remito: sin la trazabilidad de estados no se podría calcular.

## Datos de ejemplo
La opción **Cargar datos de ejemplo** agrega un historial de operaciones con fechas relativas a hoy, para que todos los reportes muestren información:
- un préstamo vencido;
- un envío que llegó dañado y volvió a su sede;
- una multa impaga;
- un envío en viaje;
- una reserva pendiente.
