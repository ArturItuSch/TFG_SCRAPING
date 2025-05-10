import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import json
from pathlib import Path
import re
from datetime import datetime
import random

# Establece la ruta raíz del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..','..'))
sys.path.insert(0, PROJECT_ROOT)

# Importación de rutas desde archivo de configuración
from Resources.rutas import *

# Directorios y rutas para guardar datos
BASE_URL = "https://lol.fandom.com/wiki/LoL_EMEA_Championship"


# Encabezados para las peticiones HTTP
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

    headers_dinamicos = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": random.choice(referers),
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

    return headers_dinamicos

def get_html(url, timeout=10):
    try:
        headers = obtener_headers_dinamicos()
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        print("⚠️ Tiempo de espera agotado.")
    except requests.exceptions.TooManyRedirects:
        print("⚠️ Demasiadas redirecciones.")
    except requests.exceptions.SSLError:
        print("⚠️ Error SSL.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Error de conexión.")
    except requests.exceptions.HTTPError as err:
        print(f"⚠️ Error HTTP: {err}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error desconocido: {e}")
        

def get_urls_sesons():
    try:
        response = get_html(BASE_URL)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {BASE_URL} en get_team_links")
            return set()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='nowraplinks')
        table_body = table.find('tbody')
        div = table_body.find('div', class_='hlist')
        hrefs_filtrados = set()

        if div:
            enlaces = div.find_all('a', class_='to_hasTooltip', href=True)
            for a in enlaces:
                href = a['href']
                if re.match(r'^/wiki/(LEC|EU_LCS)/[^/]+$', href):
                    url_completa = urljoin(BASE_URL, href)
                    hrefs_filtrados.add(url_completa)
            print(hrefs_filtrados)
        else:
            print("No se encontró el div con clase 'hlist'")
        
    except Exception as e:
        print(f"Error al intentar consguir las urls de las sesons anteriores {e}")    
    
    
    
if __name__ == '__main__':
    get_urls_sesons()