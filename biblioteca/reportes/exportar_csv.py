"""Exportación de reportes a CSV con la biblioteca estándar csv.

Se usa punto y coma como separador y codificación UTF-8 con BOM para que
Excel en español abra el archivo con las columnas y los acentos correctos.
Cada sección del reporte se escribe una debajo de la otra, separadas por una
línea en blanco.
"""
import csv


def exportar(documento_reporte, ruta):
    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo, delimiter=";")
        escritor.writerow([documento_reporte.titulo])
        escritor.writerow([f"Generado el {documento_reporte.generado:%d/%m/%Y %H:%M}"])
        for seccion in documento_reporte.secciones:
            escritor.writerow([])
            escritor.writerow([seccion.titulo])
            escritor.writerow(seccion.columnas)
            escritor.writerows(seccion.filas)
        if documento_reporte.totales:
            escritor.writerow([])
            for total in documento_reporte.totales:
                escritor.writerow([total])
    return ruta
