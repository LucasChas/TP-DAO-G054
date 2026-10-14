# TP Integrador 2026 – Biblioteca: Sistema de Préstamos Interbibliotecarios

Desarrollo de Aplicaciones con Objetos – Ingeniería en Sistemas de Información – UTN FRC.

Grupo G054.

## Integrantes

- Lucas Chas

## Documentación

- [Consigna](docs/consigna.md)
- [Modelo de dominio](docs/modelo_de_dominio.md)
- [Ciclo de vida del remito](docs/ciclo_de_vida_remito.md)
- [Reportes](docs/reportes.md)

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

El sistema crea `biblioteca.db` en la carpeta desde donde se ejecuta. Desde el menú principal, la opción **Cargar datos de ejemplo** agrega 3 sedes, 4 socios (uno inhabilitado), 6 libros, 10 ejemplares y un historial de préstamos, envíos, devoluciones y reservas para que los reportes tengan datos.

Menús disponibles:

- **Sedes:** listar, registrar, modificar, dar de baja y reactivar.
- **Socios:** listar, buscar por DNI, registrar, modificar, inhabilitar y habilitar.
- **Catálogo:** listar y buscar libros, registrar y modificar libros, listar ejemplares por sede, registrar ejemplares, finalizar reparaciones y dar de baja ejemplares.
- **Consultar disponibilidad:** cuántos ejemplares de un libro hay en cada sede y en qué estado.
- **Préstamos:** préstamo local, solicitud de préstamo interbibliotecario (genera el remito de ida), entrega al socio de un préstamo interbibliotecario recibido, cancelación de solicitudes no despachadas y listados (en curso, por socio, vencidos).
- **Reservas:** reservar un libro en una sede, cancelar, procesar reservas no retiradas y listados.
- **Devoluciones y multas:** registrar devoluciones con el estado físico del material, listar y cobrar multas impagas, y cambiar la política de multas vigente.
- **Reportes:** préstamos activos y material en tránsito; préstamos vencidos y multas acumuladas; libros más solicitados para préstamos inter-sedes; movimiento de ejemplares entre sedes; tasa de envíos exitosos e incidencias. Ver [Reportes](docs/reportes.md).
- **Remitos:** empaquetar, despachar, registrar puntos de control, recibir (con estado físico), registrar daño, reportar extravío, anular y ver la trazabilidad completa de cada remito.

## Patrones de diseño aplicados

- **DAO:** una clase de acceso a datos por entidad (`biblioteca/dao/`).
- **State:** ciclo de vida del remito; una clase por estado y transiciones inválidas rechazadas con `TransicionRemitoInvalida` (`biblioteca/patrones/estados_remito.py`). Ver [Ciclo de vida del remito](docs/ciclo_de_vida_remito.md).
- **Strategy:** cálculo de la multa por devolución tardía; la política (por tipo de material, por días de atraso o sin multa) se elige desde afuera y se puede cambiar en ejecución (`biblioteca/patrones/estrategias_multa.py`).
- **Iterator:** `CatalogoEjemplares` e `IteradorEjemplares` recorren el catálogo filtrando por sede, libro o disponibilidad sin exponer la colección interna (`biblioteca/patrones/iterador_catalogo.py`).

## Tests

```bash
pytest -q
```

Cada test usa una base SQLite en memoria nueva, así que no toca `biblioteca.db`.

## Estructura

```
main.py              # punto de entrada
biblioteca/
├── configuracion/   # motor, sesión (obtener_sesion), creación de tablas y datos de ejemplo
├── modelos/         # clases del dominio mapeadas con SQLAlchemy
├── dao/             # acceso a datos: un DAO por entidad, reciben la sesión del servicio
├── servicios/       # casos de uso y validaciones de negocio
├── patrones/        # implementaciones de patrones de diseño
├── reportes/        # un módulo por reporte
├── excepciones/     # excepciones de dominio
└── interfaz/        # menús de consola (única capa que usa input/print)
tests/               # tests con pytest
docs/                # consigna, modelo de dominio, ciclo de vida del remito y reportes
```

## Estado del proyecto

| Etapa | Estado |
|---|---|
| 1. Modelo de dominio | Hecha |
| 2. Persistencia | Hecha |
| 3. Sedes, socios y catálogo | Hecha |
| 4. Préstamos, reservas y disponibilidad | Hecha |
| 5. Remitos | Hecha |
| 6. Devoluciones y multas | Hecha |
| 7. Reportes | Hecha |
| 8. Documentación final y tests | Pendiente |
