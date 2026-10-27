# Prompt: video explicativo de los patrones DAO, Strategy, State e Iterator

> Copiá todo lo que está debajo de la línea y pegalo en la IA. Para mejores resultados, adjuntá también el código de los archivos listados en la sección 1 (como mínimo `docs/patrones_aplicados.md`, `docs/ciclo_de_vida_remito.md`, `biblioteca/patrones/`, `biblioteca/servicios/servicio_remitos.py` y `biblioteca/servicios/servicio_devoluciones.py`).

---

**Rol:** Sos un profesor de programación que explica a un chico de 10 años: usás ejemplos de la vida cotidiana, no das nada por sabido y cada término técnico lo traducís a palabras simples.

**Objetivo:** Hacé el guion completo, escena por escena, de un video animado y abstracto de 12 a 18 minutos. El video tiene que explicar cómo se aplican los patrones **DAO, Strategy, State e Iterator** en mi sistema, cómo se relacionan entre sí y cómo encaja toda la infraestructura. Quiero entender **qué hace cada patrón, dónde está en el código y por qué lo aplicamos así**. El hilo conductor son los procesos de negocio, con foco en **la gestión de remitos** y **la gestión de devoluciones**, y además quiero comprobar que **todo proceso de negocio afectado por estos patrones cumple las reglas de diseño** que defino más abajo.

---

## 1. Contexto del sistema

- **Lenguaje:** Python, con SQLAlchemy como ORM. Hay interfaz de consola y una interfaz gráfica.
- **Dominio:** biblioteca con varias sedes. Los socios piden libros prestados; si el ejemplar está en otra sede, se hace un **préstamo interbibliotecario** y el ejemplar viaja con un **remito**. Al devolverlo, se calcula la multa por atraso y, si corresponde, el ejemplar vuelve a su sede con un **remito de retorno**.

### Patrones y dónde viven

| Patrón | Archivos | Clases clave |
|---|---|---|
| **State** | `biblioteca/patrones/estados_remito.py`, `biblioteca/modelos/remito.py` | `EstadoRemito` (abstracta), `Generado`, `Empaquetado`, `EnViaje`, `Despachado`, `EnTransito`, `Recibido`, `Daniado`, `Extraviado`, `Anulado`, `Cerrado`, `crear_estado()`; contexto `Remito` (`cambiar_estado()`, `@reconstructor _cargar_estado()`); historial `MovimientoRemito` |
| **Strategy** | `biblioteca/patrones/estrategias_multa.py` | `EstrategiaMulta` (abstracta), `MultaPorDiasDeAtraso`, `MultaPorTipoDeMaterial` (por defecto), `SinMulta`; contexto `CalculadoraDeMultas` (`cambiar_estrategia()`, `cargo_por_danio()`); `estrategia_por_nombre()` |
| **Iterator** | `biblioteca/patrones/iterador_catalogo.py` | `IteradorEjemplares` (`__iter__`, `__next__`), `CatalogoEjemplares` (`disponibles()`, `por_sede()`, `por_libro()`, `en_circulacion()`) |
| **DAO** | `biblioteca/dao/` (`remito_dao.py`, `devolucion_dao.py`, `prestamo_dao.py`, `ejemplar_dao.py`, `reserva_dao.py`, `socio_dao.py`, `sede_dao.py`, `libro_dao.py`, `configuracion_dao.py`) y `biblioteca/configuracion/base_de_datos.py` | `RemitoDAO`, `DevolucionDAO`, `ConfiguracionDAO`, etc.; `obtener_sesion()`, que abre una sesión por caso de uso y confirma o deshace todo junto |

### Procesos principales

- **Gestión de remitos:**
  - `biblioteca/servicios/servicio_remitos.py`: `generar_remito()`, `anular_remito()`, `_resolver_consecuencias()` y `ServicioRemitos` (`empaquetar`, `despachar`, `registrar_punto_de_control`, `recibir`, `registrar_danio`, `reportar_extravio`, `anular`).
  - El remito de ida se genera en `biblioteca/servicios/servicio_prestamos.py` al solicitar un préstamo interbibliotecario, y se cierra ahí mismo cuando el socio retira el ejemplar.
  - Ciclo de estados: Generado → Empaquetado → Despachado → (EnTransito) → Recibido → Cerrado, con los desvíos Anulado, Daniado y Extraviado.
  - Hay dos sentidos: **ida** y **retorno**.
- **Gestión de devoluciones:**
  - `biblioteca/servicios/servicio_devoluciones.py`: `ServicioDevoluciones.registrar_devolucion()`, `cambiar_estrategia_de_multa()`, `registrar_pago_de_multa()` y `estrategia_guardada()`.
  - Modelo: `biblioteca/modelos/devolucion.py`.
  - Al devolver, se calcula la multa con la estrategia vigente más el cargo por daño. Si el préstamo es interbibliotecario, se genera el remito de **retorno**. Si es local, el ejemplar se libera o queda en reparación.
- **Otros procesos que tocan los patrones:**
  - Disponibilidad: `biblioteca/servicios/servicio_disponibilidad.py`, usa Iterator.
  - Reservas: `biblioteca/servicios/servicio_reservas.py`, usa Iterator, y `biblioteca/servicios/asignacion_reservas.py`, que aparta el ejemplar cuando vuelve.
  - Préstamos: `biblioteca/servicios/servicio_prestamos.py`.
  - Reporte de multas: `biblioteca/reportes/prestamos_vencidos_y_multas.py`, usa Strategy.
  - Socios, sedes y catálogo usan DAO.
- **Dónde lo usa el usuario:**
  - Consola: `biblioteca/interfaz/menu_remitos.py` y `menu_devoluciones.py`.
  - Interfaz gráfica: `biblioteca/interfaz_grafica/pestania_remitos.py` y `pestania_devoluciones.py`, donde está el selector de política de multas.
- **Documentación de apoyo:** `docs/patrones_aplicados.md` y `docs/ciclo_de_vida_remito.md`.
- **Tests que demuestran cada patrón:** `tests/test_remitos.py`, `tests/test_estrategias_multa.py`, `tests/test_iterador_catalogo.py`, `tests/test_persistencia.py` y `tests/test_servicio_devoluciones.py`.

---

## 2. Requisitos que tiene que cumplir todo proceso de negocio afectado por los patrones

Primero hacé una lista de **todos** los procesos de negocio del sistema que usan al menos uno de los patrones: remitos, devoluciones, préstamos, reservas, disponibilidad, reportes de multas, socios, sedes y catálogo. Después mostrá, para cada uno, que cumple estas condiciones:

1. **Persistencia por DAO:** el proceso nunca habla directo con la base de datos. Todo alta, baja, modificación o consulta pasa por su DAO, y el DAO solo guarda y busca, sin reglas de negocio ni interacción con el usuario. Cada caso de uso abre una sola sesión con `obtener_sesion()`, para que una operación que toca varias entidades se confirme o se deshaga completa.
   *Para un chico de 10 años:* "nadie entra solo al depósito; siempre le pide las cosas al encargado".
2. **Ciclo de vida con State (cuando corresponde):** si la entidad tiene un ciclo de vida con reglas distintas en cada estado, se implementa con State. Cada estado es una clase que decide qué acciones están permitidas y a qué estado se pasa. Una transición inválida (por ejemplo, anular un remito que ya salió o recibir uno que no fue despachado) lanza `TransicionRemitoInvalida`, no cambia el estado e informa el problema. Si la entidad solo guarda un estado simple, alcanza con una enumeración (`biblioteca/modelos/enumeraciones.py`). Explicá por qué el remito usa State y el préstamo, el ejemplar y la reserva usan enumeraciones.
   *Metáfora:* "un paquete ya entregado no se puede volver a despachar".
3. **Variantes con Strategy:** si hay más de una forma de hacer algo (como calcular la multa por atraso), cada forma es una estrategia intercambiable que se elige **desde afuera**. El proceso no usa un `if/elif` por cada caso, y agregar una política nueva no obliga a tocar `ServicioDevoluciones`. La política elegida se guarda con `ConfiguracionDAO`, así sigue vigente después de reiniciar. Explicá por qué el cargo por daño ($1000) **no** es una estrategia.
   *Metáfora:* "la biblioteca elige la regla para cobrar la multa: por día, según el tipo de material, o perdonarla. La devolución es siempre igual; solo cambia la regla".
4. **Recorridos con Iterator:** cuando un proceso recorre los ejemplares filtrando por sede, por disponibilidad o por estado en circulación, lo hace con `CatalogoEjemplares` e `IteradorEjemplares`, sin depender de cómo está guardada la lista. El Iterator **no se usa dentro de remitos ni de devoluciones**; vive en disponibilidad y reservas. Mostrá cómo se conecta con remitos y devoluciones de forma indirecta: cuando un ejemplar vuelve sano con el remito de retorno, se busca a quién apartárselo. Si un recorrido de colecciones no usa el iterador, marcalo como ⚠ y evaluá si vale la pena.
   *Metáfora:* "pasar lista sin importar si la lista está en un cuaderno o en la compu".
5. **Coherencia entre procesos:** si un proceso afecta a otro, tiene que quedar claro quién dispara el cambio, qué estado cambia y qué DAO lo guarda. Ejemplos: la devolución de un préstamo interbibliotecario genera el remito de retorno; un remito dañado cancela el préstamo y genera un retorno automático; un remito de retorno cerrado libera el ejemplar o lo aparta para una reserva. Ningún proceso puede dejar a otro en un estado inválido.
6. **Trazabilidad en el código:** para cada requisito, indicá archivo, clase y método. Si un proceso **no** cumple alguno, marcalo como **⚠ incumplimiento**, explicá el riesgo con palabras simples y proponé cómo corregirlo, marcándolo como *propuesta*.

---

## 3. Estructura del video

**Escena de apertura (mapa general):** mostrá el sistema como una ciudad. Las sedes de la biblioteca son edificios, los procesos de negocio son las actividades que pasan en ellos, y cada patrón es un "servicio" de la ciudad, con su propio color, que conecta esos edificios:
- DAO: el depósito con su encargado.
- State: el semáforo que lleva cada paquete.
- Strategy: la caja de reglas intercambiables.
- Iterator: la cinta transportadora.

**Una sección por patrón,** siempre en este orden:
1. **La metáfora:** el patrón explicado con una analogía cotidiana.
   - *DAO*: el bibliotecario que busca y guarda los libros por vos; no necesitás saber en qué estante están.
   - *Strategy*: la biblioteca elige la regla para cobrar la multa; la devolución es la misma, solo cambia la regla.
   - *State*: un paquete de correo que, según su estado, permite hacer unas cosas y otras no.
   - *Iterator*: la maestra que pasa lista uno por uno, sin importar cómo está guardada la lista.
2. **El problema que resuelve:** cómo sería el código sin el patrón (por ejemplo, un `if remito.estado == ...` en cada método, un `if/elif` por política de multa, o consultas SQL mezcladas con la lógica) y por qué eso es un problema.
3. **Dónde vive en el código:** archivo, clase y método concretos de la sección 1, con un fragmento corto resaltado y explicado línea por línea en lenguaje simple.
4. **Por qué lo aplicamos así:** la decisión de diseño y qué ganamos (mantenimiento, extensión, pruebas). Mencioná el test que lo demuestra.
5. **Conexión con remitos y devoluciones:** en qué paso exacto de cada proceso aparece el patrón.

**Escena de integración (caso completo):** seguí este recorrido de principio a fin y mostrá en cada paso qué patrón entra en acción:

> El socio de la sede Sur pide un libro que está en la sede Centro → se crea el préstamo interbibliotecario y el remito de ida (DAO) → el remito pasa por Generado → Empaquetado → Despachado → EnTransito → Recibido (State) → el socio lo retira y el remito se cierra → lo devuelve con 3 días de atraso → se calcula la multa con la política vigente (Strategy) → se genera el remito de retorno → vuelve a su sede y, si hay una reserva pendiente, se aparta para esa persona (Iterator en reservas y disponibilidad).

Mostrá también un **desvío**: el ejemplar llega dañado → el remito pasa a Daniado → se cancela el préstamo y se genera un remito de retorno automático.

En cada paso mostrá cómo se pasan la información los patrones:
- el **State** valida la acción y cambia el estado del remito, registrando un `MovimientoRemito`;
- la **Strategy** decide cómo calcular la multa;
- el **Iterator** recorre los ejemplares;
- el **DAO**, dentro de una sola sesión, guarda todo en la base de datos.

**Escena de "chequeo de reglas":** pasá por cada proceso de negocio del sistema con una lista visual de los 6 requisitos de la sección 2: ✔ si se cumple y ⚠ si no. Si hay incumplimientos, explicá el riesgo y mostrá la corrección propuesta.

**Cierre:** un resumen de 30 segundos con la idea central de cada patrón, en una frase cada uno.

---

## 4. Formato de salida

Para **cada escena**:
- Número y título de la escena.
- Duración aproximada.
- **Visual:** qué se ve en pantalla (formas abstractas, íconos, flechas, animaciones; un color fijo por patrón).
- **Narración:** el texto exacto que dice la voz en off.
- **Código en pantalla:** fragmento y ruta del archivo, cuando corresponda.

**Al final del guion agregá:**
1. **Diagrama resumen** (en Mermaid) de cómo se conectan los cuatro patrones con remitos, devoluciones y los demás procesos.
2. **Tabla de patrones:** patrón | metáfora | archivo/clase | para qué sirve en remitos | para qué sirve en devoluciones.
3. **Tabla de cumplimiento:** proceso | DAO | State | Strategy | Iterator | coherencia | archivo/clase | observaciones.
4. **Diagrama de estados** (en Mermaid) del remito, con las transiciones válidas, las prohibidas y la diferencia entre remito de ida y de retorno.
5. **Autoevaluación:** tres preguntas por patrón y dos por proceso de negocio, con sus respuestas aparte.

---

## 5. Reglas

- **No inventes código.** Usá solo las rutas, clases y métodos de la sección 1 y el código que te adjunto. Si algo no está, decilo y proponé cómo debería ser, marcándolo como *propuesta*.
- **Primero la idea simple y después el código**, siempre en ese orden.
- Frases cortas, nada de jerga sin explicar y una sola idea nueva por escena.
- Usá los términos del dominio: **ejemplar**, **sede**, **socio**, **préstamo**, **remito**, **devolución** y **multa** (no "producto" ni "stock").
- Usá siempre los mismos colores y metáforas para cada patrón durante todo el video, así se reconocen fácilmente.
- Si falta información para completar algún punto, preguntame antes de suponer.
