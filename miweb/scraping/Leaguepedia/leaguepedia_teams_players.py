import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import re
from datetime import datetime
import random
import time
# Establece la ruta raíz del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..'))
sys.path.insert(0, PROJECT_ROOT)

# Importación de rutas desde archivo de configuración
from Resources.rutas import *

# Directorios y rutas para guardar datos
TEAM_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_TEAMS)
PLAYER_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_PLAYERS)
PLAYER_INSTALATION_DATA = os.path.join(JSON_INSTALATION_PLAYERS, "players_data_leguepedia.json")
TEAMS_INSTALATION_JSON = os.path.join(JSON_INSTALATION_TEAMS, "teams_data_leguepedia.json")
LOGO_TEAMS_PATH = os.path.join(JSON_PATH_TEAMS_LOGOS, "teams_logos_path.json")


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

def convertir_fecha(fecha_str):
    try:
        fecha_limpia = re.sub(r'\(.*?\)', '', fecha_str).strip()
        fecha = datetime.strptime(fecha_limpia, "%B %d, %Y")
        return fecha.strftime("%Y-%m-%d")
    except ValueError:
        return None
    except Exception as e:
        print(f"Error al convertir la fecha: {e}")
        return None


def get_html(url, timeout=10):
    try:
        time.sleep(1)
        headers = obtener_headers_dinamicos()
        response = requests.get(url, headers=headers)
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

# Conseguir los enlaces de los equipos de la LEC 2025 Spring Season
def get_team_links(url):
    base_url = 'https://lol.fandom.com/'
    try:
        response = get_html(url, headers)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {url} en get_team_links")
            return set()

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', class_='catlink-teams')
        urls = set()
        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                urls.add(full_url)

        return urls

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a {url}: {e}")
        return set()
    except Exception as e:
        print(f"Error inesperado al procesar los enlaces del equipo: {e}")
        return set()

# Conseguir los datos específicos de los jugadores
def get_extra_player_data(url):
    try:
        response = get_html(url, headers)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {url} en get_player_data")
            return None
        player_data = {}
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            table = soup.find('table', id = 'infoboxPlayer')
            if not table:
                print(f"No se encontró la tabla de información del jugador en: {url}")
                return None
            player_data = {}
            rows = table.find_all('tr')
            # Obtener imagen del jugador (una sola vez)
            img_link_tag = table.find('a', class_='image')
            if img_link_tag and img_link_tag.has_attr('href'):
                player_image = download_image(os.path.join(PLAYER_IMAGES_DIR, f"{url.split('/')[-1]}.png"), img_link_tag['href'])
                if player_image is not None:
                    player_data['image'] = player_image
                else:
                    print(f"Error al descargar la imagen del jugador: {url}")
                    player_data['image'] = None
            else:
                print(f"No se encontró la imagen del jugador en: {url}")
                player_data['image'] = None

            for row in rows:
                # Conseguir el cumpleaños del jugador y sus nicknames de SoloQ
                cells = row.find_all('td')
                if len(cells) == 2:
                    label = cells[0].get_text(strip=True)
                    if label == "Birthday":
                        birthday_text = cells[1].get_text(strip=True)
                        player_data['birthday'] = convertir_fecha(birthday_text)
                        continue
                    elif label == "Soloqueue IDs":
                        entries = []
                        bold_tags = cells[1].find_all('b')
                        for b in bold_tags:
                            region = b.get_text(strip=True).replace(':', '')
                            nickname = b.next_sibling.strip() if b.next_sibling else ''
                            entries.append(f"{region}: {nickname}")
                        player_data['soloqueue_ids'] = ', '.join(entries)
                        continue              
        except Exception as e:
            print(f"Error al procesar la tabla de información del jugador: {e}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a {url}: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al procesar los datos del jugador: {e}")
        return None
    return player_data
                                 
            

def get_player_data():
    all_player_data = []
    urls = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")
    total_urls = len(urls)
    total_jugadores = 0
    jugadores_exitosos = 0

    if not urls:
        print("❌ No se encontraron URLs de equipos.")
        return []

    print(f"🔍 Consultando datos de {total_urls} equipos...")
    start_time = time.time()  # ⏱️ Inicia el temporizador

    for url in urls:
        try:
            response = get_html(url, headers)
            if response is None:
                print(f"❌ No se pudo obtener respuesta de la URL: {url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            tabla = soup.find('table', class_='team-members')
            if not tabla:
                print(f"❌ No se encontró la tabla de miembros en: {url}")
                continue

            tbody = tabla.find('tbody')
            if not tbody:
                print(f"❌ No se encontró el cuerpo de la tabla en: {url}")
                continue

            rows = tbody.find_all('tr')

            for row in rows:
                celdas = row.find_all('td')
                if len(celdas) < 7:
                    continue

                total_jugadores += 1
                try:
                    residencia = celdas[0].get_text(strip=True)
                    pais = celdas[1].find('span')['title'] if celdas[1].find('span') else ''
                    jugador = celdas[2].get_text(strip=True)
                    nombre_real = celdas[3].get_text(strip=True)
                    rol = celdas[4].find('span', class_='markup-object-name').get_text(strip=True)
                    contrato = celdas[5].get_text(strip=True)
                    spans = celdas[6].find_all('span')
                    fecha_union = spans[1].get_text(strip=True) if len(spans) > 1 else ''

                    enlace_tag = celdas[2].find('a')
                    url_relativa = enlace_tag['href'] if enlace_tag else ''
                    url_jugador = urljoin('https://lol.fandom.com', url_relativa)
                    datos_complementarios = get_extra_player_data(url_jugador) or {}

                    miembro = {
                        'jugador': jugador,
                        'nombre': nombre_real,
                        'residencia': residencia,
                        'rol': rol,
                        'equipo': re.sub(r'\s*\(.*?\)\s*', '', url.split('/')[-1].replace('_', ' ').replace('Season', '').strip()),
                        'pais': pais,
                        'nacimiento': datos_complementarios.get('birthday'),
                        'soloqueue_ids': datos_complementarios.get('soloqueue_ids'),
                        'contratado_hasta': contrato,
                        'contratado_desde': fecha_union,
                        'imagen': datos_complementarios.get('image'),
                    }

                    all_player_data.append(miembro)
                    jugadores_exitosos += 1
                    print(f"✅ Jugador extraído correctamente: {jugador}")

                except Exception as e:
                    print(f"⚠️ Error al procesar jugador: {e}")
                    continue

        except requests.exceptions.RequestException as e:
            print(f"🌐 Error de red en {url}: {e}")
            continue

        except Exception as e:
            print(f"🔥 Error inesperado al procesar URL {url}: {e}")
            continue

    end_time = time.time()
    elapsed = end_time - start_time
    minutos, segundos = divmod(elapsed, 60)

    print("\n📋 Resumen del scraping:")
    print(f"🔗 URLs consultadas: {total_urls}")
    print(f"👥 Total de jugadores detectados: {total_jugadores}")
    print(f"✔️ Jugadores extraídos correctamente: {jugadores_exitosos}")
    print(f"❌ Fallos de extracción: {total_jugadores - jugadores_exitosos}")
    print(f"⏱️ Duración total del scraping: {int(minutos)} min {int(segundos)} s")

    return all_player_data


def download_image(ruta_completa, url_imagen):
    try:
        if os.path.exists(ruta_completa):
            print(f"Imagen ya existe en {ruta_completa}, se omite la descarga.")
        else:
            print(f"Descargando imagen desde {url_imagen} a {ruta_completa}...")
            img_data = requests.get(url_imagen, timeout=10)
            img_data.raise_for_status()
            with open(ruta_completa, 'wb') as f:
                f.write(img_data.content)
            print(f"Imagen guardada correctamente en {ruta_completa}.")
        
        ruta_normalizada = ruta_completa.replace('\\', '/')
        index = ruta_normalizada.find('Resources/')
        if index != -1:
            ruta_relativa = ruta_normalizada[index + len('Resources/'):]
        else:
            ruta_relativa = os.path.relpath(ruta_completa).replace('\\', '/')
        
        return ruta_relativa

    except Exception as e:
        print(f"Error al descargar la imagen: {e}")
        return None
    
# Conseguir la información de los jugadores de los equipos desde una lista de URLs
def get_team_data():
    informacion_equipos = []
    urls = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")
    
    total_urls = len(urls)
    total_equipos = 0
    equipos_exitosos = 0

    if not urls:
        print("❌ No se encontraron enlaces de equipos.")
        return []

    print(f"🔍 Consultando información de {total_urls} equipos...")
    start_time = time.time()  # ⏱️ Inicia el temporizador

    for url in urls:
        total_equipos += 1
        try:
            response = get_html(url, headers)
            if response is None:
                print(f"❌ No se pudo obtener respuesta de la URL: {url}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.select_one('table#infoboxTeam')
            if not table:
                print(f"❌ No se encontró la tabla de información del equipo en: {url}")
                continue

            equipo = {
                'nombre_equipo': None,
                'logo': None,
                'pais': None,
                'region': None,
                'propietario': None,
                'head_coach': None,
                'partners': None,
                'fecha_fundacion': None
            }

            nombre = table.select_one('th.infobox-title')
            if nombre:
                texto = nombre.get_text(strip=True)
                texto_sin_parentesis = re.sub(r'\s*\(.*?\)\s*', '', texto)
                equipo['nombre_equipo'] = texto_sin_parentesis.replace(' ', '_').replace('Season', '').strip()

            logo_img = table.select_one('img[data-src]')
            if logo_img:
                logo_path = download_image(os.path.join(TEAM_IMAGES_DIR, f"{equipo['nombre_equipo']}.png"), logo_img['data-src'])
                if logo_path is not None:
                    equipo['logo'] = logo_path
            else:
                print(f"⚠️ No se encontró la imagen del logo en: {url}")

            org_location_row = table.find('td', class_='infobox-label', string='Org Location')
            if org_location_row:
                pais_td = org_location_row.find_next_sibling('td')
                pais_span = pais_td.select_one('span.markup-object-name')
                equipo['pais'] = pais_span.get_text(strip=True) if pais_span else pais_td.get_text(strip=True)

            region_icon = table.select_one('tr.infobox-region div.region-icon')
            if region_icon:
                equipo['region'] = region_icon.get_text(strip=True)

            owner_row = table.find('td', class_='infobox-label', string='Owner')
            if owner_row:
                owner_td = owner_row.find_next_sibling('td')
                equipo['propietario'] = owner_td.get_text(" ", strip=True)

            coach_row = table.find('td', class_='infobox-label', string='Head Coach')
            if coach_row:
                coach_td = coach_row.find_next_sibling('td')
                equipo['head_coach'] = coach_td.get_text(" ", strip=True)

            partners_row = table.find('td', class_='infobox-label', string='Partner')
            if partners_row:
                partners_td = partners_row.find_next_sibling('td')
                partners_links = partners_td.select('a')
                equipo['partners'] = ", ".join([a.get_text(strip=True) for a in partners_links])

            fecha_row = table.select_one('table.infobox-subtable td')
            if fecha_row:
                equipo['fecha_fundacion'] = fecha_row.get_text(strip=True)

            informacion_equipos.append(equipo)
            equipos_exitosos += 1
            print(f"✅ Información del equipo {equipo['nombre_equipo']} extraída correctamente.")

        except Exception as e:
            print(f"🔥 Error al intentar extraer información del equipo en {url}: {e}")
            continue

    end_time = time.time()  # ⏱️ Finaliza el temporizador
    elapsed = end_time - start_time
    minutos, segundos = divmod(elapsed, 60)

    print("\n📋 Resumen del scraping de equipos:")
    print(f"🔗 URLs consultadas: {total_urls}")
    print(f"🏢 Total de equipos detectados: {total_equipos}")
    print(f"✔️ Equipos extraídos correctamente: {equipos_exitosos}")
    print(f"❌ Fallos de extracción: {total_equipos - equipos_exitosos}")
    print(f"⏱️ Duración total del scraping: {int(minutos)} min {int(segundos)} s")

    return informacion_equipos

if __name__ == "__main__":
    equipos = get_player_data()
    
    
