"""Configuración del motor de SQLAlchemy y manejo de sesiones."""
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

URL_POR_DEFECTO = "sqlite:///biblioteca.db"

Base = declarative_base()
Sesion = sessionmaker(expire_on_commit=False)
motor = None


def _activar_claves_foraneas(conexion, registro_conexion):
    """SQLite no controla las claves foráneas salvo que se lo pida en cada conexión."""
    cursor = conexion.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def configurar_base_de_datos(url=URL_POR_DEFECTO):
    """Crea el motor para la URL indicada y lo asocia a la fábrica de sesiones.

    Para una base en memoria se usa StaticPool, así todas las sesiones
    comparten la misma conexión; de lo contrario cada sesión vería una base vacía.
    """
    global motor
    if motor is not None:
        motor.dispose()
    if ":memory:" in url:
        motor = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        motor = create_engine(url)
    event.listen(motor, "connect", _activar_claves_foraneas)
    Sesion.configure(bind=motor)
    return motor


def crear_tablas():
    """Crea todas las tablas del modelo si todavía no existen."""
    import biblioteca.modelos  # noqa: F401 (registra los modelos en Base)

    if motor is None:
        configurar_base_de_datos()
    Base.metadata.create_all(motor)


def eliminar_tablas():
    """Elimina todas las tablas del modelo. Se usa en los tests."""
    Base.metadata.drop_all(motor)


@contextmanager
def obtener_sesion():
    """Context manager que abre una sesión, confirma los cambios si no hubo
    errores, los deshace si los hubo y siempre cierra la sesión."""
    if motor is None:
        configurar_base_de_datos()
    sesion = Sesion()
    try:
        yield sesion
        sesion.commit()
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()
