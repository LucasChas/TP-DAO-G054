"""Gráficos de los reportes con matplotlib.

Se usa la clase Figure directamente (sin pyplot), así no hace falta una
ventana ni un backend gráfico: el gráfico se dibuja en memoria y se devuelve
como imagen PNG lista para insertar en el PDF.
"""
from io import BytesIO

from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

COLORES = ["#2f5d8a", "#e08a2e", "#4f9a5a", "#b8474a", "#7a5aa6", "#8c8c8c"]


def dibujar(grafico, ancho_pulgadas=7.0, alto_pulgadas=3.4):
    """Devuelve un BytesIO con el gráfico en formato PNG."""
    figura = Figure(figsize=(ancho_pulgadas, alto_pulgadas), dpi=150)
    ejes = figura.add_subplot()
    if grafico.tipo == "torta":
        pares = [(etiqueta, valor) for etiqueta, valor in zip(grafico.etiquetas, grafico.valores) if valor]
        ejes.pie(
            [valor for _, valor in pares],
            labels=[etiqueta for etiqueta, _ in pares],
            autopct="%1.1f%%",
            colors=COLORES[: len(pares)],
            startangle=90,
        )
        ejes.axis("equal")
    elif grafico.tipo == "barras_horizontales":
        posiciones = range(len(grafico.etiquetas))
        ejes.barh(posiciones, grafico.valores, color=COLORES[0])
        ejes.set_yticks(list(posiciones), grafico.etiquetas)
        ejes.invert_yaxis()
        ejes.set_xlabel(grafico.eje_valores)
        if grafico.enteros:
            ejes.xaxis.set_major_locator(MaxNLocator(integer=True))
        _sin_bordes_superiores(ejes)
    else:
        posiciones = range(len(grafico.etiquetas))
        ejes.bar(posiciones, grafico.valores, color=COLORES[0])
        ejes.set_xticks(list(posiciones), grafico.etiquetas, rotation=20, ha="right")
        ejes.set_ylabel(grafico.eje_valores)
        if grafico.enteros:
            ejes.yaxis.set_major_locator(MaxNLocator(integer=True))
        _sin_bordes_superiores(ejes)
    figura.tight_layout()
    imagen = BytesIO()
    figura.savefig(imagen, format="png")
    imagen.seek(0)
    return imagen


def _sin_bordes_superiores(ejes):
    ejes.spines["top"].set_visible(False)
    ejes.spines["right"].set_visible(False)
