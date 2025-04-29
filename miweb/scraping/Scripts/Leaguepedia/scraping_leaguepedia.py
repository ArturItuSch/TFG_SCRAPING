import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, PROJECT_ROOT)

from Resources.rutas import *
TEAM_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_TEAMS)
PLAYER_INSTALATION_DATA = os.path.join(JSON_INSTALATION_PLAYERS, "players_data_leguepedia.json")
TEAMS_INSTALATION_JSON = os.path.join(JSON_INSTALATION_TEAMS, "teams_data_leguepedia.json")
LOGO_TEAMS_PATH = os.path.join(JSON_PATH_TEAMS_LOGOS, "teams_logos_path.json")

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

# Creación y escritura del archivo JSON
def write_json(nombre_archivo, datos):
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
        print(f"Archivo JSON guardado correctamente en: {nombre_archivo}")
    except (IOError, OSError) as e:
        print(f"Error de escritura en el archivo {nombre_archivo}: {e}")
    except TypeError as e:
        print(f"Error de serialización de JSON: {e}")
        
        
# Conseguir el html 
def get_html(url, headers=None, timeout=10):
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar GET a {url}: {e}")
        return None
    
    
# Conseguir los enlaces de los equipos de la LEC 2025 Spring Season
def get_team_links(url):
    base_url = 'https://lol.fandom.com/'
    try:
        response = get_html(url, headers)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {url}")
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

# Conseguir los datos de los equipos
def get_team_data(urls):
    all_team_data = []  # Inicializa una lista vacía para almacenar los datos de todos los equipos
    for url in urls:
        try:
            response = get_html(url, headers)
            if response is None:
                print(f"No se pudo obtener respuesta de la URL: {url}")
                continue  # Saltar a la siguiente URL si no se obtiene respuesta

            soup = BeautifulSoup(response.text, 'html.parser')
            tabla = soup.find('table', class_='team-members')
            if not tabla:
                print(f"No se encontró la tabla de miembros en: {url}")
                continue  # Saltar a la siguiente URL si no se encuentra la tabla

            tbody = tabla.find('tbody')
            if not tbody:
                print(f"No se encontró el cuerpo de la tabla en: {url}")
                continue  # Saltar a la siguiente URL si no se encuentra el cuerpo de la tabla

            filas = tbody.find_all('tr')

            for fila in filas:
                celdas = fila.find_all('td')
                if len(celdas) < 7:
                    continue  # Si no hay suficientes celdas, saltar a la siguiente fila

                try:
                    residencia = celdas[0].get_text(strip=True)
                    pais = celdas[1].find('span')['title'] if celdas[1].find('span') else ''
                    jugador = celdas[2].get_text(strip=True)
                    nombre_real = celdas[3].get_text(strip=True)
                    rol = celdas[4].find('span', class_='markup-object-name').get_text(strip=True)
                    contrato = celdas[5].get_text(strip=True)
                    spans = celdas[6].find_all('span')
                    fecha_union = spans[1].get_text(strip=True) if len(spans) > 1 else ''

                    miembro = {
                        'residencia': residencia,
                        'pais': pais,
                        'jugador': jugador,
                        'nombre': nombre_real,
                        'rol': rol,
                        'contratado_hasta': contrato,
                        'contratado_desde': fecha_union
                    }
                    all_team_data.append(miembro)

                except Exception as e:
                    print(f"Error al procesar una fila: {e}")
                    continue  # Continuar con la siguiente fila si hay un error

        except requests.exceptions.RequestException as e:
            print(f"Error de red al acceder a {url}: {e}")
            continue  # Saltar a la siguiente URL si hay un error de red

        except Exception as e:
            print(f"Error inesperado al procesar los datos del equipo en {url}: {e}")
            continue  # Saltar a la siguiente URL si hay un error inesperado

    return all_team_data

def get_teams_logos(url):
    rutas_logos = []

    try:
        response = requests.get(url, headers=headers)
        if not response or response.status_code != 200:
            print(f"No se pudo obtener la página: {url}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable tournament-roster'})
        logos = []
        nombre_equipos = []

        for table in tables:
            try:
                nombre_equipo = table.find('tr').get_text(strip=True)
                nombre_equipo = nombre_equipo.replace(' ', '_').replace('/', '_')
                nombre_equipos.append(nombre_equipo)

                row = table.find('tr', {'class': 'RosterLogos'})
                if row:
                    logo_url = row.find('img')
                    if logo_url:
                        logo = logo_url.get('data-src') or logo_url.get('src')
                        if logo:
                            logos.append(logo)
                        else:
                            print(f"Logo no encontrado para {nombre_equipo}")
                    else:
                        print(f"Tag <img> no encontrado para {nombre_equipo}")
                else:
                    print(f"Fila 'RosterLogos' no encontrada en la tabla de {nombre_equipo}")
            except Exception as e:
                print(f"Error procesando la tabla de un equipo: {e}")

        for nombre_equipo, logo_url in zip(nombre_equipos, logos):
            nombre_imagen = f"{nombre_equipo}_logo.png"
            ruta_imagen = os.path.join(TEAM_IMAGES_DIR, nombre_imagen)
            relative_path = os.path.relpath(ruta_imagen, PROJECT_ROOT)
            try:
                print(f"Descargando {nombre_imagen}...")
                img_data = requests.get(logo_url).content
                with open(ruta_imagen, 'wb') as f:
                    f.write(img_data)
                print(f"Imagen {nombre_imagen} descargada correctamente.")
                rutas_logos.append({
                    "equipo": nombre_equipo,
                    "ruta": relative_path.replace("\\", "/"),  
                    "url_logo": logo_url
                })
            except Exception as e:
                print(f"Error al descargar la imagen {nombre_imagen}: {e}")

        # Guardar las rutas en un JSON
        write_json(LOGO_TEAMS_PATH, rutas_logos)

    except requests.exceptions.RequestException as e:
        print(f"Error de red al acceder a {url}: {e}")
    except Exception as e:
        print(f"Error general al procesar los logos de equipos en {url}: {e}")
   
def get_team_info(url):
    try:
        response = requests.get(url, headers=headers)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {url}")
            return set()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extraer nombre del equipo desde el título de la página
        titulo = soup.find('h1', class_='page-header__title')
        nombre = titulo.get_text(strip=True) if titulo else "Desconocido"

        # Extraer la infobox del equipo
        infobox = soup.find('table', class_='infobox')
        if not infobox:
            print("No se encontró la tabla de información del equipo.")
            return {}

        info = {'nombre': nombre}

        # Extraer filas clave-valor de la infobox
        for row in infobox.find_all('tr'):
            header = row.find('th')
            value = row.find('td')

            if header and value:
                key = header.get_text(strip=True).lower()
                val = value.get_text(strip=True)

                if 'region' in key:
                    info['region'] = val
                elif 'founded' in key or 'fundación' in key:
                    info['fundado'] = val
                elif 'location' in key or 'base' in key:
                    info['ubicación'] = val
                elif 'website' in key or 'sitio web' in key:
                    link = value.find('a')
                    info['web'] = link['href'] if link else val

        return info

    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la página: {e}")
        return {}
    except Exception as e:
        print(f"Error al procesar los datos del equipo: {e}")
        return {}
             
if __name__ == "__main__":
    equipos = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")  
    #print(f"Equipos encontrados: {equipos}")
    # Obtener los datos de los equipos
    #data = get_team_data(equipos)
    
    # Guardar los datos de los jugadores en un JSON    
    #write_json(PLAYER_INSTALATION_DATA, data)    
        
    # Obtener los logos de los equipos
    get_teams_logos("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")
    
    # Obtener los datos de los equipos
    '''for equipo in equipos:
        print(f"Accediendo a la página del equipo: {equipo}")
        data = get_team_info(equipo)
        write_json(TEAMS_INSTALATION_JSON, data)'''

    
