import os
import random
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import time
import sys
import requests
import re
import uuid

# Ubiciaciones de los archivos json:
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, BASE_DIR)
from scraping.driver import iniciar_driver
from Resources.rutas import *

JSON_DIR = os.path.join(BASE_DIR, "Resources", "JSON")
CHAMPIONS_FOLDER_PATH = os.path.join(BASE_DIR, CARPETA_IMAGENES_CHAMPIONS)
CHAMPION_DICCIONARIY_ID = os.path.join(BASE_DIR, DICCIONARIO_CLAVES, "champions_ids.json")

BASE_URL = "https://gol.gg"
CHAMPIONS_URL = "https://gol.gg/champion/list/season-S15/split-Spring/tournament-ALL/sort-1/"

# Encabezados para las peticiones HTTP
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1", 
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Si deseas cambiar el "Referer" o el "User-Agent" de forma dinámica
def obtener_headers_dinamicos():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/112.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/112.0"
    ]
    
    referers = [
        "https://www.google.com/",
        "https://www.bing.com/",
        "https://www.yahoo.com/"
    ]
    
    headers["User-Agent"] = random.choice(user_agents)
    headers["Referer"] = random.choice(referers)
    
    return headers
        
def accept_cookies(driver):
    try:
        driver.get("https://gol.gg/esports/home/")
        time.sleep(5)
        agree_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.fc-cta-consent"))
        )
        agree_button.click()
        print("Cookies aceptadas.")
    except Exception as e:
        print("No se pudo aceptar cookies:", e)

def crear_carpeta(ruta_carpeta):
    try:
        os.makedirs(ruta_carpeta, exist_ok=True)
        print(f"Carpeta creada o ya existente: {ruta_carpeta}")
    except Exception as e:
        print(f"Error al crear la carpeta '{ruta_carpeta}': {e}")
        
def download_image(ruta_local, url_imagen):
    try:
        headers = obtener_headers_dinamicos()
        response = requests.get(url_imagen, headers=headers, stream=True)
        response.raise_for_status()
        with open(ruta_local, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        time.sleep(random.uniform(1,2))
        print(f"Imagen: {url_imagen} descargada correctamente en {ruta_local}")
        ruta_relativa = os.path.relpath(ruta_local, start=os.getcwd())
        return ruta_relativa
    except Exception as e:
        print(f"Error al descargar la imagen: {e}")
        time.sleep(random.uniform(1,2))
        return None

def get_champions_information(driver):
    champions = []
    try:
        driver.get(CHAMPIONS_URL)

        # Espera a que se cargue la tabla
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table_list"))
        )

        response = driver.page_source
        soup = BeautifulSoup(response, 'html.parser')
        table = soup.find('table', class_='table_list')

        if table:
            tbody = table.find('tbody')
            rows = tbody.find_all('tr') if tbody else []

            for row in rows:
                try:
                    img = row.find('img', class_='champion_icon_light')
                    if not img:
                        continue
                    
                    nombre = re.sub(r'[\\/*?:"<>|]', "", img['alt'])   
                    url_relativa = img['src']

                    champion = {
                        'nombre': nombre,
                        'ruta_imagen': None
                    }

                    if not url_relativa.startswith("/"):
                        url_relativa = "/" + url_relativa
                        crear_carpeta(os.path.join(CHAMPIONS_FOLDER_PATH, nombre))
                        ruta_local = os.path.join(os.path.join(CHAMPIONS_FOLDER_PATH, nombre), f"{nombre}.png")
                        url_absoluta = urljoin(BASE_URL, url_relativa)
                        champion["ruta_imagen"] = download_image(ruta_local, url_absoluta)
                    else:
                        print(f"No se encontró la imagen de {nombre}")

                    champions.append(champion)

                except Exception as e:
                    print(f"Error procesando fila: {e}")
                    continue
        else:
            print("No se encontró la tabla.")
    except Exception as e:
        print(f"Error inesperado: {e}")
    return champions

def verificar_existencia_imagen(nombre_campeon, ruta_json):
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        for champ in datos:
            if champ.get("nombre", "").lower() == nombre_campeon.lower():
                ruta = champ.get("ruta_imagen")
                if ruta:
                    if os.path.exists(ruta):
                        print(f"✅ El archivo de {nombre_campeon} existe en: {ruta}")
                        return True
                    else:
                        print(f"❌ El archivo de {nombre_campeon} NO existe en: {ruta}")
                        return False
                else:
                    print(f"{nombre_campeon} no tiene ruta asignada.")
                    return False

        print(f"{nombre_campeon} no se encuentra en el JSON.")
        return False

    except Exception as e:
        print(f"Error al verificar la imagen: {e}")
        return False
    
if __name__ == '__main__':
    driver = iniciar_driver()
    try:
        champions = get_champions_information(driver)
        #verificar_existencia_imagen("Nami", os.path.join(JSON_CHAMPIONS_INSTALATION, 'champions.json'))
    finally:
        driver.quit()