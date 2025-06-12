"""
rutas.py
========

Este módulo define las rutas absolutas de los distintos recursos utilizados en el proyecto,
facilitando un acceso centralizado y coherente desde cualquier parte del código.

Variables definidas:
---------------------

- **BASE_DIR**: Ruta base del proyecto. Punto de partida para construir rutas absolutas.

### Rutas a carpetas JSON:
- **JSON_DIR**: Carpeta raíz que contiene todos los archivos `.json` auxiliares.
- **JSON_INSTALATION_PLAYERS**: Carpeta con archivos de instalación de jugadores.
- **JSON_INSTALATION_TEAMS**: Carpeta con archivos de instalación de equipos.
- **JSON_UPDATES**: Carpeta que contiene JSONs con información de actualizaciones.
- **JSON_PATH_TEAMS_LOGOS**: Subcarpeta que contiene rutas de logos de equipos.
- **JSON_PATH_PLAYERS_LOGOS**: Subcarpeta que contiene rutas de logos de jugadores.
- **JSON_GAMES**: Carpeta donde se almacenan los JSONs relacionados con partidas.
- **JSON_INSTALATION_SPLITS_LEC**: Carpeta con datos estáticos sobre splits históricos de LEC.

### Rutas a carpetas de imágenes:
- **CARPETA_IMAGENES_TEAMS**: Imágenes de los equipos (logos).
- **CARPETA_IMAGENES_PLAYERS**: Imágenes de jugadores.
- **CARPETA_IMAGENES_CHAMPIONS**: Imágenes de campeones.

### Rutas a archivos CSV:
- **CARPETA_CSV_GAMES**: Carpeta que almacena todos los archivos `.csv` con información de partidas.

### Rutas a diccionarios de claves:
- **DICCIONARIO_CLAVES**: Carpeta que contiene diccionarios `.json` usados para mapear claves,
  traducir identificadores o unificar nomenclaturas entre fuentes externas y el modelo interno.

Uso:
----
Este módulo es importado desde distintos lugares como `scraping`, `recopilador.py` y `views`,
para acceder fácilmente a los recursos sin tener que redefinir rutas o hacer referencias absolutas
de forma manual.
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# JSON 
JSON_DIR = os.path.join(BASE_DIR,'Resources', 'JSON')
JSON_INSTALATION_PLAYERS = os.path.join(JSON_DIR, 'Players')
JSON_INSTALATION_TEAMS = os.path.join(JSON_DIR, 'Teams')
JSON_UPDATES = os.path.join(JSON_DIR, 'Updates')
JSON_PATH_TEAMS_LOGOS = os.path.join(JSON_INSTALATION_TEAMS, 'Logos_PATH')
JSON_PATH_PLAYERS_LOGOS = os.path.join(JSON_INSTALATION_PLAYERS, 'Logos_PATH')
JSON_GAMES = os.path.join(JSON_DIR, 'Games')
JSON_INSTALATION_SPLITS_LEC = os.path.join(JSON_DIR, 'Splits', 'LEC')

#Imagenes
CARPETA_IMAGENES_TEAMS = os.path.join(BASE_DIR, 'Resources', 'Images', 'TeamsLEC')
CARPETA_IMAGENES_PLAYERS = os.path.join(BASE_DIR, 'Resources', 'Images', 'PlayersLEC')
CARPETA_IMAGENES_CHAMPIONS = os.path.join(BASE_DIR, 'Resources', 'Images', 'Champions')

#Carpeta CSV
CARPETA_CSV_GAMES = os.path.join(BASE_DIR, 'Resources', 'CSV')

# Diccionarios
DICCIONARIO_CLAVES = os.path.join(BASE_DIR, 'Resources', 'Diccionary')