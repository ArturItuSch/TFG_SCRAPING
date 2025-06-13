from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import re
import time
# Establece la ruta raíz del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..','..'))
sys.path.insert(0, PROJECT_ROOT)

from .leaguepedia_teams_players import download_image, get_html
# Importación de rutas desde archivo de configuración
from Resources.rutas import *
TEAMS_INSTALATION_JSON = os.path.join(JSON_INSTALATION_TEAMS, "teams_data_leguepedia.json")
TEAMS_OLD_INSTALATION_JSON = os.path.join(JSON_INSTALATION_TEAMS, "teams_inSeson_leguepedia_data.json")

LOGO_TEAMS_PATH = os.path.join(JSON_PATH_TEAMS_LOGOS, "teams_logos_path.json")
TEAM_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_TEAMS)

# Directorios y rutas para guardar datos
BASE_URL = "https://lol.fandom.com/wiki/LoL_EMEA_Championship"

    

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
            return hrefs_filtrados          
        else:
            print("No se encontró el div con clase 'hlist'")        
    except Exception as e:
        print(f"Error al intentar consguir las urls de las sesons anteriores {e}")    

def extraer_imagen_equipo(url):
    try:
        response = get_html(url)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {url}")
            return None

        print(f"Procesando: {url}")
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', id='infoboxTeam')
        if not table:
            print("No se encontró la tabla con id='infoboxTeam'")
            return None

        tag = table.find('img')
        if tag:
            logo_url = tag.get('data-src') or tag.get('src')
            return logo_url
        else:
            print("No se encontró ninguna imagen en la tabla.")
            return None

    except Exception as e:
        print(f"Error al procesar imagen del equipo en {url}: {e}")
        return None

        
def extraer_equipos(url):
    equipos = []
    try:
        response = get_html(url)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {url}")
            return equipos

        soup = BeautifulSoup(response.text, 'html.parser')
        team_spans = soup.find_all('span', class_='team')
        season = url.strip('/').split('/')[-1]

        for team in team_spans:
            team_name_tag = team.find('span', class_='teamname')
            if not team_name_tag:
                continue

            nombre = team_name_tag.get_text(strip=True).replace(" ", "_")
            if len(nombre) <= 4:
                continue 

            team_url_relativa = team_name_tag.find('a').get('href') if team_name_tag.find('a') else None
            team_url_completa = urljoin(BASE_URL, team_url_relativa) if team_url_relativa else None
            logo_url = extraer_imagen_equipo(team_url_completa) if team_url_completa else None

            if logo_url:
                ruta_imagen = os.path.join(TEAM_IMAGES_DIR, f"{nombre}.png")
                imagen_url = download_image(ruta_imagen, logo_url)

                equipos.append({
                    'name': nombre,
                    'season': season,
                    'imagen_url': imagen_url
                })

        return equipos

    except Exception as e:
        print(f"Error al procesar equipos en {url}: {e}")
        return equipos

    
def obtener_equipos_antiguos():
    print("⏳ Obteniendo URLs de temporadas...")
    start_time = time.time()  # Iniciar temporizador

    urls = get_urls_sesons()
    if not urls:
        print("⚠️ No se encontraron URLs de temporadas.")
        return []

    total_urls = len(urls)
    equipos_totales = []
    equipos_procesados = set()
    equipos_extraidos = 0

    for url in urls:
        print(f"🔎 Procesando temporada desde URL: {url}")
        equipos = extraer_equipos(url)

        for equipo in equipos:
            nombre = equipo.get("name")
            if not nombre or nombre in equipos_procesados:
                continue

            equipos_totales.append(equipo)
            equipos_procesados.add(nombre)
            equipos_extraidos += 1
            print(f"✅ Equipo extraído: {nombre}")

    end_time = time.time()
    elapsed = end_time - start_time
    minutos, segundos = divmod(elapsed, 60)

    print("\n📋 Resumen del scraping de equipos antiguos:")
    print(f"📆 URLs de temporadas procesadas: {total_urls}")
    print(f"🏁 Total de equipos antiguos extraídos: {equipos_extraidos}")
    print(f"⏱️ Duración total del scraping: {int(minutos)} min {int(segundos)} s")

    return equipos_totales

if __name__ == "__main__":
    obtener_equipos_antiguos()