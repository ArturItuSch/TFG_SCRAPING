"""
update_service.py
=================

Este script actúa como orquestador del flujo completo de actualización e inserción de datos
para el ecosistema competitivo de League of Legends (LEC).

Responsabilidades principales:
- Gestiona la conexión a Google Drive mediante una API Key para descargar archivos CSV.
- Permite la descarga del último archivo o de todos los existentes en la carpeta remota.
- Aplica procesos de filtrado y limpieza de ligas automáticamente (usando funciones de `csv_process.py`).
- Llama a todas las funciones de inserción de datos (campeones, splits, series, partidos, selecciones, etc.).
- Ejecuta tareas de mantenimiento como eliminación de archivos temporales una vez procesados.

Funciones destacadas:
- `actualizar_datos_desde_ultimo_csv()`: Automatiza la descarga, procesamiento e inserción de datos del último CSV.
- `insertar_datos_base()`: Carga inicial del proyecto con todos los datos necesarios.
- `insertar_datos_base_descargaCSV()`: Variante que primero descarga todos los CSV antes de insertar.

Dependencias:
- Variables de entorno `GOOGLE_API_KEY` y `GOOGLE_DRIVE_FOLDER_ID`.
- Scrapers funcionales previos para campeones y Leaguepedia.
- Módulos auxiliares: `csv_process.py`, `recopilador.py`, `import_data.py`.

Este archivo se puede utilizar desde comandos Django, ejecutarse en tareas programadas o invocarse directamente 
en scripts de despliegue inicial del entorno.
"""
# Librerías estándar y externas utilizadas
from googleapiclient.discovery import build
from dotenv import load_dotenv
import requests
import os
import sys


# Definición de directorios clave y rutas del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

# Carga las variables de entorno definidas en el archivo .env.dev
load_dotenv(os.path.join(BASE_DIR, '.env.dev'))
# Obtiene la clave de API de Google desde las variables de entorno
API_KEY = os.getenv('GOOGLE_API_KEY')
# Obtiene el ID de la carpeta de Google Drive desde las variables de entorno
FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
# Verifica que la clave de API esté definida; si no, lanza una excepción
if not API_KEY:
    raise Exception("No se ha definido la variable de entorno GOOGLE_API_KEY")
# Verifica que el ID de la carpeta esté definido; si no, lanza una excepción
if not FOLDER_ID:
    raise Exception("No se ha definido la variable de entorno GOOGLE_DRIVE_FOLDER_ID")

# Importación de las distintas funciones para la importación de los datos
from scraping.OracleElexir.csv_process import *
from scraping.recopilador import *
from scraping.Leaguepedia.import_data import actualizar_todo_equipos_y_jugadores
from Resources.rutas import CARPETA_CSV_GAMES
# Define la ruta final a la carpeta donde se trabajará con los CSV descargados
CARPETA_CSV = os.path.join(CARPETA_CSV_GAMES)

def obtener_ultimo_csv(api_key, folder_id):
    """
    Recupera el archivo CSV más reciente de una carpeta de Google Drive.

    Parameters:
        api_key (str): Clave de API de Google para autenticar la solicitud.
        folder_id (str): ID de la carpeta en Google Drive desde la que se desea obtener el CSV.

    Returns:
        dict | None: Diccionario con información del archivo más reciente (id, name, createdTime),
                     o None si no se encuentra ningún archivo válido.
    """
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
    """
    Descarga un archivo CSV desde Google Drive utilizando su ID y lo guarda en una carpeta local.

    Parameters:
        file_id (str): ID del archivo en Google Drive.
        filename (str): Nombre original del archivo (se ajustará al año en el nombre).
        carpeta_destino (str): Ruta del directorio local donde se almacenará el archivo descargado.

    Returns:
        str: Ruta completa del archivo descargado.

    Nota:
        Este método gestiona automáticamente los tokens de confirmación de Google
        para archivos de gran tamaño o compartidos públicamente.
    """
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
    """
    Descarga todos los archivos CSV disponibles en una carpeta de Google Drive especificada.

    Parameters:
        api_key (str): Clave de API de Google utilizada para autenticar el acceso a la API de Drive.
        folder_id (str): ID de la carpeta en Google Drive desde donde se descargarán los archivos.
        carpeta_destino (str): Ruta local del directorio donde se guardarán los archivos descargados.

    Returns:
        None

    Detalles:
        - Se asegura de que la carpeta destino exista, creándola si es necesario.
        - Recupera hasta 1000 archivos por solicitud.
        - Llama a `descargar_archivo` por cada archivo encontrado.
    """
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
    """
    Elimina todos los archivos CSV dentro de una carpeta específica.

    Parameters:
        carpeta (str): Ruta del directorio donde se buscarán y eliminarán los archivos con extensión `.csv`.

    Returns:
        None

    Detalles:
        - Verifica si la ruta especificada es una carpeta válida.
        - Recorre todos los archivos con extensión `.csv` y los elimina.
        - Imprime un mensaje de éxito por cada archivo eliminado, o un mensaje de error si ocurre un fallo.
    """
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
    """
    Descarga y procesa automáticamente el último archivo CSV disponible en Google Drive,
    filtrando e importando los datos de la liga LEC a la base de datos.

    Esta función es utilizada tanto manualmente como desde el scheduler definido en 
    `scraping.apps.ScrapingConfig`.

    Pasos del proceso:
    1. Obtiene el archivo CSV más reciente en la carpeta de Google Drive configurada.
    2. Descarga el archivo y lo guarda en la carpeta local.
    3. Filtra los datos automáticamente para aislar los registros de la LEC.
    4. Ejecuta en orden todas las funciones de importación:
       - `procesar_todos_los_csvs_en_lec`
       - `importar_splits`
       - `importar_equipos`
       - `importar_jugadores`
       - `importar_series_y_partidos`
       - `importar_jugadores_en_partida`
       - `importar_selecciones`
       - `importar_objetivos_neutrales`
    5. Elimina los archivos CSV descargados una vez procesados.

    Returns:
        None
    """
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
    importar_splits()
    importar_equipos()
    importar_jugadores()
    importar_series_y_partidos()
    importar_jugadores_en_partida()
    importar_selecciones()
    importar_objetivos_neutrales()

    borrar_csv_en_carpeta(CARPETA_CSV)

    print("✅ Proceso completo de actualización desde último CSV.")
    
def insertar_datos_base():
    """
    Inserta los datos base del proyecto LEC en la base de datos a partir de los CSV ya procesados.

    Esta función debe ser utilizada cuando los archivos CSV ya han sido previamente filtrados
    y convertidos en estructuras válidas dentro del proyecto. Es especialmente útil en
    entornos donde los datos ya están listos y solo se desea realizar la carga inicial.

    Operaciones realizadas:
    - Inserta campeones desde el sitio GOL (`importar_campeones`).
    - Inserta splits disponibles (`importar_splits`).
    - Inserta equipos detectados (`importar_equipos`).
    - Inserta jugadores y los asocia a sus equipos (`importar_jugadores`).
    - Inserta series y partidos (`importar_series_y_partidos`).
    - Inserta estadísticas detalladas de jugadores (`importar_jugadores_en_partida`).
    - Inserta picks y bans por partida (`importar_selecciones`).
    - Inserta objetivos neutrales obtenidos por los equipos (`importar_objetivos_neutrales`).
    - Actualiza información histórica y activa de equipos y jugadores (`actualizar_todo_equipos_y_jugadores`).

    Returns:
        None
    """
    importar_campeones()
    importar_splits()
    importar_equipos()
    importar_jugadores() 
    importar_series_y_partidos()
    importar_jugadores_en_partida()
    importar_selecciones()
    importar_objetivos_neutrales() 
    actualizar_todo_equipos_y_jugadores()
    
def insertar_datos_base_descargaCSV():
    """
    Descarga y procesa todos los datos necesarios desde Google Drive para luego insertarlos en la base de datos.

    Esta función está pensada para ser utilizada desde un comando personalizado de Django cuando se requiere
    poblar completamente el sistema desde cero. Incluye la descarga de todos los CSVs originales, su filtrado,
    limpieza y posterior importación a los modelos de la base de datos.

    Pasos realizados:
    1. Descarga todos los CSVs desde Google Drive (`descargar_todos_los_csv`).
    2. Filtra automáticamente los archivos para dejar solo los relevantes (`filtrar_ligas_automaticamente`).
    3. Elimina los CSVs ya procesados para evitar duplicidad (`borrar_csv_en_carpeta`).
    4. Procesa los CSVs filtrados y extrae los datos en formato estructurado (`procesar_todos_los_csvs_en_lec`).
    5. Inserta los campeones obtenidos desde GOL (`importar_campeones`).
    6. Inserta splits (`importar_splits`).
    7. Inserta equipos (`importar_equipos`).
    8. Inserta jugadores (`importar_jugadores`).
    9. Inserta series y partidos (`importar_series_y_partidos`).
    10. Inserta estadísticas por jugador (`importar_jugadores_en_partida`).
    11. Inserta selecciones y baneos (`importar_selecciones`).
    12. Inserta objetivos neutrales (`importar_objetivos_neutrales`).
    13. Actualiza estado y datos históricos de equipos y jugadores (`actualizar_todo_equipos_y_jugadores`).

    Returns:
        None
    """
    descargar_todos_los_csv(API_KEY, FOLDER_ID, CARPETA_CSV)
    filtrar_ligas_automaticamente(CARPETA_CSV, CARPETA_CSV, BASE_DIR)    
    borrar_csv_en_carpeta(CARPETA_CSV)  
    procesar_todos_los_csvs_en_lec() 
    importar_campeones()
    importar_splits()
    importar_equipos()
    importar_jugadores() 
    importar_series_y_partidos()
    importar_jugadores_en_partida()
    importar_selecciones()
    importar_objetivos_neutrales()  
    actualizar_todo_equipos_y_jugadores()
  
        
   
