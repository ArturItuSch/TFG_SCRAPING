import pandas as pd
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, PROJECT_ROOT)

from Resources.rutas import *

CARPETA_CSV = os.path.join(CARPETA_CSV_GAMES)
CARPETA_CSV_LEC = os.path.join(CARPETA_CSV, 'LEC')
archivos_CSV = [
    os.path.relpath(os.path.join(CARPETA_CSV, archivo), start=PROJECT_ROOT)
    for archivo in os.listdir(CARPETA_CSV)
    if archivo.endswith('.csv') and os.path.isfile(os.path.join(CARPETA_CSV, archivo))
]
    
# Cargar el archivo CSV
for archivo in archivos_CSV:
    ruta_absoluta = os.path.join(PROJECT_ROOT, archivo)
    df = pd.read_csv(ruta_absoluta, dtype={2: str})
    lec_matches = df[df['league'] == 'LEC']
    nombre_base = os.path.splitext(os.path.basename(archivo))[0]
    lec_matches.to_csv(os.path.join(CARPETA_CSV_LEC, f"{nombre_base}_LEC.csv"), index=False)