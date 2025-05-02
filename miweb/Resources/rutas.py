import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(BASE_DIR,'Resources', 'JSON')

# Rutas a los recursos de la instalación
JSON_INSTALATION = os.path.join(JSON_DIR, 'Instalation')
JSON_INSTALATION_PLAYERS = os.path.join(JSON_INSTALATION, 'Players')
JSON_INSTALATION_TEAMS = os.path.join(JSON_INSTALATION, 'Teams')

JSON_PATH_TEAMS_LOGOS = os.path.join(JSON_INSTALATION_TEAMS, 'Logos_PATH')
JSON_PATH_PLAYERS_LOGOS = os.path.join(JSON_INSTALATION_PLAYERS, 'Logos_PATH')

JSON_UPDATES = os.path.join(JSON_DIR, 'Updates')

# Rutas a las carpetas de imagenes
CARPETA_IMAGENES_TEAMS = os.path.join(BASE_DIR, 'Resources', 'Images', 'TeamsLEC')
CARPETA_IMAGENES_PLAYERS = os.path.join(BASE_DIR, 'Resources', 'Images', 'PlayersLEC')

# Ruta a los csv de las partidas jugadas
CARPETA_CSV_GAMES = os.path.join(BASE_DIR, 'Resources', 'Games')