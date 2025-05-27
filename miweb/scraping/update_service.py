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

def descargar_archivo(file_id, filename, carpeta_destino):
    URL = "https://docs.google.com/uc?export=download"
    session = requests.Session()

    response = session.get(URL, params={'id': file_id}, stream=True)

    # Buscar el token de confirmación en las cookies
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break

    if token:
        params = {'id': file_id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    filename = filename.split("_")[0] + ".csv"
    ruta_completa = os.path.join(carpeta_destino, filename)

    with open(ruta_completa, "wb") as f:
        for chunk in response.iter_content(32768):
            if chunk:
                f.write(chunk)

    print(f"{ruta_completa} descargado correctamente.")
    return ruta_completa


def descargar_todos_los_csv(api_key, folder_id, carpeta_destino):
    service = build('drive', 'v3', developerKey=api_key)

    if not os.path.exists(carpeta_destino):
        os.makedirs(carpeta_destino)

    query = f"'{folder_id}' in parents and mimeType='text/csv'"
    results = service.files().list(
        q=query,
        fields="files(id, name)",
        pageSize=1000
    ).execute()

    archivos = results.get('files', [])

    if not archivos:
        print('No se encontraron archivos CSV en la carpeta.')
        return

    print(f"Se encontraron {len(archivos)} archivo(s).")

    for archivo in archivos:
        file_id = archivo['id']
        filename = archivo['name']

        descargar_archivo(file_id, filename, carpeta_destino)
        
def borrar_csv_en_carpeta(carpeta):
    if not os.path.isdir(carpeta):
        print(f"La ruta proporcionada no es una carpeta válida: {carpeta}")
        return

    archivos = [f for f in os.listdir(carpeta) if f.endswith('.csv')]
    
    for archivo in archivos:
        ruta_archivo = os.path.join(carpeta, archivo)
        try:
            os.remove(ruta_archivo)
            print(f"✅ Archivo borrado: {ruta_archivo}")
        except Exception as e:
            print(f"❌ No se pudo borrar el archivo {ruta_archivo}: {e}")
        
def actualizar_datos_desde_ultimo_csv():
    # 1. Obtener el último CSV
    archivo = obtener_ultimo_csv(API_KEY, FOLDER_ID)
    if not archivo:
        print("❌ No se encontró ningún archivo CSV.")
        return

    print(f"📦 Último archivo: {archivo['name']} (creado: {archivo['createdTime']})")
    ruta_csv = descargar_archivo(archivo['id'], archivo['name'], CARPETA_CSV)
    filtrar_ligas_automaticamente(CARPETA_CSV, CARPETA_CSV, BASE_DIR)
    
    # 4. Procesar e importar datos
    procesar_todos_los_csvs_en_lec()
    importar_campeones()
    importar_splits()
    importar_equipos()
    importar_jugadores()
    importar_series_y_partidos()
    importar_jugadores_en_partida()
    importar_selecciones()
    importar_objetivos_neutrales()

    borrar_csv_en_carpeta(CARPETA_CSV)

    print("✅ Proceso completo de actualización desde último CSV.")
        
if __name__ == "__main__":
    #descargar_todos_los_csv(API_KEY, FOLDER_ID, CARPETA_CSV)
    #filtrar_ligas_automaticamente(CARPETA_CSV, CARPETA_CSV, BASE_DIR)    
    #borrar_csv_en_carpeta(CARPETA_CSV)  
    #procesar_todos_los_csvs_en_lec() 
    #importar_campeones()
    #importar_splits()
    #importar_equipos()
    #importar_jugadores() 
    #importar_series_y_partidos()
    #importar_jugadores_en_partida()
    importar_selecciones()
    #importar_objetivos_neutrales()    
