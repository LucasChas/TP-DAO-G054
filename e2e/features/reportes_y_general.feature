# language: es
Característica: Reportes y general
  Pruebas E2E sobre la interfaz gráfica real (Tkinter). Implementación: e2e/test_e2e_*.py

  @CP-26 @positivo @P04
  Escenario: CP-26 Cargar datos de ejemplo
    Dado la base está vacía
    Cuando el usuario elige "Archivo" > "Cargar datos de ejemplo"
    Entonces el sistema muestra "Se cargaron los datos de ejemplo."
    Y hay 3 sedes y 4 remitos

  @CP-27 @positivo @P02
  Escenario: CP-27 Ver y exportar los cinco reportes a PDF y CSV
    Dado se cargaron los datos de ejemplo
    Cuando el usuario abre cada reporte y hace click en los dos botones de exportación
    Entonces el sistema muestra "Reporte exportado en: <ruta>"
    Y se generan 10 archivos no vacíos "reporte_<clave>_<fecha>"

  @CP-28 @positivo @P02
  Escenario: CP-28 Filtrar por rango de fechas
    Dado se cargaron los datos de ejemplo
    Cuando el usuario ingresa 01/01/2000 a 31/12/2000 y abre "4. Movimiento entre sedes"
    Entonces el sistema muestra "Tiempo promedio de tránsito en la red: -"

  @CN-41 @negativo @P02
  Escenario: CN-41 Fecha inválida en el filtro
    Dado el usuario abrió "Reportes"
    Cuando el usuario ingresa "32/13/2026" en "Desde" y abre "3. Libros más solicitados"
    Entonces el sistema muestra el aviso "'32/13/2026' no es una fecha válida (dd/mm/aaaa)."

  @CN-42 @negativo @P04
  Escenario: CN-42 Cargar datos de ejemplo dos veces
    Dado ya se cargaron los datos de ejemplo
    Cuando el usuario elige "Archivo" > "Cargar datos de ejemplo"
    Entonces el sistema muestra el aviso "La base ya tiene datos; no se cargó nada."

  @CP-29 @positivo @R01 @P04
  Escenario: CP-29 Interfaz de consola: cargar datos y listar sedes
    Dado se ejecuta "python main.py" sobre una base vacía
    Cuando el usuario elige 10 (datos de ejemplo), 1 > 1 (listar sedes) y 0 para salir
    Entonces la salida muestra "Se cargaron los datos de ejemplo.", la tabla "Sedes de la red" y "¡Hasta luego!"

  @CN-43 @negativo @R03
  Escenario: CN-43 Consola: opción inválida y DNI inválido
    Dado se ejecuta "python main.py"
    Cuando el usuario elige 99 y después registra un socio con DNI "12ab"
    Entonces la salida muestra "Opción inválida." y "El DNI '12ab' no es válido: debe tener 7 u 8 dígitos."
    Y el programa termina normalmente con "¡Hasta luego!"
