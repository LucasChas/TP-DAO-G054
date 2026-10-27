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

Sistema de consola para una red de bibliotecas públicas. Administra las sedes, los socios y el catálogo, y gestiona:
- préstamos locales e interbibliotecarios;
- reservas;
- el envío de ejemplares entre sedes, con remitos trazables;
- devoluciones y multas.

Incluye cinco reportes, que se pueden ver en pantalla y exportar a PDF (con gráficos) o a CSV.

Está hecho en Python con SQLAlchemy sobre SQLite y separado en capas: modelos, DAO, servicios e interfaz. Tiene dos interfaces que usan los mismos servicios: una de **consola** y una **gráfica** con Tkinter.

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
python main.py             # interfaz de consola
python main.py --grafica   # interfaz gráfica (Tkinter)
```

Tkinter viene incluido en el instalador de Python para Windows y macOS. En Linux puede hacer falta instalarlo aparte (por ejemplo, `sudo apt install python3-tk`). La consola funciona aunque Tkinter no esté instalado.

El sistema crea `biblioteca.db` en la carpeta desde donde se ejecuta. Para probarlo rápido, elegí **Cargar datos de ejemplo** en el menú principal de la consola o en el menú **Archivo** de la interfaz gráfica. Se cargan:
- 3 sedes, 4 socios (uno inhabilitado), 6 libros y 10 ejemplares;
- un historial con fechas relativas a hoy: un préstamo vencido, un envío que llegó dañado y volvió a su sede, una multa impaga, un envío en viaje y una reserva pendiente.

Con eso todos los reportes muestran información.

## Tests

```bash
pytest -q
```

Hay 228 tests y cada uno usa una base SQLite en memoria nueva, así que no toca `biblioteca.db`. Cubren el 96 % del paquete `biblioteca`, sin contar las interfaces. Los 15 tests de la interfaz gráfica se saltean solos si Python no trae Tkinter o si no hay pantalla disponible. En [docs/validaciones.md](docs/validaciones.md) está la relación entre cada validación de la consigna y sus tests positivos y negativos.

## Funcionalidades

| Proceso de la consigna | Dónde está en el menú |
|---|---|
| 1. Administrar sedes | **Sedes:** alta, modificación, baja lógica y reactivación |
| 2. Administrar socios | **Socios:** alta, modificación, búsqueda por DNI, inhabilitación con motivo y rehabilitación |
| 3. Catálogo de libros y ejemplares por sede | **Catálogo:** libros (alta, modificación, búsqueda) y ejemplares (alta en una sede, fin de reparación, baja) |
| 4. Préstamos locales e interbibliotecarios | **Préstamos:** préstamo local, solicitud interbibliotecaria (sede origen y destino), entrega, cancelación y listados |
| 5. Empaquetar, despachar y recibir con remito trazable | **Remitos:** empaquetar, despachar, puntos de control, recibir con estado físico, daño, extravío, anulación y trayecto completo |
| 6. Consultar disponibilidad | **Consultar disponibilidad:** ejemplares de un libro por sede y por estado |
| 7. Gestionar reservas | **Reservas:** reservar, cancelar, procesar reservas no retiradas y listados |
| 8. Devoluciones y estado físico | **Devoluciones y multas:** devolución con estado físico, multas, pagos y política de multas |
| Reportes | **Reportes:** los cinco reportes descriptos más abajo, en pantalla o exportados a PDF y CSV |

Los errores de negocio (por ejemplo, prestar a un socio inhabilitado) se informan en pantalla sin cortar el programa.

## Interfaz gráfica

Es una ventana con una pestaña por área: Sedes, Socios, Catálogo, Préstamos, Reservas, Remitos, Devoluciones y multas, y Reportes. En cada pestaña:
- una tabla muestra los datos;
- los botones abren formularios con listas desplegables, así no hace falta escribir ids;
- las operaciones que actúan sobre un registro se aplican a la fila seleccionada.

Detalles por pestaña:
- **Préstamos:** al elegir la sede (o la sede de origen, en el interbibliotecario), la lista de ejemplares muestra solo los que pertenecen a esa sede.
- **Catálogo:** al elegir un libro se ven sus ejemplares, y "Ver disponibilidad" muestra cuántos hay en cada sede.
- **Remitos:** al elegir un remito se ve su trayecto completo, con cada cambio de estado.
- **Devoluciones y multas:** permite cambiar la política de multas vigente (patrón Strategy). La tabla separa la multa por atraso del cargo por devolver el material dañado.

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
├── interfaz/        # menús de consola
└── interfaz_grafica/  # ventana Tkinter: una pestaña por área, formularios y tablas
tests/               # tests con pytest
docs/                # documentación del trabajo
```

Ninguna de las dos interfaces accede a la base directamente: las dos llaman a los mismos servicios y reportes. Los modelos no conocen ninguna interfaz.

## Pruebas E2E y auditoría

La carpeta `e2e/` tiene 74 pruebas de punta a punta que manejan la interfaz gráfica real (formularios y cuadros de mensaje de Tk) y la consola. Necesitan una pantalla; en Linux se ejecutan con Xvfb:

```bash
xvfb-run -a -s "-screen 0 1320x780x24" python -m pytest e2e -v
```

Los casos están en Gherkin en `e2e/features/` y en `docs/pruebas/casos_xray.csv` (para Jira/Xray). El informe de la auditoría (cumplimiento de la consigna, patrones, flujos con capturas y resultados) está en [docs/informe_auditoria.html](docs/informe_auditoria.html) y, sobre la plantilla de la cátedra, en `docs/Presentacion-grupo-G054.docx`. Se regeneran con `PYTHONPATH=. python docs/auditoria/construir_documentacion.py`.

## Documentación

- [Consigna](docs/consigna.md)
- [Modelo de dominio](docs/modelo_de_dominio.md): entidades, atributos, relaciones y reglas de negocio
- [Ciclo de vida del remito](docs/ciclo_de_vida_remito.md): diagrama de estados y consecuencias de cada transición
- [Patrones aplicados](docs/patrones_aplicados.md)
- [Reportes](docs/reportes.md)
- [Validaciones y tests](docs/validaciones.md)

## Estado del proyecto

Todos los procesos obligatorios, las validaciones y los reportes están implementados y probados.

| Etapa | Estado |
|---|---|
| 1. Modelo de dominio | Hecha |
| 2. Persistencia | Hecha |
| 3. Sedes, socios y catálogo | Hecha |
| 4. Préstamos, reservas y disponibilidad | Hecha |
| 5. Remitos | Hecha |
| 6. Devoluciones y multas | Hecha |
| 7. Reportes | Hecha |
| 8. Documentación final y tests | Hecha |

### Procesos opcionales de la consigna

| Proceso opcional | Estado |
|---|---|
| Revisión de estado de recepción de ejemplares (extravío, daño, destrucción) | Implementado como parte del ciclo de vida del remito |
| Inventario con códigos | Parcial: cada ejemplar tiene un código de inventario único |
| Envío de notificaciones | No implementado |
| Historial de lecturas | No implementado (los préstamos de cada socio se pueden listar) |
| Recomendaciones | No implementado |
