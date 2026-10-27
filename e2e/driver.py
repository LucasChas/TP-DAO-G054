"""Driver E2E de la interfaz gráfica (Tkinter).

Maneja la aplicación real como lo haría una persona: hace clic en los botones,
completa los formularios modales, lee el texto de los cuadros de mensaje de Tk
y presiona sus botones. No reemplaza ninguna función de la aplicación.

Los formularios y los mensajes son modales (bloquean hasta que se cierran), así
que antes de hacer clic se encolan los "pasos" que se esperan (Formulario,
Mensaje, Ventana) y un sondeo con after() los atiende a medida que aparecen.

Si la variable de entorno E2E_CAPTURAS indica una carpeta, cada paso con
captura guarda una imagen de la pantalla (Xvfb) en esa carpeta.
"""
import os
import subprocess
import time
from pathlib import Path
from tkinter import ttk

from biblioteca.interfaz_grafica import componentes

ANCHO, ALTO = 1320, 780
TIEMPO_MAXIMO = 8.0


class PasoFallido(AssertionError):
    pass


def _hijos(widget):
    for hijo in widget.winfo_children():
        yield hijo
        yield from _hijos(hijo)


class Paso:
    captura = None

    def buscar(self, driver):
        raise NotImplementedError

    def resolver(self, driver, objetivo):
        """Hace lo que corresponde y devuelve la acción final (el clic) para ejecutarla después
        de reprogramar el sondeo: el clic puede abrir otro diálogo modal."""
        raise NotImplementedError


class Formulario(Paso):
    """Completa un formulario (por etiqueta del campo) y presiona Aceptar o Cancelar."""

    def __init__(self, valores=None, captura=None, boton="Aceptar", titulo=None):
        self.valores = valores or {}
        self.captura = captura
        self.boton = boton
        self.titulo = titulo

    def __repr__(self):
        return f"Formulario({self.titulo or ''} {list(self.valores)})"

    def buscar(self, driver):
        formularios = [
            w for w in _hijos(driver.app)
            if isinstance(w, componentes.Formulario) and w.winfo_exists() and w.winfo_ismapped()
        ]
        return formularios[-1] if formularios else None

    def resolver(self, driver, formulario):
        if self.titulo is not None:
            assert formulario.title() == self.titulo, f"Se abrió '{formulario.title()}' y se esperaba '{self.titulo}'"
        campos = {campo.etiqueta: campo for campo in formulario._campos}
        for etiqueta, valor in self.valores.items():
            if etiqueta not in campos:
                raise PasoFallido(f"El formulario '{formulario.title()}' no tiene el campo '{etiqueta}': {list(campos)}")
            campo = campos[etiqueta]
            control = formulario._controles[campo.clave]
            if campo.tipo == "opcion":
                textos = list(control.cget("values"))
                elegido = next((t for t in textos if t == valor), None) or next((t for t in textos if t.startswith(valor)), None)
                if elegido is None:
                    raise PasoFallido(f"'{valor}' no está entre las opciones de '{etiqueta}': {textos}")
                control.set(elegido)
                control.event_generate("<<ComboboxSelected>>")
            else:
                control.delete(0, "end")
                control.insert(0, str(valor))
            driver.app.update()
        driver.capturar(self.captura)
        boton = driver.boton(self.boton, formulario)
        return boton.invoke


class Mensaje(Paso):
    """Cuadro de mensaje de Tk (showinfo, showerror, showwarning, askyesno)."""

    def __init__(self, captura=None, responder=None, contiene=None, titulo=None):
        self.captura = captura
        self.responder = responder
        self.contiene = contiene
        self.titulo = titulo

    def __repr__(self):
        return f"Mensaje({self.titulo or ''} {self.contiene or ''})"

    def buscar(self, driver):
        cuadros = driver.cuadros_de_mensaje()
        return cuadros[-1] if cuadros else None

    def resolver(self, driver, ruta):
        titulo = str(driver.app.tk.call("wm", "title", ruta))
        texto = str(driver.app.tk.call(f"{ruta}.msg", "cget", "-text"))
        driver.mensajes.append((titulo, texto))
        driver.capturar(self.captura)
        if self.titulo is not None and titulo != self.titulo:
            raise PasoFallido(f"Se mostró '{titulo}: {texto}' y se esperaba un mensaje '{self.titulo}'")
        if self.contiene is not None and self.contiene not in texto:
            raise PasoFallido(f"El mensaje '{texto}' no contiene '{self.contiene}'")
        boton = self.responder or driver.boton_por_defecto(ruta)
        return lambda: driver.app.tk.call(f"{ruta}.{boton}", "invoke")


class Ventana(Paso):
    """Ventana secundaria no modal (por ejemplo, la disponibilidad de un libro)."""

    def __init__(self, titulo, captura=None):
        self.titulo = titulo
        self.captura = captura
        self.tabla = None

    def __repr__(self):
        return f"Ventana({self.titulo})"

    def buscar(self, driver):
        for w in _hijos(driver.app):
            if w.winfo_class() == "Toplevel" and w.winfo_exists() and w.title() == self.titulo:
                return w
        return None

    def resolver(self, driver, ventana):
        driver.app.update()
        tabla = next(w for w in _hijos(ventana) if isinstance(w, componentes.Tabla))
        self.tabla = driver.filas(tabla)
        driver.capturar(self.captura)
        return driver.boton("Cerrar", ventana).invoke


class DriverGUI:
    def __init__(self, app, carpeta_capturas=None, prefijo=""):
        self.app = app
        self.carpeta_capturas = Path(carpeta_capturas) if carpeta_capturas else None
        self.prefijo = prefijo
        self.mensajes = []
        self.capturas = []
        self._pendientes = []
        self._error = None
        self._inicio = None

    # --- Navegación y lectura ----------------------------------------------------------

    def ir_a(self, pestania, captura=None):
        self.app.mostrar_pestania(pestania)
        self.app.update()
        self.capturar(captura)
        return self.app.pestanias[pestania]

    @property
    def pestania(self):
        return self.app.pestania_actual()

    def boton(self, texto, contenedor=None):
        contenedor = contenedor or self.pestania
        for w in _hijos(contenedor):
            if isinstance(w, ttk.Button) and w.cget("text") == texto:
                return w
        raise PasoFallido(f"No hay un botón '{texto}' en {contenedor}")

    def filas(self, tabla):
        columnas = list(tabla._columnas)
        return [dict(zip(columnas, valores)) for valores in tabla.filas()]

    def seleccionar(self, tabla, columna, valor):
        indice = list(tabla._columnas).index(columna)
        for item in tabla.arbol.get_children():
            if str(tabla.arbol.item(item, "values")[indice]) == str(valor):
                tabla.arbol.selection_set(item)
                tabla.arbol.see(item)
                tabla.arbol.event_generate("<<TreeviewSelect>>")
                self.app.update()
                return
        raise PasoFallido(f"No hay una fila con {columna} = {valor}")

    def cuadros_de_mensaje(self):
        encontrados = []

        def recorrer(ruta):
            for hijo in self.app.tk.splitlist(self.app.tk.call("winfo", "children", ruta)):
                hijo = str(hijo)
                if hijo.endswith("__tk__messagebox") and int(self.app.tk.call("winfo", "ismapped", hijo)):
                    encontrados.append(hijo)
                recorrer(hijo)

        recorrer(".")
        return encontrados

    def boton_por_defecto(self, ruta):
        for nombre in ("ok", "yes"):
            if int(self.app.tk.call("winfo", "exists", f"{ruta}.{nombre}")):
                return nombre
        raise PasoFallido(f"El cuadro {ruta} no tiene botón OK ni Sí")

    # --- Capturas ----------------------------------------------------------------------

    def capturar(self, nombre):
        if not nombre or self.carpeta_capturas is None:
            return
        self.app.update()
        time.sleep(0.05)
        self.app.update()
        self.carpeta_capturas.mkdir(parents=True, exist_ok=True)
        archivo = self.carpeta_capturas / f"{self.prefijo}{nombre}.png"
        subprocess.run(
            ["import", "-display", os.environ["DISPLAY"], "-window", "root", "-crop", f"{ANCHO}x{ALTO}+0+0", str(archivo)],
            check=True,
        )
        self.capturas.append(archivo)

    # --- Interacción con diálogos modales ----------------------------------------------

    def clic(self, texto, *pasos, contenedor=None):
        """Hace clic en un botón y atiende, en orden, los diálogos que se esperan.
        Devuelve los mensajes (título, texto) que se mostraron."""
        boton = self.boton(texto, contenedor)
        return self._con_pasos(boton.invoke, pasos)

    def menu(self, cascada, opcion, *pasos):
        barra = self.app.nametowidget(self.app.cget("menu"))
        for indice in range(barra.index("end") + 1):
            if barra.type(indice) == "cascade" and barra.entrycget(indice, "label") == cascada:
                submenu = self.app.nametowidget(barra.entrycget(indice, "menu"))
                for i in range(submenu.index("end") + 1):
                    if submenu.type(i) == "command" and submenu.entrycget(i, "label") == opcion:
                        return self._con_pasos(lambda: submenu.invoke(i), pasos)
        raise PasoFallido(f"No existe el menú {cascada} > {opcion}")

    def _con_pasos(self, accion, pasos):
        inicio_mensajes = len(self.mensajes)
        self._pendientes = list(pasos)
        self._error = None
        self._inicio = time.monotonic()
        if self._pendientes:
            self.app.after(50, self._atender)
        accion()
        self.app.update()
        # Una ventana no modal no bloquea el clic: se siguen procesando eventos hasta atenderla.
        while self._pendientes and self._error is None and time.monotonic() - self._inicio < TIEMPO_MAXIMO:
            self.app.update()
            time.sleep(0.02)
        if self._error is not None:
            raise PasoFallido(self._error)
        if self._pendientes:
            raise PasoFallido(f"No apareció lo esperado: {self._pendientes}. Mensajes: {self.mensajes[inicio_mensajes:]}")
        return self.mensajes[inicio_mensajes:]

    def _atender(self):
        if not self._pendientes or self._error is not None:
            return
        paso = self._pendientes[0]
        try:
            objetivo = paso.buscar(self)
            if objetivo is None and not isinstance(paso, Mensaje) and self.cuadros_de_mensaje():
                ruta = self.cuadros_de_mensaje()[-1]
                texto = self.app.tk.call(f"{ruta}.msg", "cget", "-text")
                self.capturar("inesperado")
                raise PasoFallido(f"Se esperaba {paso} y apareció el mensaje: {texto}")
            if objetivo is None:
                if time.monotonic() - self._inicio > TIEMPO_MAXIMO:
                    raise PasoFallido(f"Tiempo agotado esperando {paso}")
                self.app.after(50, self._atender)
                return
            clic = paso.resolver(self, objetivo)
        except Exception as error:  # noqa: BLE001 - se informa al terminar el clic
            self._error = f"{type(error).__name__}: {error}"
            self._cerrar_todo()
            return
        self._pendientes.pop(0)
        self._inicio = time.monotonic()
        if self._pendientes:
            self.app.after(50, self._atender)
        clic()

    def _cerrar_todo(self):
        """Cierra diálogos abiertos para que el clic original pueda terminar."""
        for ruta in self.cuadros_de_mensaje():
            for nombre in ("ok", "no", "cancel", "yes"):
                if int(self.app.tk.call("winfo", "exists", f"{ruta}.{nombre}")):
                    self.app.tk.call(f"{ruta}.{nombre}", "invoke")
                    break
        for w in list(_hijos(self.app)):
            if isinstance(w, componentes.Formulario) and w.winfo_exists():
                w.destroy()
