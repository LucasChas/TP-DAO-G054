"""Tests de la exportación de reportes a PDF (ReportLab + matplotlib) y CSV."""
import csv
from datetime import date

import pytest

from biblioteca.configuracion.datos_de_ejemplo import cargar_datos_de_ejemplo
from biblioteca.patrones.estrategias_multa import CalculadoraDeMultas, SinMulta
from biblioteca.reportes import armado, exportacion
from biblioteca.reportes.graficos import dibujar

CLAVES = [clave for clave, _, _ in armado.REPORTES]


@pytest.fixture
def datos():
    cargar_datos_de_ejemplo()


def leer_csv(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        return list(csv.reader(archivo, delimiter=";"))


@pytest.mark.parametrize("clave", CLAVES)
def test_cada_reporte_se_exporta_a_pdf(datos, tmp_path, clave):
    ruta = exportacion.exportar(clave, "pdf", carpeta=tmp_path)
    contenido = ruta.read_bytes()
    assert ruta.suffix == ".pdf"
    assert contenido.startswith(b"%PDF")
    assert len(contenido) > 5000


@pytest.mark.parametrize("clave", CLAVES)
def test_cada_reporte_se_exporta_a_csv_con_todas_sus_tablas(datos, tmp_path, clave):
    documento = armado.armar(clave)
    filas = leer_csv(exportacion.exportar(clave, "csv", carpeta=tmp_path))
    assert filas[0] == [documento.titulo]
    for seccion in documento.secciones:
        assert [seccion.titulo] in filas
        assert seccion.columnas in filas


def test_el_csv_de_la_tasa_de_envios_tiene_los_valores_del_reporte(datos, tmp_path):
    filas = leer_csv(exportacion.exportar("tasa", "csv", carpeta=tmp_path))
    assert ["Toda la red", "2", "1", "0", "0", "1", "66.7 %"] in filas


def test_el_reporte_de_multas_usa_la_politica_recibida(datos):
    documento = armado.armar("vencidos", calculadora=CalculadoraDeMultas(SinMulta()))
    assert "Sin multa" in documento.descripcion
    vencidos = documento.secciones[0]
    assert vencidos.filas and all(fila[-1] == "$0.00" for fila in vencidos.filas)


def test_el_rango_de_fechas_queda_indicado_en_el_reporte(datos):
    documento = armado.armar("solicitados", desde=date(2020, 1, 1))
    assert "Período: 01/01/2020 a hoy." in documento.descripcion


def test_cada_reporte_tiene_un_grafico_con_datos(datos):
    for clave in CLAVES:
        assert any(grafico.tiene_datos for grafico in armado.armar(clave).graficos), clave


@pytest.mark.parametrize("clave", CLAVES)
def test_los_graficos_se_dibujan_como_png(datos, clave):
    for grafico in armado.armar(clave).graficos:
        assert dibujar(grafico).getvalue().startswith(b"\x89PNG")


def test_sin_datos_el_pdf_se_genera_igual(tmp_path):
    ruta = exportacion.exportar("tasa", "pdf", carpeta=tmp_path)
    assert ruta.read_bytes().startswith(b"%PDF")


def test_un_formato_desconocido_se_rechaza(tmp_path):
    with pytest.raises(ValueError):
        exportacion.exportar("tasa", "xlsx", carpeta=tmp_path)
