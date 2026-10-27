"""Punto de entrada para exportar un reporte a PDF o CSV. Lo usan la consola y la interfaz gráfica."""
from pathlib import Path

from biblioteca.reportes import armado, exportar_csv, exportar_pdf

CARPETA_POR_DEFECTO = Path("reportes_generados")
EXPORTADORES = {"pdf": exportar_pdf.exportar, "csv": exportar_csv.exportar}


def exportar(clave, formato, carpeta=CARPETA_POR_DEFECTO, desde=None, hasta=None, calculadora=None):
    """Arma el reporte indicado, lo guarda en la carpeta y devuelve la ruta del archivo generado."""
    if formato not in EXPORTADORES:
        raise ValueError(f"Formato desconocido: {formato}")
    documento = armado.armar(clave, desde, hasta, calculadora)
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / armado.nombre_de_archivo(clave, formato, documento.generado)
    return EXPORTADORES[formato](documento, ruta)
