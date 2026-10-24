"""Exportación de reportes a PDF con ReportLab, con tablas y gráficos de matplotlib."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from biblioteca.reportes.graficos import dibujar

AZUL = colors.HexColor("#2f5d8a")
GRIS_CLARO = colors.HexColor("#eef2f6")
ENCABEZADO_INSTITUCIONAL = "Red de Bibliotecas · Sistema de Préstamos Interbibliotecarios"


def _estilos():
    estilos = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("Titulo", parent=estilos["Title"], textColor=AZUL, fontSize=18, spaceAfter=4),
        "subtitulo": ParagraphStyle("Subtitulo", parent=estilos["Heading2"], textColor=AZUL, spaceBefore=10, spaceAfter=4),
        "normal": estilos["Normal"],
        "chico": ParagraphStyle("Chico", parent=estilos["Normal"], fontSize=8, textColor=colors.grey),
        "celda": ParagraphStyle("Celda", parent=estilos["Normal"], fontSize=8, leading=10),
        "celda_encabezado": ParagraphStyle("CeldaEncabezado", parent=estilos["Normal"], fontSize=8, leading=10,
                                           textColor=colors.white, fontName="Helvetica-Bold"),
        "total": ParagraphStyle("Total", parent=estilos["Normal"], fontName="Helvetica-Bold", spaceBefore=4),
    }


def _tabla(seccion, estilos, ancho_disponible):
    """Convierte una sección en una tabla de ReportLab. Las celdas son Paragraph para que el texto largo baje de renglón."""
    encabezado = [Paragraph(str(columna), estilos["celda_encabezado"]) for columna in seccion.columnas]
    filas = [[Paragraph(str(valor), estilos["celda"]) for valor in fila] for fila in seccion.filas]
    ancho_columna = ancho_disponible / len(seccion.columnas)
    tabla = Table([encabezado] + filas, colWidths=[ancho_columna] * len(seccion.columnas), repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tabla


def _pie_de_pagina(lienzo, documento):
    lienzo.saveState()
    lienzo.setFont("Helvetica", 8)
    lienzo.setFillColor(colors.grey)
    lienzo.drawString(documento.leftMargin, 1 * cm, ENCABEZADO_INSTITUCIONAL)
    lienzo.drawRightString(documento.pagesize[0] - documento.rightMargin, 1 * cm, f"Página {documento.page}")
    lienzo.restoreState()


def exportar(documento_reporte, ruta):
    """Genera el PDF del reporte en la ruta indicada y devuelve la ruta."""
    estilos = _estilos()
    documento = SimpleDocTemplate(
        str(ruta), pagesize=landscape(A4),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=1.5 * cm, bottomMargin=1.8 * cm,
        title=documento_reporte.titulo, author="Sistema de Préstamos Interbibliotecarios",
    )
    ancho = documento.width
    elementos = [
        Paragraph(documento_reporte.titulo, estilos["titulo"]),
        Paragraph(f"Generado el {documento_reporte.generado:%d/%m/%Y a las %H:%M}", estilos["chico"]),
        Spacer(1, 6),
        Paragraph(documento_reporte.descripcion, estilos["normal"]),
    ]
    for seccion in documento_reporte.secciones:
        bloque = [Paragraph(seccion.titulo, estilos["subtitulo"])]
        if seccion.filas:
            bloque.append(_tabla(seccion, estilos, ancho))
        else:
            bloque.append(Paragraph("No hay datos para mostrar.", estilos["normal"]))
        elementos.append(KeepTogether(bloque[:2]) if len(seccion.filas) < 15 else bloque[0])
        if len(seccion.filas) >= 15:
            elementos.append(bloque[1])
    for total in documento_reporte.totales:
        elementos.append(Paragraph(total, estilos["total"]))
    for grafico in documento_reporte.graficos:
        if grafico.tiene_datos:
            imagen = Image(dibujar(grafico), width=17 * cm, height=17 * cm * 3.4 / 7.0)
            elementos.append(KeepTogether([Paragraph(grafico.titulo, estilos["subtitulo"]), imagen]))
    documento.build(elementos, onFirstPage=_pie_de_pagina, onLaterPages=_pie_de_pagina)
    return ruta
