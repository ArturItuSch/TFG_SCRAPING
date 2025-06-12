"""
Resources
=========

Este módulo agrupa todos los recursos auxiliares que utiliza la aplicación, tanto para el backend como para el frontend.
Su objetivo es organizar los archivos estáticos, datos procesados y configuraciones internas necesarias para la ejecución
y desarrollo del proyecto.

Contenido de la carpeta:
------------------------

- **rutas.py**: Define rutas absolutas y relativas a los distintos recursos utilizados, facilitando el acceso desde cualquier módulo del proyecto.

- **Images/**: Contiene imágenes usadas en el frontend, como logos de equipos, iconos de campeones o imágenes de perfil.

- **Diccionary/**: Incluye archivos `.json` con información auxiliar, como claves personalizadas, ID temporales o estructuras utilizadas
  para traducir valores del scraping a identificadores válidos en la base de datos.

- **CSV/**: Almacena todos los archivos `.csv` descargados y procesados, que luego se usan en la lógica de scraping. Esta carpeta es
  clave para los módulos de `scraping.OracleElexir`.

- **JSON/**: Carpeta de uso interno para desarrollo. Contiene archivos `.json` con resultados intermedios o finales del scraping.
  Aunque no forman parte funcional del sistema, permiten inspeccionar visualmente los datos extraídos, validar consistencia y
  depurar errores durante el desarrollo.

Importancia:
------------
Este módulo no contiene lógica de negocio, pero es esencial para estructurar y mantener el acceso coherente a todos los recursos estáticos
y archivos intermedios del proyecto.
"""