from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests
import os
import sys

load_dotenv()

API_KEY = os.getenv('GOOGLE_API_KEY')
FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

if not API_KEY:
    raise Exception("No se ha definido la variable de entorno GOOGLE_API_KEY")

if not FOLDER_ID:
    raise Exception("No se ha definido la variable de entorno GOOGLE_DRIVE_FOLDER_ID")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from scraping.OracleElexir.csv_process import *
from Resources.rutas import CARPETA_CSV_GAMES
from scraping.main import *

CARPETA_CSV = os.path.join(CARPETA_CSV_GAMES)

def obtener_ultimo_csv(api_key, folder_id):
    service = build('drive', 'v3', developerKey=api_key)

    query = f"'{folder_id}' in parents and mimeType='text/csv'"

    results = service.files().list(
        q=query,
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc"
    ).execute()

    archivos = results.get('files', [])

    if not archivos:
        print('No se encontraron archivos CSV en la carpeta.')
        return None

    return archivos[0]

def borrar_archivo_csv(ruta_archivo):
    if os.path.exists(ruta_archivo) and ruta_archivo.endswith('.csv'):
        try:
            os.remove(ruta_archivo)
            print(f"Archivo borrado: {ruta_archivo}")
        except Exception as e:
            print(f"No se pudo borrar el archivo {ruta_archivo}: {e}")
    else:
        print(f"El archivo no existe o no es un CSV: {ruta_archivo}")
        
def descargar_archivo(file_id, filename, carpeta_destino):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    respuesta = requests.get(url)
    filename = filename.split("_")[0] + ".csv"
    if respuesta.status_code == 200:
        ruta_completa = os.path.join(carpeta_destino, filename)
        with open(ruta_completa, 'wb') as f:
            f.write(respuesta.content)
        print(f"{ruta_completa} descargado correctamente.")
        return ruta_completa
    else:
        print("Error al descargar el archivo.")

if __name__ == "__main__":
    archivo = obtener_ultimo_csv(API_KEY, FOLDER_ID)
    if archivo:
        print(f"Archivo más reciente: {archivo['name']} (creado: {archivo['createdTime']})")
        archivo_descargado = descargar_archivo(archivo['id'], archivo['name'], CARPETA_CSV_GAMES)
    if archivo_descargado: 
        filtrar_ligas_automaticamente(CARPETA_CSV, CARPETA_CSV, BASE_DIR)
        borrar_archivo_csv(archivo_descargado)
        procesar_todos_los_csvs_en_lec()
        limpiar_playerid_en_todos_los_csvs()
        importar_campeones()
        importar_splits()
        importar_equipos()
        importar_jugadores() 
        importar_series_y_partidos()
        importar_jugadores_en_partida()
        importar_selecciones()
        importar_objetivos_neutrales()