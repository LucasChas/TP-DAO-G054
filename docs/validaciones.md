# Validaciones de la consigna y sus tests

Para cada validación obligatoria de la consigna, esta tabla indica dónde se controla y qué tests la verifican. Todas tienen al menos un test positivo (la operación válida se permite) y uno negativo (la operación inválida se rechaza con una excepción de dominio).

Para correr todos los tests: `pytest -q`. Para correr los de una validación puntual, por ejemplo: `pytest -k "inhabilitado"`.

## 1. No prestar ejemplares no disponibles
**Dónde se controla:** `ServicioPrestamos._validar_solicitud`, que lanza `EjemplarNoDisponible`. Un ejemplar apartado por una reserva solo puede prestarse al socio titular de esa reserva.

| Tipo | Test |
|---|---|
| Positivo | `test_servicio_prestamos.py::test_se_presta_un_ejemplar_disponible_a_un_socio_habilitado` |
| Positivo | `test_servicio_reservas.py::test_el_titular_de_la_reserva_retira_el_ejemplar_apartado` |
| Negativo | `test_servicio_prestamos.py::test_no_se_presta_un_ejemplar_no_disponible` |
| Negativo | `test_servicio_prestamos.py::test_no_se_presta_un_ejemplar_dado_de_baja` |
| Negativo | `test_servicio_reservas.py::test_otro_socio_no_puede_llevarse_un_ejemplar_apartado` |

## 2. No prestar material a socios inhabilitados
**Dónde se controla:** `reglas.validar_socio_habilitado`, que lanza `SocioInhabilitado`. Se aplica en el préstamo local, en la solicitud interbibliotecaria, en la reserva y también en la entrega de un préstamo interbibliotecario que ya llegó.

| Tipo | Test |
|---|---|
| Positivo | `test_servicio_prestamos.py::test_se_presta_un_ejemplar_disponible_a_un_socio_habilitado` |
| Positivo | `test_servicio_socios.py::test_se_vuelve_a_habilitar_un_socio` |
| Negativo | `test_servicio_prestamos.py::test_no_se_presta_a_socio_inhabilitado` |
| Negativo | `test_servicio_prestamos.py::test_no_se_solicita_para_un_socio_inhabilitado` |
| Negativo | `test_servicio_reservas.py::test_no_se_reserva_para_un_socio_inhabilitado` |
| Negativo | `test_remitos.py::test_no_se_entrega_a_un_socio_inhabilitado` |

## 3. Controlar fechas de vencimiento de préstamos
**Dónde se controla:**
- **Plazo:** `Prestamo.registrar_entrega` fija 14 días contados desde la entrega.
- **Vencimiento:** `Prestamo.esta_vencido_al` y `dias_de_atraso_al` lo calculan.
- **Préstamos nuevos:** `ServicioPrestamos` no presta a socios con préstamos vencidos (`SocioConPrestamosVencidos`) ni con multas impagas (`SocioConMultasImpagas`).
- **Devolución:** se calcula la multa con el patrón Strategy.

| Tipo | Test |
|---|---|
| Positivo | `test_servicio_prestamos.py::test_se_presta_a_socio_con_prestamos_dentro_del_plazo` |
| Positivo | `test_servicio_devoluciones.py::test_devolucion_en_termino_sin_multa` |
| Positivo | `test_servicio_devoluciones.py::test_despues_de_pagar_la_multa_se_puede_volver_a_prestar` |
| Positivo | `test_persistencia.py::test_prestamo_dentro_del_plazo_no_esta_vencido` |
| Negativo | `test_servicio_prestamos.py::test_no_se_presta_a_socio_con_prestamos_vencidos` |
| Negativo | `test_servicio_devoluciones.py::test_no_se_presta_a_socio_con_multas_impagas` |
| Negativo | `test_servicio_devoluciones.py::test_devolucion_tardia_genera_multa_segun_el_material` |
| Negativo | `test_persistencia.py::test_prestamo_activo_pasada_la_fecha_esta_vencido` |

## 4. Mantener trazabilidad del remito en todo el trayecto
**Dónde se controla:**
- Patrón State (`estados_remito.py`): cada transición válida llama a `Remito.cambiar_estado`, que registra un `MovimientoRemito`. Las transiciones inválidas lanzan `TransicionRemitoInvalida` y no dejan rastro.
- El préstamo interbibliotecario tiene remito de ida y de retorno, así que se registra el trayecto completo de ida y vuelta.

| Tipo | Test |
|---|---|
| Positivo | `test_remitos.py::test_circuito_completo_hasta_la_entrega_al_socio` |
| Positivo | `test_remitos.py::test_cada_movimiento_guarda_estado_anterior_fecha_y_observacion` |
| Positivo | `test_servicio_devoluciones.py::test_el_ejemplar_vuelve_a_su_sede_al_recibir_el_retorno` |
| Positivo | `test_remitos.py::test_el_estado_se_reconstruye_al_leer_el_remito_de_la_base` |
| Negativo | `test_remitos.py::test_acciones_no_permitidas_en_un_remito_generado` |
| Negativo | `test_remitos.py::test_una_transicion_invalida_no_cambia_el_estado_ni_el_historial` |
| Negativo | `test_remitos.py::test_no_se_anula_un_remito_ya_despachado` |
| Negativo | `test_remitos.py::test_no_se_opera_sobre_un_remito_cerrado` |

## 5. Evitar duplicados (socios, catálogo, ejemplares)
**Dónde se controla:**
- **Servicios:** controlan el duplicado antes de guardar y lanzan `EntidadDuplicada`. Antes normalizan el DNI, el ISBN y el código de inventario.
- **Base de datos:** restricciones `UNIQUE` como segunda barrera.

| Tipo | Test |
|---|---|
| Positivo | `test_servicio_socios.py::test_se_registra_un_socio_habilitado` |
| Positivo | `test_persistencia.py::test_se_guardan_socios_con_distinto_dni` |
| Positivo | `test_servicio_catalogo.py::test_se_registra_un_libro_con_isbn_normalizado` |
| Positivo | `test_servicio_catalogo.py::test_se_registra_un_ejemplar_disponible_en_su_sede` |
| Negativo | `test_servicio_socios.py::test_no_se_registra_socio_con_dni_duplicado` |
| Negativo | `test_servicio_catalogo.py::test_no_se_registra_libro_con_isbn_duplicado` |
| Negativo | `test_servicio_catalogo.py::test_no_se_registra_ejemplar_con_codigo_duplicado` |
| Negativo | `test_persistencia.py::test_no_se_permite_socio_con_dni_duplicado` (y los equivalentes de libro y ejemplar) |

## 6. No prestar ejemplares que no pertenezcan a la sede de origen del préstamo
**Dónde se controla:** `ServicioPrestamos._validar_solicitud`, que lanza `EjemplarDeOtraSede`. La sede propietaria del ejemplar no cambia aunque el ejemplar viaje.

| Tipo | Test |
|---|---|
| Positivo | `test_servicio_prestamos.py::test_se_presta_un_ejemplar_disponible_a_un_socio_habilitado` |
| Positivo | `test_servicio_prestamos.py::test_se_solicita_un_prestamo_entre_sedes` |
| Negativo | `test_servicio_prestamos.py::test_no_se_presta_un_ejemplar_de_otra_sede` |
| Negativo | `test_servicio_prestamos.py::test_no_se_solicita_un_ejemplar_que_no_pertenece_a_la_sede_de_origen` |

## 7. No iniciar préstamos, reservas ni envíos hacia o desde una sede dada de baja
**Dónde se controla:**
- **Préstamos y reservas:** `reglas.validar_sede_activa`, que lanza `SedeDadaDeBaja`.
- **Envíos:** `Empaquetado.despachar` en el patrón State.
- **Catálogo:** `ServicioCatalogo.registrar_ejemplar` no incorpora ejemplares a una sede dada de baja.
- **Baja de la sede:** `ServicioSedes.dar_de_baja_sede` no da de baja una sede mientras algún ejemplar tenga que volver desde o hacia ella (préstamo interbibliotecario despachado, listo para retiro o activo, o remito de retorno sin cerrar). Si no, su remito de retorno no se podría despachar ni anular. Los envíos de ida que todavía no salieron sí se pueden anular, así que no impiden la baja.

| Tipo | Test |
|---|---|
| Positivo | `test_servicio_prestamos.py::test_se_presta_en_una_sede_reactivada` |
| Positivo | `test_servicio_prestamos.py::test_se_solicita_un_prestamo_entre_sedes` |
| Negativo | `test_servicio_prestamos.py::test_no_se_presta_en_una_sede_dada_de_baja` |
| Negativo | `test_servicio_prestamos.py::test_no_se_solicita_hacia_una_sede_dada_de_baja` |
| Negativo | `test_servicio_prestamos.py::test_no_se_solicita_desde_una_sede_dada_de_baja` |
| Negativo | `test_servicio_reservas.py::test_no_se_reserva_en_una_sede_dada_de_baja` |
| Negativo | `test_remitos.py::test_no_se_despacha_hacia_una_sede_dada_de_baja` |
| Negativo | `test_remitos.py::test_no_se_da_de_baja_una_sede_con_un_ejemplar_que_tiene_que_volver` |
| Negativo | `test_remitos.py::test_no_se_da_de_baja_una_sede_con_un_retorno_en_curso` |
| Negativo | `test_servicio_catalogo.py::test_no_se_registra_ejemplar_en_sede_dada_de_baja` |

## Cobertura
Los 181 tests cubren el 96 % de las líneas del paquete `biblioteca`, sin contar la interfaz de consola. Lo que queda sin cubrir son sobre todo los métodos `__repr__` y `__str__` de los modelos, algunos casos de "entidad no encontrada" y acciones de la clase base del patrón State que ningún estado deja llegar.
