# Patrones de diseño aplicados

La consigna exige aplicar al menos dos patrones de diseño. Se aplicaron cuatro: **State**, **Strategy**, **Iterator** y **DAO**. Para cada uno se explica qué problema resuelve en este sistema, qué clases intervienen y cómo se ve en el código.

---

## 1. State: ciclo de vida del remito

**Archivos:** `biblioteca/patrones/estados_remito.py` y `biblioteca/modelos/remito.py`

### Problema
Un remito pasa por muchos estados: generado, empaquetado, despachado, en tránsito, recibido, dañado, extraviado, anulado y cerrado. En cada estado solo algunas acciones tienen sentido. Por ejemplo, no se puede recibir algo que no salió, ni anular un envío que ya está en camino. Además, cada transición tiene consecuencias distintas sobre el préstamo y el ejemplar, según el remito sea de ida o de retorno.

Resolverlo con `if remito.estado == ...` en cada método dejaría las reglas desparramadas y difíciles de revisar. La consigna aclara que el ciclo de vida del remito "será evaluado críticamente".

### Clases
| Rol en el patrón | Clase |
|---|---|
| Estado abstracto | `EstadoRemito(ABC)`: implementa todas las acciones lanzando `TransicionRemitoInvalida` |
| Estados concretos | `Generado`, `Empaquetado`, `Despachado`, `EnTransito`, `Recibido`, `Daniado`, `Extraviado`, `Anulado`, `Cerrado` |
| Clase intermedia | `EnViaje`: comportamiento común de `Despachado` y `EnTransito` |
| Contexto | `Remito`: guarda el objeto estado y le delega cada acción |

### Cómo funciona
- Cada estado concreto redefine solo las acciones que admite y decide a qué estado se pasa.
- Las acciones no permitidas heredan el comportamiento de la clase base: lanzan una excepción y el remito no cambia. La interfaz informa el error, como pide la cátedra ("las acciones no permitidas deben informar el problema sin cambiar el estado").
- Cada cambio de estado registra un `MovimientoRemito`, que es lo que da la trazabilidad.
- En la base se guarda el nombre del estado, y el objeto se reconstruye al leer el remito.

```python
class EstadoRemito(ABC):
    @property
    @abstractmethod
    def nombre(self):
        """Nombre con el que el estado se guarda en la base."""

    def _no_permitida(self, accion):
        raise TransicionRemitoInvalida(f"No se puede {accion} un remito en estado {self.nombre}.")

    def despachar(self, remito, fecha_hora, observacion):
        self._no_permitida("despachar")
    # ... lo mismo para el resto de las acciones


class Empaquetado(EstadoRemito):
    nombre = "Empaquetado"

    def despachar(self, remito, fecha_hora, observacion):
        # La consigna prohíbe iniciar envíos hacia o desde una sede dada de baja.
        for rol, sede in (("origen", remito.sede_origen), ("destino", remito.sede_destino)):
            if not sede.esta_activa:
                raise SedeDadaDeBaja(f"No se puede despachar: la sede de {rol} '{sede.nombre}' está dada de baja.")
        remito.ejemplar.estado = EstadoEjemplar.EN_TRANSITO
        if remito.sentido == SentidoRemito.IDA:
            remito.prestamo.estado = EstadoPrestamo.EN_ENVIO
        remito.cambiar_estado(Despachado(), fecha_hora, observacion)
```

El contexto (`Remito`):

```python
class Remito(Base):
    def __init__(self, **datos):
        super().__init__(**datos)
        self._estado = Generado()
        self.nombre_estado = self._estado.nombre

    @reconstructor
    def _cargar_estado(self):
        """SQLAlchemy llama a este método al traer el remito de la base."""
        self._estado = crear_estado(self.nombre_estado)

    def cambiar_estado(self, nuevo_estado, fecha_hora, observacion=None):
        self.movimientos.append(MovimientoRemito(
            estado_anterior=self.nombre_estado, estado_nuevo=nuevo_estado.nombre,
            fecha_hora=fecha_hora, observacion=observacion,
        ))
        self._estado = nuevo_estado
        self.nombre_estado = nuevo_estado.nombre

    def despachar(self, fecha_hora, observacion=None):
        self._estado.despachar(self, fecha_hora, observacion)
```

El diagrama de estados y la justificación de cada estado están en [ciclo_de_vida_remito.md](ciclo_de_vida_remito.md).

---

## 2. Strategy: cálculo de multas

**Archivo:** `biblioteca/patrones/estrategias_multa.py`

### Problema
La multa por devolución tardía se puede calcular de varias formas: un monto fijo por día, un monto según el tipo de material, o ninguno durante una condonación. La política la decide la biblioteca y puede cambiar sin que cambie el proceso de devolución. Si el cálculo estuviera dentro del servicio de devoluciones, cada política nueva obligaría a modificar ese servicio.

### Clases
| Rol en el patrón | Clase |
|---|---|
| Estrategia abstracta | `EstrategiaMulta(ABC)`, con `calcular(dias_atraso, tipo_material)` y `descripcion` |
| Estrategias concretas | `MultaPorTipoDeMaterial` (la que se usa por defecto), `MultaPorDiasDeAtraso`, `SinMulta` |
| Contexto | `CalculadoraDeMultas`, con `cambiar_estrategia()` |
| Cliente | `ServicioDevoluciones` y el reporte de multas, que reciben la calculadora ya configurada |

El cargo fijo por devolver un material dañado ($1000) no es una estrategia: lo calcula `CalculadoraDeMultas.cargo_por_danio()` con cualquier política vigente, porque es el costo de una reparación y no una sanción por atraso que se pueda condonar.

### Diferencia con State
Como marca la cátedra, en Strategy la estrategia **se elige desde afuera**: la elige quien configura la calculadora, por ejemplo desde el menú "Cambiar política de multas". En State, en cambio, es el propio estado el que decide la transición.

```python
class EstrategiaMulta(ABC):
    @abstractmethod
    def calcular(self, dias_atraso, tipo_material):
        """Devuelve el monto en pesos."""


class MultaPorTipoDeMaterial(EstrategiaMulta):
    MONTOS_DIARIOS = {TipoMaterial.LIBRO: 500.0, TipoMaterial.REVISTA: 300.0, TipoMaterial.CONSULTA: 1000.0}

    def calcular(self, dias_atraso, tipo_material):
        return dias_atraso * self.MONTOS_DIARIOS[tipo_material]


class CalculadoraDeMultas:
    def __init__(self, estrategia):
        self._estrategia = estrategia

    def cambiar_estrategia(self, estrategia):
        self._estrategia = estrategia

    def calcular(self, prestamo, fecha_devolucion):
        dias_atraso = prestamo.dias_de_atraso_al(fecha_devolucion)
        monto = self._estrategia.calcular(dias_atraso, prestamo.ejemplar.libro.tipo_material) if dias_atraso else 0.0
        return dias_atraso, monto
```

Uso en el servicio:

```python
servicio = ServicioDevoluciones(CalculadoraDeMultas(MultaPorDiasDeAtraso()))
servicio.cambiar_estrategia_de_multa(SinMulta())   # condonación
```

---

## 3. Iterator: recorrido del catálogo de ejemplares

**Archivo:** `biblioteca/patrones/iterador_catalogo.py`

### Problema
Varios casos de uso necesitan recorrer los ejemplares de un libro filtrando por sede, por disponibilidad o descartando los que ya no forman parte del inventario. Por ejemplo, la consulta de disponibilidad y la validación de reservas. Si cada uno recorriera la lista con sus propios `if`, los filtros se repetirían y el código cliente dependería de la estructura interna de la colección.

### Clases
| Rol en el patrón | Clase |
|---|---|
| Agregado | `CatalogoEjemplares`: guarda la lista de forma privada (`_ejemplares`) y ofrece iteradores |
| Iterador | `IteradorEjemplares`: implementa `__iter__` y `__next__`, saltea los que no cumplen la condición y termina con `StopIteration` |

Se usa el protocolo de iteración de Python, como en el material de la cátedra, así que los iteradores funcionan directamente en un `for`.

```python
class IteradorEjemplares:
    def __init__(self, ejemplares, condicion=None):
        self._ejemplares = ejemplares
        self._condicion = condicion or (lambda ejemplar: True)
        self._posicion = 0

    def __iter__(self):
        return self

    def __next__(self):
        while self._posicion < len(self._ejemplares):
            ejemplar = self._ejemplares[self._posicion]
            self._posicion += 1
            if self._condicion(ejemplar):
                return ejemplar
        raise StopIteration


class CatalogoEjemplares:
    def __init__(self, ejemplares):
        self._ejemplares = list(ejemplares)

    def disponibles(self, id_sede=None):
        return IteradorEjemplares(
            self._ejemplares,
            lambda e: e.estado == EstadoEjemplar.DISPONIBLE and (id_sede is None or e.sede_id == id_sede),
        )
```

Uso en el servicio de reservas:

```python
catalogo = CatalogoEjemplares(EjemplarDAO(sesion).listar(id_libro=libro.id, id_sede=sede.id))
if list(catalogo.disponibles()):
    raise OperacionNoPermitida("Hay ejemplares disponibles. Solicite el préstamo.")
```

---

## 4. DAO: acceso a datos

**Archivos:** `biblioteca/dao/`

### Problema
Si los servicios armaran sus propias consultas a la base, la lógica de negocio quedaría mezclada con el acceso a datos y sería difícil de probar y de cambiar.

### Clases
Hay un DAO por entidad principal: `SedeDAO`, `SocioDAO`, `LibroDAO`, `EjemplarDAO`, `PrestamoDAO`, `ReservaDAO`, `RemitoDAO` y `DevolucionDAO`. Todos ofrecen `crear`, `actualizar`, `obtener_por_id`, `listar` y consultas propias de su entidad, como `obtener_por_dni`, `primera_pendiente` o `socio_tiene_vencidos`. Como dice el apunte de la cátedra, los DAO no interactúan con el usuario.

### Diferencia con el apunte
En el apunte, cada método del DAO abre su propia sesión. Acá el servicio abre **una sola sesión por caso de uso**, con `obtener_sesion()`, y se la pasa a los DAO que usa. Así una operación que toca varias entidades se confirma o se deshace completa. Por ejemplo, solicitar un préstamo interbibliotecario crea el préstamo, compromete el ejemplar, cumple la reserva y genera el remito: si algo falla a la mitad, no queda nada a medio hacer.

```python
class SocioDAO:
    def __init__(self, sesion):
        self.sesion = sesion

    def obtener_por_dni(self, dni):
        return self.sesion.query(Socio).filter_by(dni=dni).first()


class ServicioSocios:
    def registrar_socio(self, dni, nombre, apellido, email=None, telefono=None):
        dni = normalizar_dni(dni)
        with obtener_sesion() as sesion:
            dao = SocioDAO(sesion)
            if dao.obtener_por_dni(dni) is not None:
                raise EntidadDuplicada(f"Ya existe un socio con DNI {dni}.")
            socio = Socio(dni=dni, nombre=nombre, apellido=apellido, email=email, telefono=telefono)
            dao.crear(socio)
        return socio
```

`obtener_sesion()` es el context manager de la cátedra: confirma los cambios si no hubo errores, los deshace si los hubo y siempre cierra la sesión.
