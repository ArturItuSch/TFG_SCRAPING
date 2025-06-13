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
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
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

def cargar_diccionario_ids():
    if os.path.exists(CHAMPION_DICCIONARIY_ID):
        with open(CHAMPION_DICCIONARIY_ID, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def guardar_diccionario_ids(diccionario):
    with open(CHAMPION_DICCIONARIY_ID, "w", encoding="utf-8") as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=4)


def download_image(ruta_local, url_imagen):
    try:
        if not url_imagen:
            return None

        if os.path.exists(ruta_local):
            print(f"⚠️ Imagen ya existente, se omite descarga: {ruta_local}")
        else:
            headers = obtener_headers_dinamicos()
            response = requests.get(url_imagen, headers=headers, stream=True)
            response.raise_for_status()

            with open(ruta_local, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            time.sleep(random.uniform(1, 2))
            print(f"✅ Imagen descargada: {ruta_local}")

        partes = ruta_local.split(os.sep)
        if "Resources" in partes:
            idx = partes.index("Resources")
            ruta_relativa = os.path.join(*partes[idx + 1:])
        else:
            ruta_relativa = os.path.relpath(ruta_local, start=os.getcwd())

        # Convertir a estilo URL con /
        ruta_relativa = ruta_relativa.replace("\\", "/")
        return ruta_relativa

    except Exception as e:
        print(f"❌ Error al descargar la imagen: {e}")
        time.sleep(random.uniform(1, 2))
        return None

    except Exception as e:
        print(f"❌ Error al descargar la imagen: {e}")
        time.sleep(random.uniform(1, 2))
        return None

def get_champions_information(driver):
    champions = []
    ids_existentes = cargar_diccionario_ids()
    nuevos_ids = False
    total_campeones = 0
    campeones_exitosos = 0

    print("⏳ Iniciando scraping de campeones...")
    start_time = time.time()  # ⏱️ Inicia el temporizador

    try:
        driver.get(CHAMPIONS_URL)

        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table_list"))
        )

        response = driver.page_source
        soup = BeautifulSoup(response, 'html.parser')
        table = soup.find('table', class_='table_list')

        if not table:
            print("❌ No se encontró la tabla de campeones.")
            return champions

        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else []

        total_campeones = len(rows)
        print(f"🔍 Detectados {total_campeones} campeones en la tabla...")

        for row in rows:
            try:
                img = row.find('img', class_='champion_icon_light')
                if not img:
                    continue

                nombre = re.sub(r'[\\/*?:"<>|]', "", img['alt'])
                if nombre in ids_existentes:
                    champ_id = ids_existentes[nombre]
                else:
                    champ_id = str(uuid.uuid4())
                    ids_existentes[nombre] = champ_id
                    nuevos_ids = True

                url_relativa = img['src']
                champion = {
                    'id': champ_id,
                    'nombre': nombre,
                    'ruta_imagen': None
                }

                nombre_archivo = f"{nombre}.png"
                ruta_local = os.path.join(CHAMPIONS_FOLDER_PATH, nombre_archivo)

                # Asegurar que la URL sea válida
                if not url_relativa.startswith("http"):
                    url_relativa = url_relativa if url_relativa.startswith("/") else "/" + url_relativa
                    url_absoluta = urljoin(BASE_URL, url_relativa)
                else:
                    url_absoluta = url_relativa

                ruta_relativa = download_image(ruta_local, url_absoluta)
                if ruta_relativa:
                    champion["ruta_imagen"] = ruta_relativa
                    campeones_exitosos += 1
                    print(f"✅ Campeón {nombre} procesado correctamente.")
                else:
                    print(f"⚠️ No se pudo descargar la imagen de {nombre}")

                champions.append(champion)

            except Exception as e:
                print(f"⚠️ Error procesando fila: {e}")
                continue

    except Exception as e:
        print(f"🔥 Error inesperado: {e}")

    if nuevos_ids:
        guardar_diccionario_ids(ids_existentes)

    end_time = time.time()
    elapsed = end_time - start_time
    minutos, segundos = divmod(elapsed, 60)

    print("\n📋 Resumen del scraping de campeones:")
    print(f"🏆 Campeones detectados: {total_campeones}")
    print(f"✔️ Campeones procesados correctamente: {campeones_exitosos}")
    print(f"❌ Fallos de extracción: {total_campeones - campeones_exitosos}")
    print(f"⏱️ Duración total del scraping: {int(minutos)} min {int(segundos)} s")

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
        for champion in champions:
            print(f"Campeón: {champion['nombre']}, ID: {champion['id']}, Ruta Imagen: {champion['ruta_imagen']}")
        #verificar_existencia_imagen("Nami", os.path.join(JSON_CHAMPIONS_INSTALATION, 'champions.json'))
    finally:
        driver.quit()