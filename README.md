# TP Integrador 2026 – Biblioteca: Sistema de Préstamos Interbibliotecarios

Desarrollo de Aplicaciones con Objetos – Ingeniería en Sistemas de Información – UTN FRC.

Grupo G054.

## Integrantes

- Lucas Chas

## Descripción

Sistema de consola para una red de bibliotecas públicas. Administra las sedes, los socios y el catálogo, y gestiona:
- préstamos locales e interbibliotecarios;
- reservas;
- el envío de ejemplares entre sedes, con remitos trazables;
- devoluciones y multas.

Incluye cinco reportes.

Está hecho en Python con SQLAlchemy sobre SQLite y separado en capas: modelos, DAO, servicios e interfaz.

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

El sistema crea `biblioteca.db` en la carpeta desde donde se ejecuta. Para probarlo rápido, elegí **Cargar datos de ejemplo** en el menú principal. Se cargan:
- 3 sedes, 4 socios (uno inhabilitado), 6 libros y 10 ejemplares;
- un historial con fechas relativas a hoy: un préstamo vencido, un envío que llegó dañado y volvió a su sede, una multa impaga, un envío en viaje y una reserva pendiente.

Con eso todos los reportes muestran información.

## Tests

```bash
pytest -q
```

Hay 181 tests y cada uno usa una base SQLite en memoria nueva, así que no toca `biblioteca.db`. Cubren el 96 % del paquete `biblioteca`, sin contar la interfaz de consola. En [docs/validaciones.md](docs/validaciones.md) está la relación entre cada validación de la consigna y sus tests positivos y negativos.

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
| Reportes | **Reportes:** los cinco reportes descriptos más abajo |

Los errores de negocio (por ejemplo, prestar a un socio inhabilitado) se informan en pantalla sin cortar el programa.

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

## Estructura

```
main.py              # punto de entrada
biblioteca/
├── configuracion/   # motor, sesión (obtener_sesion), creación de tablas y datos de ejemplo
├── modelos/         # clases del dominio mapeadas con SQLAlchemy
├── dao/             # acceso a datos: un DAO por entidad, reciben la sesión del servicio
├── servicios/       # casos de uso y validaciones de negocio
├── patrones/        # State, Strategy e Iterator
├── reportes/        # un módulo por reporte
├── excepciones/     # excepciones de dominio
└── interfaz/        # menús de consola (única capa que usa input/print)
tests/               # tests con pytest
docs/                # documentación del trabajo
```

La interfaz nunca accede a la base directamente: llama a los servicios y a los reportes. Los modelos no conocen la consola.

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
