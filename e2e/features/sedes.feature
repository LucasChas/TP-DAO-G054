# language: es
Característica: Sedes
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-01 @positivo @R01
  Escenario: CP-01 Alta de sede con todos sus datos
    Dado el usuario abrió la pestaña "Sedes" sin sedes cargadas
    Cuando el usuario hace click en "Nueva sede"
    Y el usuario ingresa "Sede Oeste", "Av. Sabattini 2500", "351-4222222", "oeste@biblio.org" y "Lun a Sab 9 a 18"
    Y el usuario hace click en "Aceptar"
    Entonces el sistema muestra el mensaje "Sede registrada."
    Y la grilla muestra "Sede Oeste" con estado "Activa"

  @CP-02 @positivo @R01
  Escenario: CP-02 Modificar teléfono y horario de una sede
    Dado existe la sede "Sede Norte"
    Cuando el usuario selecciona "Sede Norte" y hace click en "Modificar"
    Y el usuario ingresa "351-4999999" en "Teléfono" y "Lun a Vie 8 a 14" en "Horario de atención"
    Y el usuario hace click en "Aceptar"
    Entonces el sistema muestra el mensaje "Sede modificada."
    Y la grilla muestra el teléfono y el horario nuevos

  @CP-03 @positivo @R02
  Escenario: CP-03 Dar de baja y reactivar una sede
    Dado existe la sede activa "Sede Sur"
    Cuando el usuario selecciona "Sede Sur" y hace click en "Dar de baja"
    Y el usuario confirma con "Sí"
    Y el usuario hace click en "Reactivar"
    Entonces el sistema muestra el mensaje "Sede dada de baja." y la sede queda "Dada de baja"
    Y el sistema muestra el mensaje "Sede reactivada." y la sede vuelve a "Activa"

  @CN-01 @negativo @R01
  Escenario: CN-01 Alta sin el nombre obligatorio
    Dado el usuario abrió la pestaña "Sedes"
    Cuando el usuario hace click en "Nueva sede"
    Y el usuario ingresa solo la dirección y hace click en "Aceptar"
    Entonces el sistema muestra el aviso "Complete el dato 'Nombre'."
    Y no se registra ninguna sede

  @CN-02 @negativo @R01
  Escenario: CN-02 Sede con nombre repetido (sin distinguir mayúsculas)
    Dado existe la sede "Sede Centro"
    Cuando el usuario registra una sede llamada "sede centro"
    Entonces el sistema muestra el mensaje "Operación rechazada": "Ya existe una sede llamada 'sede centro'."

  @CN-03 @negativo @R01
  Escenario: CN-03 Email con formato inválido
    Dado el usuario abrió la pestaña "Sedes"
    Cuando el usuario registra una sede con email "este-arroba"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El email 'este-arroba' no tiene un formato válido."

  @CN-04 @negativo @R02
  Escenario: CN-04 Dar de baja una sede ya dada de baja
    Dado la sede "Sede Sur" está dada de baja
    Cuando el usuario selecciona "Sede Sur", hace click en "Dar de baja" y confirma
    Entonces el sistema muestra el mensaje "Operación rechazada": "La sede 'Sede Sur' ya está dada de baja."

  @CN-05 @negativo @R01
  Escenario: CN-05 Modificar sin seleccionar una fila
    Dado existen sedes cargadas y ninguna está seleccionada
    Cuando el usuario hace click en "Modificar"
    Entonces el sistema muestra el aviso "Seleccione una sede en la lista."

  @CN-45 @negativo @R01
  Escenario: CN-45 Vaciar un dato opcional al modificar lo borra
    Dado la sede "Sede Centro" tiene teléfono y email
    Cuando el usuario selecciona "Sede Centro", hace click en "Modificar"
    Y el usuario borra "Teléfono" y "Email" y acepta
    Entonces el sistema muestra el mensaje "Sede modificada."
    Y la grilla muestra teléfono y email vacíos
