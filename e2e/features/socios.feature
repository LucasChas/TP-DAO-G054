# language: es
Característica: Socios
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-04 @positivo @R03
  Escenario: CP-04 Alta de socio con DNI con puntos
    Dado el usuario abrió la pestaña "Socios"
    Cuando el usuario hace click en "Nuevo socio"
    Y el usuario ingresa "30.555.666", "Carla", "Ruiz" y acepta
    Entonces el sistema muestra el mensaje "Socio registrado."
    Y la grilla muestra DNI "30555666", "Ruiz, Carla" y estado "Habilitado"

  @CP-05 @positivo @R03 @V02
  Escenario: CP-05 Inhabilitar con motivo y volver a habilitar
    Dado existe el socio habilitado DNI "28999888"
    Cuando el usuario lo inhabilita con el motivo "Extravió un ejemplar"
    Y el usuario hace click en "Habilitar"
    Entonces el sistema muestra "Socio inhabilitado." y la grilla muestra el estado y el motivo
    Y el sistema muestra "Socio habilitado." y el estado vuelve a "Habilitado"

  @CP-06 @positivo @R03
  Escenario: CP-06 Modificar el email de un socio
    Dado existe la socia "Pérez, Ana"
    Cuando el usuario cambia el email a "ana.perez@correo.com"
    Entonces el sistema muestra el mensaje "Socio modificado."
    Y la grilla muestra el email nuevo

  @CN-06 @negativo @R03
  Escenario: CN-06 DNI con letras
    Dado el usuario abrió la pestaña "Socios"
    Cuando el usuario registra un socio con DNI "12ab"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El DNI '12ab' no es válido: debe tener 7 u 8 dígitos."

  @CN-07 @negativo @V05
  Escenario: CN-07 DNI duplicado
    Dado existe un socio con DNI "30111222"
    Cuando el usuario registra otro socio con DNI "30111222"
    Entonces el sistema muestra el mensaje "Operación rechazada": "Ya existe un socio con DNI 30111222."
    Y la grilla sigue mostrando 3 socios

  @CN-08 @negativo @R03
  Escenario: CN-08 Inhabilitar sin motivo
    Dado existe la socia "Pérez, Ana" seleccionada
    Cuando el usuario hace click en "Inhabilitar" y acepta sin motivo
    Entonces el sistema muestra el aviso "Complete el dato 'Motivo'."

  @CN-09 @negativo @R03
  Escenario: CN-09 Inhabilitar a un socio ya inhabilitado
    Dado la socia "Torres, Lía" está inhabilitada
    Cuando el usuario la inhabilita de nuevo
    Entonces el sistema muestra el mensaje "Operación rechazada": "El socio Torres, Lía ya está inhabilitado."
