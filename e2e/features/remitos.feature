# language: es
Característica: Remitos
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-13 @positivo @R08 @R09 @R10 @R12 @V04 @P03
  Escenario: CP-13 Empaquetar, despachar, punto de control, recibir y entregar con trazabilidad
    Dado existe el remito "R-000001" (Ida, Norte → Centro) en estado "Generado"
    Cuando el usuario hace click en "Empaquetar", "Despachar", "Punto de control" y "Recibir" con estado "Bueno"
    Y el usuario entrega el préstamo al socio en la pestaña "Préstamos"
    Entonces el sistema informa cada estado: "Empaquetado", "Despachado", "EnTransito", "Recibido"
    Y el remito queda "Cerrado" y el trayecto muestra los 6 movimientos en orden

  @CP-14 @positivo @R10 @R12 @R16
  Escenario: CP-14 Recepción con daño genera el remito de retorno
    Dado el remito "R-000001" está despachado
    Cuando el usuario recibe el remito con estado físico "Dañado"
    Entonces el sistema muestra "Remito recibido. Estado actual: Cerrado."
    Y el trayecto muestra Recibido → Daniado → Cerrado
    Y aparece "R-000002" (Retorno, Centro → Norte, Generado)

  @CP-15 @positivo @R12 @R16
  Escenario: CP-15 Registrar daño antes de entregar al socio
    Dado el remito "R-000001" está "Recibido"
    Cuando el usuario hace click en "Registrar daño" con una descripción
    Entonces el sistema muestra "Daño registrado; se generó el remito de retorno. Estado actual: Cerrado."

  @CP-16 @positivo @R12
  Escenario: CP-16 Reportar extravío
    Dado el remito "R-000001" está despachado
    Cuando el usuario hace click en "Reportar extravío" con una observación
    Entonces el sistema muestra "Extravío registrado. Estado actual: Cerrado."
    Y el ejemplar "NOR-0001" queda "Extraviado"

  @CP-17 @positivo @R12
  Escenario: CP-17 Anular un remito de ida no despachado
    Dado el remito "R-000001" está "Generado"
    Cuando el usuario hace click en "Anular" con el motivo "El socio desistió"
    Entonces el sistema muestra "Remito anulado y préstamo cancelado. Estado actual: Anulado."
    Y el ejemplar "NOR-0001" vuelve a "Disponible"

  @CP-18 @positivo @R15 @R12 @V04
  Escenario: CP-18 Devolución interbibliotecaria y remito de retorno
    Dado "Pérez, Ana" tiene un préstamo interbibliotecario activo de "NOR-0001"
    Cuando el usuario registra la devolución en estado "Bueno"
    Y el usuario empaqueta, despacha y recibe el remito "R-000002"
    Entonces el sistema muestra "Devolución registrada.\nSe generó el remito de retorno a la sede propietaria."
    Y "R-000002" queda "Cerrado" con la observación "Ejemplar reintegrado a su sede"
    Y "NOR-0001" queda "Disponible"

  @CN-27 @negativo @R12 @P03
  Escenario: CN-27 Recibir un remito que no salió
    Dado el remito "R-000001" está "Generado"
    Cuando el usuario hace click en "Recibir"
    Entonces el sistema muestra el mensaje "Operación rechazada": "No se puede recibir un remito en estado Generado."
    Y el remito sigue "Generado" con 1 movimiento

  @CN-28 @negativo @R12 @P03
  Escenario: CN-28 Anular un remito despachado
    Dado el remito "R-000001" está "Despachado"
    Cuando el usuario hace click en "Anular"
    Entonces el sistema muestra el mensaje "Operación rechazada": "No se puede anular un remito en estado Despachado."

  @CN-29 @negativo @V11
  Escenario: CN-29 Despachar hacia una sede dada de baja
    Dado el remito está "Empaquetado" y la "Sede Centro" (destino) se dio de baja
    Cuando el usuario hace click en "Despachar"
    Entonces el sistema muestra el mensaje "Operación rechazada": "No se puede despachar: la sede de destino 'Sede Centro' está dada de baja."
    Y el remito sigue "Empaquetado"

  @CN-30 @negativo @R12 @P03
  Escenario: CN-30 Anular un remito de retorno
    Dado existe el remito de retorno "R-000002"
    Cuando el usuario hace click en "Anular"
    Entonces el sistema muestra el mensaje "Operación rechazada": "Un remito de retorno no se puede anular: el ejemplar debe volver a su sede."

  @CN-31 @negativo @R12
  Escenario: CN-31 Punto de control sin ubicación
    Dado el remito está despachado
    Cuando el usuario hace click en "Punto de control" y acepta sin ubicación
    Entonces el sistema muestra el aviso "Complete el dato 'Ubicación'."

  @CN-32 @negativo @R12
  Escenario: CN-32 Acción sin remito seleccionado
    Dado no hay remito seleccionado
    Cuando el usuario hace click en "Empaquetar"
    Entonces el sistema muestra el aviso "Seleccione un remito en la lista."
