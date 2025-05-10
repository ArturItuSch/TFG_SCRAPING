import os
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin
import time
import sys

# Ubiciaciones de los archivos json:
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, BASE_DIR)
JSON_DIR = os.path.join(BASE_DIR, "scraping", "JSON")
JSON_INSTALATION = os.path.join(JSON_DIR, "Instalation")
JSON_UPDATES = os.path.join(JSON_DIR, "Updates")

# Si los directorios existen
os.makedirs(JSON_INSTALATION, exist_ok=True)
os.makedirs(JSON_UPDATES, exist_ok=True)

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
        
def get_team_data(driver):
    driver.get("https://gol.gg/teams/list/season-ALL/split-ALL/tournament-LEC%202025%20Spring%20Season/")
    time.sleep(2)
    try:
        team_data=[]
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )

        # Obtener todas las filas de la tabla, excluyendo la cabecera
        rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 7:
               team = {
                "nombre": cells[0].text.strip(),
                "win_rate": cells[1].text.strip(),
                "kda": cells[2].text.strip(),
                "game_duration": cells[3].text.strip(),
                "gpm": cells[4].text.strip(),
                "dpm": cells[5].text.strip(),
                "wpm": cells[6].text.strip(),
            }
            team_data.append(team)
        print("✅ Tabla extraída correctamente.")
        return team_data
    except Exception as e:
        print("❌ Error al extraer la tabla:", e)
        
def guardar_json(data, directory):
    try:
        with open(directory, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ Archivo guardado correctamente en: {directory}")
    except Exception as e:
        print(f"❌ Error al guardar el archivo JSON: {e}")
        
def cargar_json(directory):
    try:
        with open(directory, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Archivo cargado correctamente desde: {directory}")
        return data
    except Exception as e:
        print(f"❌ Error al cargar el archivo JSON: {e}")
        return None
