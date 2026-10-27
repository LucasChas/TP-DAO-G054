# language: es
Característica: Catálogo y disponibilidad
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-07 @positivo @R04 @R05
  Escenario: CP-07 Alta de libro y de un ejemplar en una sede
    Dado existen las sedes de la red
    Cuando el usuario registra el libro "Ficciones" con ISBN "978-950-04-3046-3"
    Y el usuario selecciona el libro y registra el ejemplar "nor-0100" en "Sede Norte"
    Entonces el sistema muestra "Libro registrado." y el ISBN "9789500430463"
    Y el sistema muestra "Ejemplar registrado." y el ejemplar "NOR-0100" de "Sede Norte", "Disponible"

  @CP-08 @positivo @R13
  Escenario: CP-08 Consultar disponibilidad de un libro por sede
    Dado Rayuela tiene un ejemplar en cada sede
    Y el de Centro está prestado y el de Sur comprometido en una solicitud
    Cuando el usuario selecciona "Rayuela" y hace click en "Ver disponibilidad"
    Entonces el sistema muestra la ventana "Disponibilidad de 'Rayuela'"
    Y Centro: 1 prestado; Norte: 1 disponible; Sur: 1 prestado

  @CP-09 @positivo @R05 @R16
  Escenario: CP-09 Finalizar reparación y dar de baja un ejemplar
    Dado el ejemplar "CEN-0001" está "En reparación" por una devolución dañada
    Cuando el usuario hace click en "Finalizar reparación"
    Y el usuario hace click en "Dar de baja ejemplar" y confirma
    Entonces el sistema muestra "El ejemplar vuelve a circular." y el ejemplar queda "Disponible" / "Regular"
    Y el sistema muestra "Ejemplar dado de baja." y el ejemplar queda "Dado de baja"

  @CN-10 @negativo @R04
  Escenario: CN-10 ISBN inválido
    Dado el usuario abrió la pestaña "Catálogo"
    Cuando el usuario registra un libro con ISBN "123"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El ISBN '123' no es válido: debe tener 10 o 13 dígitos."

  @CN-11 @negativo @V06
  Escenario: CN-11 ISBN duplicado con guiones
    Dado existe Rayuela con ISBN "9789500700016"
    Cuando el usuario registra un libro con ISBN "978-950-07-0001-6"
    Entonces el sistema muestra el mensaje "Operación rechazada": "Ya existe un libro con ISBN 9789500700016."

  @CN-12 @negativo @V07
  Escenario: CN-12 Código de inventario duplicado
    Dado existe el ejemplar "CEN-0001"
    Cuando el usuario registra un ejemplar con código "cen-0001"
    Entonces el sistema muestra el mensaje "Operación rechazada": "Ya existe un ejemplar con código CEN-0001."

  @CN-13 @negativo @R05 @V09
  Escenario: CN-13 Ejemplar en una sede dada de baja
    Dado la "Sede Sur" está dada de baja
    Cuando el usuario registra un ejemplar en "Sede Sur (dada de baja)"
    Entonces el sistema muestra el mensaje "Operación rechazada": "No se pueden incorporar ejemplares a la sede 'Sede Sur' porque está dada de baja."

  @CN-14 @negativo @R04
  Escenario: CN-14 Año no numérico
    Dado el usuario abrió la pestaña "Catálogo"
    Cuando el usuario ingresa "abc" en "Año de publicación" y acepta
    Entonces el sistema muestra el aviso "'abc' no es un valor válido para 'Año de publicación'."

  @CN-15 @negativo @R04
  Escenario: CN-15 Año futuro
    Dado el usuario abrió la pestaña "Catálogo"
    Cuando el usuario ingresa el año siguiente en "Año de publicación"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El año de publicación <año> no es válido."

  @CN-16 @negativo @R05
  Escenario: CN-16 Baja de un ejemplar prestado
    Dado el ejemplar "CEN-0001" está prestado
    Cuando el usuario lo da de baja y confirma
    Entonces el sistema muestra el mensaje "Operación rechazada": "El ejemplar CEN-0001 está prestado y no se puede dar de baja."

  @CN-17 @negativo @R05
  Escenario: CN-17 Finalizar reparación de un ejemplar sano
    Dado el ejemplar "NOR-0001" está disponible
    Cuando el usuario hace click en "Finalizar reparación"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El ejemplar NOR-0001 no está en reparación."

  @CP-31 @positivo @R04
  Escenario: CP-31 Buscar libros por título o autor
    Dado el catálogo tiene Rayuela, Revista Ñ y el Diccionario de la RAE
    Cuando el usuario ingresa "rae" y hace click en "Buscar"
    Y el usuario hace click en "Ver todos"
    Entonces la grilla muestra solo "Diccionario de la lengua"
    Y la grilla vuelve a mostrar los 3 libros

  @CN-47 @negativo @R04 @V06
  Escenario: CN-47 ISBN con dígito verificador incorrecto
    Dado el usuario abrió la pestaña "Catálogo"
    Cuando el usuario registra un libro con ISBN "978-950-04-3046-7"
    Entonces el sistema muestra el mensaje "Operación rechazada": "El ISBN '978-950-04-3046-7' no es válido: el dígito verificador no corresponde."
