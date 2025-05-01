import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import json
from pathlib import Path
import re
from datetime import datetime

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

# Conversiín de fechas
def convertir_fecha(fecha_str):
    try:
        # Elimina la parte de la edad si está presente
        fecha_limpia = re.sub(r'\(.*?\)', '', fecha_str).strip()
        # Convierte al formato YYYY-MM-DD
        fecha = datetime.strptime(fecha_limpia, "%B %d, %Y")
        return fecha.strftime("%Y-%m-%d")
    except ValueError:
        return None
    except Exception as e:
        print(f"Error al convertir la fecha: {e}")
        return None


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
            for row in rows:
                td = row.find('td', class_='infobox-wide')
                if td is not None:
                    img_link_tag = table.find('a', class_='image')
                    if img_link_tag and img_link_tag.has_attr('href'):
                        player_data['image'] = img_link_tag['href']
                        continue # Salta al siguiente ciclo del bucle
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
                                 
            

# Conseguir los datos de los jugadores de los equipos
def get_player_data(urls):
    all_player_data = []  
    for url in urls:
        try:
            response = get_html(url, headers)
            if response is None:
                print(f"No se pudo obtener respuesta de la URL: {url} en get_team_data")
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

            rows = tbody.find_all('tr')

            for row in rows:
                celdas = row.find_all('td')
                if len(celdas) < 7:
                    continue 
                try:
                    
                    residencia = celdas[0].get_text(strip=True)
                    pais = celdas[1].find('span')['title'] if celdas[1].find('span') else ''
                    jugador = celdas[2].get_text(strip=True)
                    nombre_real = celdas[3].get_text(strip=True)
                    rol = celdas[4].find('span', class_='markup-object-name').get_text(strip=True)
                    contrato = celdas[5].get_text(strip=True)
                    spans = celdas[6].find_all('span')
                    fecha_union = spans[1].get_text(strip=True) if len(spans) > 1 else ''
                
                    try:
                        enlace_tag = celdas[2].find('a')
                        url_relativa = enlace_tag['href'] if enlace_tag else ''
                        url_jugador = urljoin('https://lol.fandom.com', url_relativa)
                        datos_complementarios = get_extra_player_data(url_jugador)
                    except Exception as e:
                        print(f"Error al obtener datos complementarios del jugador: {e}")
                        datos_complementarios = {}
                        
                    miembro = {
                        'residencia': residencia,
                        'pais': pais,
                        'jugador': jugador,
                        'nombre': nombre_real,
                        'nacimiento': datos_complementarios.get('birthday', None),
                        'rol': rol,
                        'soloqueue_ids': datos_complementarios.get('soloqueue_ids', None),
                        'contratado_hasta': contrato,
                        'contratado_desde': fecha_union,
                        'imagen': datos_complementarios.get('image', None),
                    }
                    all_player_data.append(miembro)

                except Exception as e:
                    print(f"Error al procesar una fila: {e}")
                    continue  # Continuar con la siguiente fila si hay un error

        except requests.exceptions.RequestException as e:
            print(f"Error de red al acceder a {url}: {e}")
            continue  # Saltar a la siguiente URL si hay un error de red

        except Exception as e:
            print(f"Error inesperado al procesar los datos del equipo en {url}: {e}")
            continue  # Saltar a la siguiente URL si hay un error inesperado

    return all_player_data

# Extraer los logos de los equipos y su nombre -> Retorna una lista de diccionarios con el nombre del equipo y una lista de las urls de los logos
def get_teams_logos(url):
    nombre_equipos = []
    logos = []

    try:
        response = requests.get(url, headers=headers)
        if not response or response.status_code != 200:
            print(f"No se pudo obtener la página: {url}")
            return nombre_equipos, logos

        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable tournament-roster'})

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

    except requests.exceptions.RequestException as e:
        print(f"Error de red al acceder a {url}: {e}")
    except Exception as e:
        print(f"Error general al extraer logos de equipos en {url}: {e}")

    download_images(nombre_equipos, logos, TEAM_IMAGES_DIR)
    return nombre_equipos, logos

# Descragar las images 
def download_images(nombres_archivo, url_imagenes, ruta):
    rutas_logos = []
    
    for nombre_archivo, logo_url in zip(nombres_archivo, url_imagenes):
        nombre_imagen = f"{nombre_archivo}_logo.png"
        ruta_imagen = os.path.join(ruta, nombre_imagen)
        relative_path = os.path.relpath(ruta_imagen, PROJECT_ROOT)

        try:
            print(f"Descargando {nombre_imagen}...")
            img_data = requests.get(logo_url).content
            with open(ruta_imagen, 'wb') as f:
                f.write(img_data)
            print(f"Imagen {nombre_imagen} descargada correctamente.")
            rutas_logos.append({
                "equipo": nombre_archivo,
                "ruta": relative_path.replace("\\", "/"),
                "url_logo": logo_url
            })
        except Exception as e:
            print(f"Error al descargar la imagen {nombre_imagen}: {e}")

    write_json(LOGO_TEAMS_PATH, rutas_logos)
   
def get_team_info(urls):
    informacion_equipos = []

    for url in urls:
        try:
            response = get_html(url, headers)
            if response is None:
                print(f"No se pudo obtener respuesta de la URL: {url}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar la tabla de información del equipo
            table = soup.find('table', class_='infobox InfoboxTeam', id='infoboxTeam')
            if not table:
                print(f"No se encontró la tabla de información del equipo en: {url}")
                continue
            
            # Inicializamos las variables
            nombre_equipo = None
            pais = None
            propietario = None
            fecha_fundacion = None
            
            rows = table.find_all('tr')
            for row in rows:
                # Buscar el nombre del equipo
                if row.find('th', class_='infobox-title'):
                    nombre_equipo = row.find('th', class_='infobox-title').get_text(strip=True)
                
                # Buscar el país
                if row.find('span', class_='sprite country-sprite'):
                    pais = row.find('span', class_='sprite country-sprite')['title']
                
                # Buscar el propietario
                if row.find('td', class_='infobox-label') and row.find('td', class_='infobox-label').get_text(strip=True) == 'Owner':
                    propietario = row.find('td', class_='infobox-data').get_text(strip=True)
                
                # Buscar la fecha de fundación en sub-tablas
                if row.find('table', class_='infobox-suitable'):
                    sub_rows = row.find_all('tr')
                    for sub_row in sub_rows:
                        if sub_row.find('th', class_='infobox-label') and sub_row.find('td', class_='infobox-data'):
                            if sub_row.find('th', class_='teamdate'):
                                fecha_fundacion = sub_row.find('td', class_='infobox-data').get_text(strip=True)

            # Verificar que tenemos todos los datos
            if nombre_equipo and pais and propietario and fecha_fundacion:
                # Almacenar la información del equipo
                informacion_equipos.append({
                    'nombre': nombre_equipo,
                    'region': "EMEA",
                    'pais': pais,
                    'propietario': propietario,
                    'ano_fundacion': fecha_fundacion
                })
            else:
                print(f"Faltan datos para el equipo en {url}")

        except requests.exceptions.RequestException as e:
            print(f"Error al obtener la página {url}: {e}")
        except Exception as e:
            print(f"Error al procesar la página {url}: {e}")

    return informacion_equipos
             
if __name__ == "__main__":
    equipos_url = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")  
    
    # Obtener los datos de los Jugadores
    #player_data = get_player_data(equipos_url)
     
    # Guardar los datos de los jugadores en un JSON    
    #write_json(PLAYER_INSTALATION_DATA, player_data)    
        
    # Obtener los logos de los equipos
    get_teams_logos("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")
    
    # Obtener los datos de los equipos
    team_data = get_team_info(equipos_url)
    write_json(TEAMS_INSTALATION_JSON, team_data)    
    
    
