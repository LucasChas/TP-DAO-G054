# TP Integrador 2026 – Biblioteca: Sistema de Préstamos Interbibliotecarios

Desarrollo de Aplicaciones con Objetos – Ingeniería en Sistemas de Información – UTN FRC.

Grupo G054.

## Integrantes

| Legajo | Nombre |
|---|---|
| 95346 | Chas Diaz Lucas Martin |
| 408708 | Melina Micaela Moran Gianotti |
| 403112 | Fabrizio Sebastián Banffi Moreno |
| 94488 | Lorenzo Francisco Gonzalez |
| 94183 | Graña Carranza Mateo |

## Descripción

Sistema de escritorio para una red de bibliotecas públicas. Administra las sedes, los socios y el catálogo, y gestiona:
- préstamos locales e interbibliotecarios;
- reservas;
- el envío de ejemplares entre sedes, con remitos trazables;
- devoluciones y multas.

Incluye cinco reportes, que se pueden ver en pantalla y exportar a PDF (con gráficos) o a CSV.

Está hecho en Python con SQLAlchemy sobre SQLite y separado en capas: modelos, DAO, servicios e interfaz gráfica (Tkinter).

## Requisitos

- Python 3.12 o superior

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

Tkinter viene incluido en el instalador de Python para Windows y macOS. En Linux puede hacer falta instalarlo aparte (por ejemplo, `sudo apt install python3-tk`).

El sistema crea `biblioteca.db` en la carpeta desde donde se ejecuta. Para probarlo rápido, elegí **Archivo > Cargar datos de ejemplo**. Se cargan:
- 3 sedes, 4 socios (uno inhabilitado), 6 libros y 10 ejemplares;
- un historial con fechas relativas a hoy: un préstamo vencido, un envío que llegó dañado y volvió a su sede, una multa impaga, un envío en viaje y una reserva pendiente.

Con eso todos los reportes muestran información.

## Tests

```bash
pytest -q
```

Hay 259 tests y cada uno usa una base SQLite en memoria nueva, así que no toca `biblioteca.db`. Cubren el 97 % del paquete `biblioteca`, sin contar la interfaz gráfica. Los 32 tests de la interfaz gráfica se saltean solos si Python no trae Tkinter o si no hay pantalla disponible. En [docs/validaciones.md](docs/validaciones.md) está la relación entre cada validación de la consigna y sus tests positivos y negativos.

## Funcionalidades

| Proceso de la consigna | Pestaña de la ventana |
|---|---|
| 1. Administrar sedes | **Sedes:** alta, modificación, baja lógica y reactivación |
| 2. Administrar socios | **Socios:** alta, modificación, búsqueda por DNI, inhabilitación con motivo y rehabilitación |
| 3. Catálogo de libros y ejemplares por sede | **Catálogo:** libros (alta, modificación, búsqueda) y ejemplares (alta en una sede, fin de reparación, baja) |
| 4. Préstamos locales e interbibliotecarios | **Préstamos:** préstamo local, solicitud interbibliotecaria (sede origen y destino), entrega, cancelación y listados |
| 5. Empaquetar, despachar y recibir con remito trazable | **Remitos:** empaquetar, despachar, puntos de control, recibir con estado físico, daño, extravío, anulación y trayecto completo |
| 6. Consultar disponibilidad | **Catálogo > Ver disponibilidad:** ejemplares del libro seleccionado por sede y por estado |
| 7. Gestionar reservas | **Reservas:** reservar, registrar el retiro del ejemplar apartado, cancelar, procesar reservas no retiradas y listados |
| 8. Devoluciones y estado físico | **Devoluciones y multas:** devolución con estado físico, multas, pagos y política de multas |
| Reportes | **Reportes:** los cinco reportes descriptos más abajo, en pantalla o exportados a PDF y CSV |

## Interfaz gráfica

Es una ventana con una pestaña por área: Sedes, Socios, Catálogo, Préstamos, Reservas, Remitos, Devoluciones y multas, y Reportes. Todas siguen la misma estructura:

1. **Encabezado:** el nombre de la pestaña, una línea que explica para qué sirve y la acción principal a la derecha (por ejemplo, "Nueva sede").
2. **Búsqueda y filtros:** el campo de búsqueda filtra la tabla mientras se escribe. Los filtros son botones con su cantidad ("Vencidos 1", "Con incidencia 1"). A la derecha están las acciones que se aplican a la fila elegida.
3. **Tabla:** la primera columna muestra el estado con un punto de color: verde si está en regla, azul si está en curso, ámbar si requiere atención, rojo si hay un problema y gris si está cerrado. El texto de la fila siempre queda oscuro y legible. Un clic en un encabezado ordena por esa columna, y las barras de desplazamiento aparecen solo cuando hacen falta.
4. **Detalle** (en Socios, Catálogo y Remitos): debajo de la tabla, con un divisor que se puede arrastrar, se ve el registro elegido con sus propias acciones.

Además:
- **Cabecera:** cuatro indicadores de la red (préstamos en curso, vencidos, envíos en tránsito y multas impagas). Se recalculan después de cada operación, y un clic en uno abre la pestaña con ese filtro.
- **Barra de estado:** muestra el resultado de la última operación (o el motivo del rechazo) y la base de datos en uso.
- **Botones:** la acción principal va rellena en azul; las que dan de baja, cancelan o anulan, con borde rojo; las que no aplican a la fila elegida se ven atenuadas.
- **Formularios:** listas desplegables en lugar de ids, datos obligatorios marcados con `*` y, si falta uno o tiene un formato inválido, el campo queda marcado en rojo.
- **Tamaño de pantalla:** la ventana se abre en 1320 × 780 si la pantalla lo permite; en pantallas más chicas (por ejemplo, una notebook de 1366 × 768) se abre maximizada. Si no entran en una línea, las acciones de la barra de filtros y los botones de los reportes pasan a la línea siguiente. Cuando la ventana es baja, se ocultan las descripciones de las pestañas para dejar más lugar a las tablas.
- **Contraste:** todo el texto cumple el nivel AA de WCAG 2.2 (al menos 4,5:1) y los bordes de botones y campos, al menos 3:1. Los colores, las fuentes y los estilos están centralizados en `biblioteca/interfaz_grafica/tema.py`.

Atajos de teclado (también en **Ayuda > Atajos de teclado**): `Ctrl+1` … `Ctrl+8` para cambiar de pestaña, `F5` para actualizar, doble clic o `Enter` sobre una fila para modificarla (Sedes, Socios y Catálogo), `Enter`/`Esc` para aceptar o cancelar un formulario y `Ctrl+Q` para salir.

Detalles por pestaña:
- **Sedes:** filtros Activas, Dadas de baja y Todas.
- **Socios:** la columna "Situación" resume préstamos vencidos, multas impagas, reservas activas o el motivo de la inhabilitación. Al elegir un socio, debajo se listan todos sus préstamos, con las acciones Modificar, Habilitar e Inhabilitar. El filtro "Con deuda" lista a quienes tienen vencidos o multas impagas.
- **Catálogo:** la columna "Disponibles" indica cuántos ejemplares libres hay sobre el total ("2 de 3"). Al elegir un libro se ven sus ejemplares, y "Ver disponibilidad" muestra el detalle por sede y por estado.
- **Préstamos:** filtros En curso, Por vencer (vencen en 3 días o menos), Vencidos y Todos. Al elegir la sede (o la sede de origen, en el interbibliotecario), la lista de ejemplares muestra solo los que pertenecen a esa sede.
- **Reservas:** muestra el lugar de cada reserva pendiente en la cola de su libro y sede ("1.º de 2") y su situación (qué espera, o hasta cuándo puede retirarse el ejemplar apartado). Cuando una reserva queda "Disponible para retiro", "Registrar retiro" presta el ejemplar apartado al socio (préstamo local de 14 días) y la reserva pasa a "Cumplida".
- **Remitos:** el recorrido del remito elegido se ve como un desglose vertical. Cada movimiento tiene su fecha, la duración desde el anterior y la observación completa. El paso actual se marca con la última ubicación conocida, y al final se ven los pasos que faltan. Solo se ofrecen las acciones que el estado admite (patrón State), con la que hace avanzar el remito como principal. La vista "Tabla" muestra los mismos movimientos en columnas.
- **Devoluciones y multas:** permite cambiar la política de multas vigente (patrón Strategy). Los filtros son Todas, Impagas y Pagadas, y la tabla separa la multa por atraso del cargo por devolver el material dañado.
- **Reportes:** los cinco reportes se eligen arriba. Cada uno muestra tarjetas con sus totales, el mismo gráfico de matplotlib que se exporta al PDF y sus tablas.

Los errores de negocio se muestran en un cuadro de diálogo con el motivo, sin cerrar la aplicación.

## Patrones de diseño aplicados

Ver el detalle en [docs/patrones_aplicados.md](docs/patrones_aplicados.md).

- **State:** el ciclo de vida del remito, con una clase por estado. Las transiciones inválidas se rechazan con `TransicionRemitoInvalida` sin cambiar el estado. Ver [Ciclo de vida del remito](docs/ciclo_de_vida_remito.md).
- **Strategy:** el cálculo de la multa por devolución tardía. Hay tres políticas: por tipo de material, por días de atraso y sin multa. Se eligen desde afuera y se pueden cambiar mientras el programa corre.
- **Iterator:** `CatalogoEjemplares` e `IteradorEjemplares` recorren los ejemplares filtrando por sede, libro o disponibilidad sin exponer la colección interna.
- **DAO:** una clase de acceso a datos por entidad. Reciben la sesión del servicio, de modo que cada caso de uso se confirma o se deshace completo.

## Reportes

Ver el detalle en [docs/reportes.md](docs/reportes.md).

1. Préstamos activos y material en tránsito.
2. Préstamos vencidos y multas acumuladas.
3. Libros más solicitados para préstamos inter-sedes.
4. Movimiento de ejemplares entre sedes y tiempo promedio de tránsito.
5. Tasa de envíos logísticos exitosos e incidencias.

Todos se pueden exportar a **PDF** (tablas con estilo, totales y un gráfico de matplotlib) o a **CSV** (con el separador y la codificación que espera Excel en español).

## Estructura

```
main.py              # punto de entrada
biblioteca/
├── configuracion/   # motor, sesión (obtener_sesion), creación de tablas y datos de ejemplo
├── modelos/         # clases del dominio mapeadas con SQLAlchemy
├── dao/             # acceso a datos: un DAO por entidad, reciben la sesión del servicio
├── servicios/       # casos de uso y validaciones de negocio
├── patrones/        # State, Strategy e Iterator
├── reportes/        # un módulo por reporte y la exportación a PDF/CSV
├── excepciones/     # excepciones de dominio
└── interfaz_grafica/  # ventana Tkinter: una pestaña por área, formularios y tablas
tests/               # tests unitarios y de integración (pytest)
e2e/                 # pruebas de punta a punta sobre la ventana real
docs/                # documentación del trabajo y ejemplos de reportes exportados
```

La interfaz no accede a la base directamente: llama a los servicios y a los reportes. Los modelos no conocen la interfaz.

## Pruebas E2E

La carpeta `e2e/` tiene 80 pruebas de punta a punta que manejan la interfaz gráfica real (formularios y cuadros de mensaje de Tk). Necesitan una pantalla; en Linux se ejecutan con Xvfb:

```bash
xvfb-run -a -s "-screen 0 1320x780x24" python -m pytest e2e -v
```

Los casos están escritos en Gherkin en `e2e/features/`.

## Documentación

- [Consigna](docs/consigna.md)
- [Modelo de dominio](docs/modelo_de_dominio.md): entidades, atributos, relaciones y reglas de negocio
- [Ciclo de vida del remito](docs/ciclo_de_vida_remito.md): diagrama de estados y consecuencias de cada transición
- [Patrones aplicados](docs/patrones_aplicados.md)
- [Reportes](docs/reportes.md)
- [Validaciones y tests](docs/validaciones.md)

## Procesos opcionales de la consigna

| Proceso opcional | Estado |
|---|---|
| Revisión de estado de recepción de ejemplares (extravío, daño, destrucción) | Implementado como parte del ciclo de vida del remito |
| Inventario con códigos | Parcial: cada ejemplar tiene un código de inventario único |
| Envío de notificaciones | No implementado |
| Historial de lecturas | No implementado |
| Recomendaciones | No implementado |
