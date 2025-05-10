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

#Imagenes
CARPETA_IMAGENES_TEAMS = os.path.join(BASE_DIR, 'Resources', 'Images', 'TeamsLEC')
CARPETA_IMAGENES_PLAYERS = os.path.join(BASE_DIR, 'Resources', 'Images', 'PlayersLEC')
CARPETA_IMAGENES_CHAMPIONS = os.path.join(BASE_DIR, 'Resources', 'Images', 'Champions')

#Carpeta CSV
CARPETA_CSV_GAMES = os.path.join(BASE_DIR, 'Resources', 'CSV')

# Diccionarios
DICCIONARIO_CLAVES = os.path.join(BASE_DIR, 'Resources', 'Diccionary')