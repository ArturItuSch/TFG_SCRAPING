"""
Resources.Images
================

Este paquete contiene todos los recursos visuales utilizados por la aplicación, organizados en subcarpetas
según su categoría y origen. Las imágenes pueden haber sido obtenidas mediante scraping automatizado o añadidas manualmente.

Estructura de subcarpetas:

- `Champions/`: Imágenes de campeones utilizadas en estadísticas y visualizaciones de partidas.
- `PlayersLEC/`: Fotografías de jugadores activos e históricos de la liga LEC.
- `TeamsLEC/`: Logos e insignias de los equipos que han participado en la LEC.
- `Others/`: Imágenes misceláneas u otros recursos no categorizados directamente.

Las subcarpetas `PlayersLEC/` y `TeamsLEC/` incluyen el sufijo "LEC" para facilitar futuras extensiones
del sistema a otras ligas, permitiendo mantener una estructura modular y escalable.

Estas imágenes se emplean tanto en el frontend (para mejorar la experiencia visual del usuario)
como en tareas de validación durante el scraping y la inserción de datos.
"""