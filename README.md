# TP Integrador 2026 – Biblioteca: Sistema de Préstamos Interbibliotecarios

Desarrollo de Aplicaciones con Objetos – Ingeniería en Sistemas de Información – UTN FRC.

Grupo G054.

## Integrantes

- Lucas Chas

## Documentación

- [Consigna](docs/consigna.md)
- [Modelo de dominio](docs/modelo_de_dominio.md)
- [Ciclo de vida del remito](docs/ciclo_de_vida_remito.md)

## Requisitos

- Python 3.12 o superior

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

El menú de consola (`main.py`) se agrega en la etapa 3.

## Tests

```bash
pytest -q
```

Cada test usa una base SQLite en memoria nueva, así que no toca `biblioteca.db`.

## Estructura

```
biblioteca/
├── configuracion/   # motor, sesión (obtener_sesion) y creación de tablas
└── modelos/         # clases del dominio mapeadas con SQLAlchemy
tests/               # tests con pytest
docs/                # consigna, modelo de dominio y ciclo de vida del remito
```

## Estado del proyecto

| Etapa | Estado |
|---|---|
| 1. Modelo de dominio | Hecha |
| 2. Persistencia | Hecha |
| 3. Sedes, socios y catálogo | Pendiente |
| 4. Préstamos, reservas y disponibilidad | Pendiente |
| 5. Remitos | Pendiente |
| 6. Devoluciones y multas | Pendiente |
| 7. Reportes | Pendiente |
| 8. Documentación final y tests | Pendiente |
