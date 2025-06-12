"""
Resources.JSON
==============

Este paquete contiene archivos auxiliares en formato JSON que sirven exclusivamente durante la etapa de desarrollo.
Su propósito principal es visualizar, validar y depurar los datos extraídos mediante scraping antes de ser insertados
en la base de datos del proyecto.

No son utilizados en producción ni forman parte del flujo de ejecución de la aplicación web.

Estructura de subcarpetas:

- `Champions/`: Información de campeones procesados.
- `Games/`: Detalles organizados sobre partidas.
- `Players/`: Datos estructurados sobre jugadores.
- `Splits/`: Representación de los diferentes splits competitivos.
- `Teams/`: Información general y visual sobre los equipos.
- `Updates/`: Archivos con cambios incrementales o registros de actualización.

Estos archivos son de uso interno para el desarrollador. Pueden ser útiles para depuración,
seguimiento de datos y comparaciones, pero no deben considerarse parte del entorno productivo.
"""