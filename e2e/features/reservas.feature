# language: es
Característica: Reservas
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-19 @positivo @R14 @R15
  Escenario: CP-19 Reservar, asignar al devolverse y retirar
    Dado el único Rayuela de "Sede Centro" ("CEN-0001") lo tiene "Gómez, Juan"
    Cuando "Pérez, Ana" reserva "Rayuela" en "Sede Centro"
    Y Juan devuelve el ejemplar
    Y el usuario presta "CEN-0001" a Ana
    Entonces el sistema muestra "Reserva registrada. Los ejemplares se asignan por orden de llegada."
    Y la reserva pasa a "Disponible para retiro" con "CEN-0001" hasta <hoy+3>
    Y la reserva queda "Cumplida"

  @CP-20 @positivo @R14
  Escenario: CP-20 Cancelar una reserva
    Dado "Pérez, Ana" tiene una reserva pendiente
    Cuando el usuario la selecciona y hace click en "Cancelar reserva"
    Entonces el sistema muestra "Reserva cancelada."
    Y la lista de reservas activas queda vacía

  @CP-21 @positivo @R14
  Escenario: CP-21 Vencer reservas no retiradas
    Dado una reserva tiene el ejemplar apartado y el plazo de retiro venció
    Cuando el usuario hace click en "Procesar reservas no retiradas"
    Entonces el sistema muestra "Reservas vencidas por no retirar: 1."
    Y la reserva queda "Vencida"

  @CN-33 @negativo @R14
  Escenario: CN-33 Reservar con ejemplares disponibles
    Dado "CEN-0001" está disponible
    Cuando "Pérez, Ana" reserva "Rayuela" en "Sede Centro"
    Entonces el sistema muestra el mensaje "Operación rechazada": "Hay ejemplares de 'Rayuela' disponibles en 'Sede Centro'. Solicite el préstamo."

  @CN-34 @negativo @R14
  Escenario: CN-34 Reservar en una sede sin ejemplares
    Dado "Sede Norte" no tiene el Diccionario
    Cuando "Pérez, Ana" reserva el Diccionario en "Sede Norte"
    Entonces el sistema muestra el mensaje "Operación rechazada": "La sede 'Sede Norte' no tiene ejemplares de 'Diccionario de la lengua'. Solicite un préstamo interbibliotecario."

  @CN-35 @negativo @R14
  Escenario: CN-35 Reserva duplicada
    Dado Ana ya reservó Rayuela
    Cuando Ana reserva Rayuela otra vez
    Entonces el sistema muestra el mensaje "Operación rechazada": "El socio ya tiene una reserva activa de 'Rayuela'."

  @CN-36 @negativo @R14 @V02
  Escenario: CN-36 Reserva de socio inhabilitado
    Dado "Torres, Lía" está inhabilitada
    Cuando Lía reserva Rayuela
    Entonces el sistema muestra el mensaje "Operación rechazada": "El socio Torres, Lía está inhabilitado (Deuda de cuota social)."

  @CN-37 @negativo @V10
  Escenario: CN-37 Reserva en sede dada de baja
    Dado "Sede Norte" está dada de baja
    Cuando Ana reserva Rayuela en "Sede Norte"
    Entonces el sistema muestra el mensaje "Operación rechazada": "La sede de retiro 'Sede Norte' está dada de baja."

  @CN-38 @negativo @R14 @V01
  Escenario: CN-38 Prestar a otro socio un ejemplar apartado
    Dado "CEN-0001" está apartado para la reserva de Ana
    Cuando el usuario presta "CEN-0001" a "Gómez, Juan"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El ejemplar CEN-0001 está apartado para la reserva de otro socio."
