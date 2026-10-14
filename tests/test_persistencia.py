"""Tests de la capa de persistencia: tablas, restricciones y propiedades de los modelos."""
from datetime import date, timedelta

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from biblioteca.configuracion import base_de_datos
from biblioteca.configuracion.base_de_datos import obtener_sesion
from biblioteca.modelos import Ejemplar, Libro, MovimientoRemito, Prestamo, Remito, Sede, Socio
from biblioteca.modelos.enumeraciones import (
    EstadoEjemplar,
    EstadoPrestamo,
    EstadoSede,
    EstadoSocio,
    SentidoRemito,
    TipoPrestamo,
)


class TestConfiguracion:
    def test_se_crean_todas_las_tablas(self):
        tablas = set(inspect(base_de_datos.motor).get_table_names())
        esperadas = {
            "sedes", "socios", "libros", "ejemplares", "prestamos",
            "reservas", "remitos", "movimientos_remito", "devoluciones",
        }
        assert esperadas <= tablas

    def test_obtener_sesion_confirma_los_cambios(self):
        with obtener_sesion() as sesion:
            sesion.add(Sede(nombre="Sede Sur", direccion="Av. Vélez Sarsfield 500"))
        with obtener_sesion() as sesion:
            assert sesion.query(Sede).filter_by(nombre="Sede Sur").count() == 1

    def test_obtener_sesion_deshace_los_cambios_ante_un_error(self):
        with pytest.raises(RuntimeError):
            with obtener_sesion() as sesion:
                sesion.add(Sede(nombre="Sede Sur", direccion="Av. Vélez Sarsfield 500"))
                sesion.flush()
                raise RuntimeError("falla en medio de la operación")
        with obtener_sesion() as sesion:
            assert sesion.query(Sede).count() == 0


class TestDuplicados:
    def test_se_guardan_socios_con_distinto_dni(self, socio):
        with obtener_sesion() as sesion:
            sesion.add(Socio(dni="30999888", nombre="Juan", apellido="Gómez"))
        with obtener_sesion() as sesion:
            assert sesion.query(Socio).count() == 2

    def test_no_se_permite_socio_con_dni_duplicado(self, socio):
        with pytest.raises(IntegrityError):
            with obtener_sesion() as sesion:
                sesion.add(Socio(dni=socio.dni, nombre="Otro", apellido="Socio"))

    def test_no_se_permite_libro_con_isbn_duplicado(self, libro):
        with pytest.raises(IntegrityError):
            with obtener_sesion() as sesion:
                sesion.add(Libro(isbn=libro.isbn, titulo="Otro título", autor="Otro autor"))

    def test_no_se_permite_ejemplar_con_codigo_duplicado(self, ejemplar):
        with pytest.raises(IntegrityError):
            with obtener_sesion() as sesion:
                sesion.add(Ejemplar(
                    codigo_inventario=ejemplar.codigo_inventario,
                    libro_id=ejemplar.libro_id,
                    sede_id=ejemplar.sede_id,
                ))

    def test_no_se_permite_ejemplar_de_una_sede_inexistente(self, libro):
        with pytest.raises(IntegrityError):
            with obtener_sesion() as sesion:
                sesion.add(Ejemplar(codigo_inventario="X-1", libro_id=libro.id, sede_id=999))


class TestModelos:
    def test_valores_por_defecto_de_sede_socio_y_ejemplar(self, sede_central, socio, ejemplar):
        with obtener_sesion() as sesion:
            assert sesion.get(Sede, sede_central.id).estado == EstadoSede.ACTIVA
            assert sesion.get(Socio, socio.id).estado == EstadoSocio.HABILITADO
            assert sesion.get(Ejemplar, ejemplar.id).estado == EstadoEjemplar.DISPONIBLE

    def test_el_ejemplar_conoce_su_libro_y_su_sede(self, ejemplar, libro, sede_central):
        with obtener_sesion() as sesion:
            guardado = sesion.get(Ejemplar, ejemplar.id)
            assert guardado.libro.titulo == libro.titulo
            assert guardado.sede.nombre == sede_central.nombre

    def test_prestamo_activo_pasada_la_fecha_esta_vencido(self):
        prestamo = Prestamo(
            tipo=TipoPrestamo.LOCAL,
            estado=EstadoPrestamo.ACTIVO,
            fecha_vencimiento=date(2026, 10, 1),
        )
        assert prestamo.esta_vencido_al(date(2026, 10, 5))
        assert prestamo.dias_de_atraso_al(date(2026, 10, 5)) == 4

    def test_prestamo_dentro_del_plazo_no_esta_vencido(self):
        prestamo = Prestamo(
            tipo=TipoPrestamo.LOCAL,
            estado=EstadoPrestamo.ACTIVO,
            fecha_vencimiento=date.today() + timedelta(days=3),
        )
        assert not prestamo.esta_vencido
        assert prestamo.dias_de_atraso_al(date.today()) == 0

    def test_prestamo_devuelto_no_figura_como_vencido(self):
        prestamo = Prestamo(
            tipo=TipoPrestamo.LOCAL,
            estado=EstadoPrestamo.DEVUELTO,
            fecha_vencimiento=date(2026, 10, 1),
        )
        assert not prestamo.esta_vencido_al(date(2026, 10, 5))

    def test_el_remito_conserva_sus_movimientos_en_orden(self, socio, ejemplar, sede_central, sede_norte):
        with obtener_sesion() as sesion:
            prestamo = Prestamo(
                socio_id=socio.id,
                ejemplar_id=ejemplar.id,
                sede_origen_id=sede_central.id,
                sede_destino_id=sede_norte.id,
                tipo=TipoPrestamo.INTERBIBLIOTECARIO,
            )
            remito = Remito(
                numero="R-0001",
                prestamo=prestamo,
                sede_origen_id=sede_central.id,
                sede_destino_id=sede_norte.id,
                sentido=SentidoRemito.IDA,
            )
            remito.movimientos.append(MovimientoRemito(estado_anterior=None, estado_nuevo="Generado"))
            remito.movimientos.append(MovimientoRemito(estado_anterior="Generado", estado_nuevo="Empaquetado"))
            sesion.add(remito)
        with obtener_sesion() as sesion:
            guardado = sesion.query(Remito).filter_by(numero="R-0001").one()
            assert [m.estado_nuevo for m in guardado.movimientos] == ["Generado", "Empaquetado"]
            assert guardado.prestamo.es_interbibliotecario
