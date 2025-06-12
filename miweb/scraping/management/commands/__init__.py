"""
Módulo `scraping.management.commands`

Este paquete contiene comandos personalizados de Django relacionados con el scraping y la inserción
de datos históricos o base en el proyecto de estadísticas de la LEC.

Comandos disponibles:
---------------------
- `update_historic_teams.py`: 
    Comando manual que recopila y actualiza en la base de datos todos los equipos históricos de Leaguepedia.
    Extrae equipos de temporadas pasadas, descarga sus logos y actualiza su estado como inactivos (`activo=False`).

- `insertar_datos_base.py`:
    Comando automatizado que se ejecuta al iniciar el sistema desde cero. Inserta todos los datos base
    necesarios para el funcionamiento inicial del proyecto, incluyendo equipos, jugadores y estadísticas fundamentales.

Uso general:
-------------
Estos comandos se ejecutan desde la terminal con:

    python manage.py <nombre_del_comando>

Y permiten mantener sincronizada la base de datos con los datos extraídos desde fuentes externas como Leaguepedia.
"""