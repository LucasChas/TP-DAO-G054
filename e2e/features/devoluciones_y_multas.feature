# language: es
Característica: Devoluciones y multas
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-22 @positivo @R15 @R16
  Escenario: CP-22 Devolución en término
    Dado Ana tiene un préstamo local de hoy
    Cuando el usuario registra la devolución en estado "Bueno"
    Entonces el sistema muestra "Devolución registrada."
    Y la grilla muestra 0 días, "$0.00" y pagada "Sí"

  @CP-23 @positivo @R15 @V03 @P01
  Escenario: CP-23 Multa por atraso según material y pago
    Dado Ana devuelve el Diccionario (consulta) con 3 días de atraso
    Cuando el usuario registra la devolución
    Y el usuario filtra "Solo multas impagas" y hace click en "Registrar pago de multa"
    Entonces el sistema muestra "Devolución registrada.\n3 días de atraso: multa de $3,000.00.\nTotal a pagar: $3,000.00."
    Y el sistema muestra "Pago registrado." y no quedan multas impagas

  @CP-24 @positivo @R16
  Escenario: CP-24 Devolución dañada con cargo
    Dado Ana tiene un préstamo local en término
    Cuando el usuario registra la devolución en estado "Dañado"
    Entonces el sistema muestra "Devolución registrada.\nMaterial devuelto dañado: cargo de $1,000.00.\nTotal a pagar: $1,000.00."
    Y el ejemplar queda "En reparación" / "Dañado"

  @CP-25 @positivo @P01
  Escenario: CP-25 Cambiar la política de multas en ejecución (Strategy)
    Dado dos préstamos con 3 días de atraso
    Cuando el usuario elige "Por días de atraso ($500 por día)" y registra una devolución
    Y el usuario elige "Sin multa (condonación)" y registra la otra
    Entonces el sistema informa "Política de multas: Por días de atraso ($500 por día)." y la multa es "$1,500.00"
    Y con la condonación muestra solo "Devolución registrada."

  @CN-39 @negativo @R15
  Escenario: CN-39 Pagar una devolución sin multa
    Dado existe una devolución sin multa
    Cuando el usuario hace click en "Registrar pago de multa"
    Entonces el sistema muestra el mensaje "Operación rechazada": "Esa devolución no tiene una multa pendiente de pago."

  @CN-40 @negativo @R15
  Escenario: CN-40 Devolución sin préstamos activos
    Dado no hay préstamos activos
    Cuando el usuario hace click en "Registrar devolución" y acepta sin préstamo
    Entonces el sistema muestra el aviso "Complete el dato 'Préstamo'."

  @CP-32 @positivo @P01 @R15
  Escenario: CP-32 La política de multas se mantiene al reiniciar
    Dado la política vigente es la de por defecto
    Cuando el usuario elige "Sin multa (condonación)"
    Y el usuario cierra y vuelve a abrir el programa
    Entonces la pestaña "Devoluciones y multas" muestra "Sin multa (condonación)" como política vigente
