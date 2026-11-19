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

Hay 252 tests y cada uno usa una base SQLite en memoria nueva, así que no toca `biblioteca.db`. Cubren el 97 % del paquete `biblioteca`, sin contar la interfaz gráfica. Los 27 tests de la interfaz gráfica se saltean solos si Python no trae Tkinter o si no hay pantalla disponible. En [docs/validaciones.md](docs/validaciones.md) está la relación entre cada validación de la consigna y sus tests positivos y negativos.

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

Es una ventana con una pestaña por área: Sedes, Socios, Catálogo, Préstamos, Reservas, Remitos, Devoluciones y multas, y Reportes.

- **Cabecera:** muestra cuatro indicadores de la red que se recalculan después de cada operación: préstamos en curso, préstamos vencidos, envíos en tránsito y multas impagas (vencidos y multas impagas se resaltan cuando son mayores que cero).
- **Barra de estado:** abajo se ve el resultado de la última operación (o el motivo del rechazo) y la base de datos en uso.
- **Tablas:** filas alternadas, clic en un encabezado para ordenar (otro clic invierte el orden), cantidad de registros a la derecha de la barra de botones y un mensaje cuando no hay datos. Las filas con problemas (socio inhabilitado, ejemplar extraviado o dañado, reserva vencida) se ven en rojo y las cerradas o dadas de baja, en gris.
- **Botones:** la acción principal de cada pestaña está resaltada y las que dan de baja, cancelan o anulan se ven en rojo.
- **Formularios:** listas desplegables en lugar de ids, los datos obligatorios marcados con `*` y, si falta uno o tiene un formato inválido, el campo queda marcado en rojo.
- Las operaciones que actúan sobre un registro se aplican a la fila seleccionada; en Sedes, Socios y Catálogo, el doble clic (o Enter) sobre una fila abre "Modificar".

Atajos de teclado (también en **Ayuda > Atajos de teclado**): `Ctrl+1` … `Ctrl+8` para cambiar de pestaña, `F5` para actualizar, `Enter`/`Esc` para aceptar o cancelar un formulario y `Ctrl+Q` para salir.

El aspecto (colores, fuentes y estilos) está centralizado en `biblioteca/interfaz_grafica/tema.py`.

Detalles por pestaña:
- **Reservas:** cuando una reserva queda "Disponible para retiro", "Registrar retiro" presta el ejemplar apartado al socio de la reserva (préstamo local de 14 días) y la reserva pasa a "Cumplida".
- **Préstamos:** al elegir la sede (o la sede de origen, en el interbibliotecario), la lista de ejemplares muestra solo los que pertenecen a esa sede.
- **Catálogo:** al elegir un libro se ven sus ejemplares (el recuadro muestra el título del libro), y "Ver disponibilidad" muestra cuántos hay en cada sede.
- **Remitos:** al elegir un remito se ve su trayecto completo, con cada cambio de estado.
- **Devoluciones y multas:** permite cambiar la política de multas vigente (patrón Strategy). La tabla separa la multa por atraso del cargo por devolver el material dañado.
- **Reportes:** el reporte elegido queda resaltado en la lista; cada reporte muestra tarjetas con sus totales y el contenido se desplaza si no entra en la ventana.

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
