# language: es
Característica: Préstamos
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-10 @positivo @R06 @V03
  Escenario: CP-10 Préstamo local a 14 días
    Dado la socia "Pérez, Ana" está habilitada y "CEN-0001" está disponible en "Sede Centro"
    Cuando el usuario hace click en "Préstamo local"
    Y el usuario elige socia, "Sede Centro" y "CEN-0001" y acepta
    Entonces el sistema muestra el mensaje "Préstamo registrado. Vence el <hoy+14>."
    Y la grilla muestra el préstamo "Local" en estado "Activo"

  @CP-11 @positivo @R07 @R11
  Escenario: CP-11 Solicitud interbibliotecaria con remito de ida
    Dado "NOR-0001" pertenece a "Sede Norte" y está disponible
    Cuando el usuario pide "NOR-0001" de "Sede Norte" para retirar en "Sede Centro"
    Entonces el sistema muestra el mensaje "Solicitud registrada. Se generó el remito de ida."
    Y el préstamo queda "Solicitado" y aparece el remito "R-000001" (Ida, Generado)

  @CP-12 @positivo @R07
  Escenario: CP-12 Cancelar una solicitud no despachada
    Dado existe una solicitud interbibliotecaria de "NOR-0001" sin despachar
    Cuando el usuario selecciona la solicitud, hace click en "Cancelar solicitud" y confirma
    Entonces el sistema muestra "Solicitud cancelada."
    Y el préstamo queda "Cancelado", el remito "Anulado" y el ejemplar "Disponible"

  @CN-18 @negativo @V02
  Escenario: CN-18 Préstamo a socio inhabilitado
    Dado la socia "Torres, Lía" está inhabilitada por "Deuda de cuota social"
    Cuando el usuario registra un préstamo local para "Torres, Lía"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El socio Torres, Lía está inhabilitado (Deuda de cuota social)."

  @CN-19 @negativo @V01
  Escenario: CN-19 Prestar un ejemplar ya prestado
    Dado "CEN-0001" está prestado a "Gómez, Juan"
    Cuando el usuario presta "CEN-0001" a "Pérez, Ana"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El ejemplar CEN-0001 no está disponible (prestado)."

  @CN-44 @negativo @V01
  Escenario: CN-44 Prestar un ejemplar en reparación
    Dado "CEN-0001" está en reparación
    Cuando el usuario presta "CEN-0001" a "Pérez, Ana"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El ejemplar CEN-0001 no está disponible (en reparación)."

  @CN-20 @negativo @V08
  Escenario: CN-20 Solo se ofrecen ejemplares de la sede de origen
    Dado la "Sede Sur" tiene los ejemplares "SUR-0001" y "SUR-0002"
    Cuando el usuario abre "Préstamo interbibliotecario" y elige "Sede Sur" como origen
    Entonces la lista "Ejemplar de la sede de origen" muestra solo "SUR-0001" y "SUR-0002"

  @CN-21 @negativo @V09
  Escenario: CN-21 Préstamo desde una sede dada de baja
    Dado la "Sede Norte" está dada de baja
    Cuando el usuario pide "NOR-0001" con origen "Sede Norte (dada de baja)"
    Entonces el sistema muestra el mensaje "Operación rechazada": "La sede de origen 'Sede Norte' está dada de baja."

  @CN-22 @negativo @V03
  Escenario: CN-22 Socio con préstamos vencidos
    Dado "Gómez, Juan" tiene un préstamo vencido hace 6 días
    Cuando el usuario le registra un nuevo préstamo
    Entonces el sistema muestra el mensaje "Operación rechazada": "El socio Gómez, Juan tiene préstamos vencidos sin devolver."

  @CN-23 @negativo @V03
  Escenario: CN-23 Socio con multas impagas
    Dado "Gómez, Juan" devolvió con atraso y no pagó la multa
    Cuando el usuario le registra un nuevo préstamo
    Entonces el sistema muestra el mensaje "Operación rechazada": "El socio Gómez, Juan tiene multas sin pagar."

  @CN-24 @negativo @R07
  Escenario: CN-24 Misma sede de origen y destino
    Dado el usuario abrió la pestaña "Préstamos"
    Cuando el usuario pide un interbibliotecario de "Sede Centro" a "Sede Centro"
    Entonces el sistema muestra el mensaje "Operación rechazada": "En un préstamo interbibliotecario la sede de origen y la de destino deben ser distintas."

  @CN-25 @negativo @R07 @R12
  Escenario: CN-25 Entregar un préstamo que no llegó
    Dado existe una solicitud interbibliotecaria sin despachar
    Cuando el usuario hace click en "Entregar al socio"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El préstamo está solicitado: solo se entregan préstamos listos para retiro."

  @CN-26 @negativo @R07 @R12
  Escenario: CN-26 Cancelar una solicitud ya despachada
    Dado el remito de la solicitud ya fue despachado
    Cuando el usuario hace click en "Cancelar solicitud" y confirma
    Entonces el sistema muestra el mensaje "Operación rechazada": "El préstamo está en envío: solo se cancelan solicitudes no despachadas."
