"""
Script para realizar scraping de datos de Leaguepedia.

Este módulo contiene funciones reutilizables para trabajar con datos
de jugadores y equipos, incluyendo la obtención de HTML, conversión de fechas,
creación de archivos JSON y descarga de imágenes.

Autor: Artur Schuldt
Fecha: 25 de abril de 2025
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import json
from pathlib import Path
import re
from datetime import datetime

# Establece la ruta raíz del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
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


def convertir_fecha(fecha_str):
    """
    Convierte una fecha en inglés al formato 'YYYY-MM-DD'.

    :param fecha_str: Cadena con la fecha, puede contener edad entre paréntesis.
                      Ejemplo: "March 15, 2000 (24 años)"
    :type fecha_str: str
    :return: Fecha convertida en formato 'YYYY-MM-DD' o None si hay error.
    :rtype: str or None
    """
    try:
        fecha_limpia = re.sub(r'\(.*?\)', '', fecha_str).strip()
        fecha = datetime.strptime(fecha_limpia, "%B %d, %Y")
        return fecha.strftime("%Y-%m-%d")
    except ValueError:
        return None
    except Exception as e:
        print(f"Error al convertir la fecha: {e}")
        return None


def write_json(nombre_archivo, datos):
    """
    Guarda un diccionario en un archivo JSON con formato legible.

    :param nombre_archivo: Ruta del archivo donde se guardará el JSON.
    :type nombre_archivo: str
    :param datos: Datos a guardar, típicamente un diccionario o lista.
    :type datos: dict or list
    """
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
        print(f"Archivo JSON guardado correctamente en: {nombre_archivo}")
    except (IOError, OSError) as e:
        print(f"Error de escritura en el archivo {nombre_archivo}: {e}")
    except TypeError as e:
        print(f"Error de serialización de JSON: {e}")


def get_html(url, headers=None, timeout=10):
    """
    Realiza una petición GET a una URL y devuelve la respuesta si es exitosa.

    :param url: Dirección web a la que se desea acceder.
    :type url: str
    :param headers: Encabezados HTTP opcionales.
    :type headers: dict
    :param timeout: Tiempo máximo de espera para la respuesta.
    :type timeout: int
    :return: Objeto `requests.Response` si fue exitoso, o None si hubo error.
    :rtype: requests.Response or None
    """
    try:
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

# Conseguir los enlaces de los equipos de la LEC 2025 Spring Season
def get_team_links(url):
    """
    Obtiene los enlaces de los equipos listados en la página de la LEC 2025 Spring Season.

    Esta función analiza el HTML de la página dada y extrae todos los enlaces
    de los equipos usando la clase CSS `catlink-teams`.

    :param url: URL de la página de Leaguepedia con los equipos de la LEC.
    :type url: str
    :return: Conjunto de URLs absolutas de las páginas de los equipos encontrados.
    :rtype: set[str]

    :raises requests.exceptions.RequestException: Si ocurre un error al hacer la solicitud HTTP.
    :raises Exception: Si ocurre cualquier otro error inesperado durante el análisis.
    """
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
    """
    Extrae información adicional de un jugador desde su página en Leaguepedia.

    Esta función obtiene el HTML de la página del jugador y analiza la tabla 
    con id `infoboxPlayer` para obtener:
    
    - Enlace e imagen del jugador (si está disponible).
    - Fecha de cumpleaños (convertida al formato YYYY-MM-DD).
    - Nombres de invocador en Soloqueue por región.

    :param url: URL de la página del jugador en Leaguepedia.
    :type url: str
    :return: Diccionario con los datos extraídos (`image`, `birthday`, `soloqueue_ids`) o None si falla.
    :rtype: dict or None

    :raises requests.exceptions.RequestException: Si ocurre un error al hacer la solicitud HTTP.
    :raises Exception: Si ocurre cualquier otro error inesperado durante el análisis de la página.
    """
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
                        player_image = download_image(os.path.join(PLAYER_IMAGES_DIR, f"{url.split('/')[-1]}.png"), img_link_tag['href'])
                        if player_image is not None:
                            player_data['image'] = player_image
                            continue
                        else:
                            print(f"Error al descargar la imagen del jugador: {url}")
                            player_data['image'] = None
                    else:
                        print(f"No se encontró la imagen del jugador en: {url}")
                        return None                            
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
    """
    Extrae información de los jugadores de los equipos desde sus respectivas páginas de Leaguepedia.

    La función recorre una lista de URLs de equipos, accede a la tabla de miembros del equipo
    y extrae datos como el nombre del jugador, nombre real, país, residencia, rol, fechas de contrato,
    así como información adicional como la fecha de nacimiento, IDs de Soloqueue y la imagen del jugador,
    mediante la función auxiliar `get_extra_player_data`.

    :param urls: Lista de URLs de páginas de equipos en Leaguepedia.
    :type urls: list[str]
    :return: Lista de diccionarios, cada uno con los datos de un jugador.
    :rtype: list[dict]

    Cada diccionario incluye las siguientes claves:

        - 'jugador' (str): Nombre del jugador en el roster.
        - 'nombre' (str): Nombre real del jugador.
        - 'residencia' (str): Región de residencia.
        - 'rol' (str): Rol del jugador (Top, Jungle, etc.).
        - 'equipo' (str): Nombre del equipo (derivado de la URL).
        - 'pais' (str): País de nacionalidad (derivado del atributo title de la bandera).
        - 'nacimiento' (str or None): Fecha de nacimiento (en formato YYYY-MM-DD si disponible).
        - 'soloqueue_ids' (str or None): Lista de IDs de Soloqueue separados por coma y región.
        - 'contratado_hasta' (str): Fecha hasta la cual tiene contrato.
        - 'contratado_desde' (str): Fecha desde la cual está en el equipo.
        - 'imagen' (str or None): Ruta del archivo local de la imagen del jugador descargada.

    :raises requests.exceptions.RequestException: Si ocurre un error de red al obtener una página.
    :raises Exception: Si ocurre un error inesperado durante el análisis de la información.
    """
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
                        'jugador': jugador,
                        'nombre': nombre_real,
                        'residencia': residencia,
                        'rol': rol,
                        'equipo': url.split('/')[-1].replace('_', ' ').replace('Season', '').strip(),
                        'pais': pais,
                        'nacimiento': datos_complementarios.get('birthday', None),
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

def download_image(ruta_completa, url_imagen):
    """
    Descarga una imagen desde una URL y la guarda en la ruta especificada.

    Descarga una imagen desde la URL proporcionada y la guarda en el sistema de archivos en la ubicación
    especificada por `ruta_completa`. Retorna la ruta relativa al proyecto si la descarga fue exitosa.

    :param ruta_completa: Ruta completa donde se guardará la imagen.
    :type ruta_completa: str
    :param url_imagen: URL de la imagen a descargar.
    :type url_imagen: str
    :return: Ruta relativa a la imagen si fue descargada correctamente, o None si falló.
    :rtype: str or None

    :raises requests.exceptions.RequestException: Si ocurre un error al realizar la solicitud.
    :raises OSError: Si ocurre un error al escribir el archivo.
    """
    try:
        print(f"Descargando imagen desde {url_imagen} a {ruta_completa}...")
        img_data = requests.get(url_imagen, timeout=10)
        img_data.raise_for_status()

        with open(ruta_completa, 'wb') as f:
            f.write(img_data.content)

        print(f"Imagen guardada correctamente en {ruta_completa}.")

        # Obtener ruta relativa
        ruta_relativa = os.path.relpath(ruta_completa, start=os.getcwd())
        return ruta_relativa

    except Exception as e:
        print(f"Error al descargar la imagen: {e}")
        return None
    
# Conseguir la información de los jugadores de los equipos que se pasan por una lista de urls y retorna una lista de diccionarios con la información de los jugadores
def get_team_info(urls):
    """
    Extrae información básica de equipos de Leaguepedia desde una lista de URLs.

    Accede a cada página de equipo especificada, busca su tabla `infoboxTeam` y extrae datos clave como nombre,
    logo, país, región, propietario, entrenador principal, socios comerciales y fecha de fundación.

    :param urls: Lista de URLs de páginas de equipos en Leaguepedia.
    :type urls: list[str]
    :return: Lista de diccionarios con información de cada equipo.
    :rtype: list[dict]

    Cada diccionario de equipo contiene las siguientes claves:

        - 'nombre_equipo' (str): Nombre del equipo (usado como identificador).
        - 'logo' (str or None): Ruta relativa al logo descargado.
        - 'pais' (str or None): País de origen del equipo.
        - 'region' (str or None): Región de competencia del equipo.
        - 'propietario' (str or None): Nombre del propietario del equipo.
        - 'head_coach' (str or None): Entrenador principal.
        - 'partners' (str or None): Lista de socios del equipo (separados por coma).
        - 'fecha_fundacion' (str or None): Fecha en la que se fundó el equipo (si está disponible).

    :raises Exception: Si ocurre un error durante el análisis de la información de una URL.
    """
    informacion_equipos = []

    for url in urls:
        try:
            response = get_html(url, headers)
            if response is None:
                print(f"No se pudo obtener respuesta de la URL: {url}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')

            # Buscar la tabla de información del equipo
            table = soup.select_one('table#infoboxTeam')
            if not table:
                print(f"No se encontró la tabla de información del equipo en: {url}")
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

            # Nombre del equipo
            nombre = table.select_one('th.infobox-title')
            if nombre:
                equipo['nombre_equipo'] = nombre.get_text(strip=True).replace(' ', '_').replace('Season', '').strip()

            # Logo
            logo_img = table.select_one('img[data-src]')
            if logo_img:
                logo_path = download_image(os.path.join(TEAM_IMAGES_DIR, f"{equipo['nombre_equipo']}.png"), logo_img['data-src'])
                if logo_path is not None:
                    equipo['logo'] = logo_path
            else:
                print(f"No se encontró la imagen del logo en: {url}")

            # País (Org Location)
            org_location_row = table.find('td', class_='infobox-label', string='Org Location')
            if org_location_row:
                pais_td = org_location_row.find_next_sibling('td')
                pais_span = pais_td.select_one('span.markup-object-name')
                equipo['pais'] = pais_span.get_text(strip=True) if pais_span else pais_td.get_text(strip=True)

            # Región
            region_icon = table.select_one('tr.infobox-region div.region-icon')
            if region_icon:
                equipo['region'] = region_icon.get_text(strip=True)

            # Propietario (Owner)
            owner_row = table.find('td', class_='infobox-label', string='Owner')
            if owner_row:
                owner_td = owner_row.find_next_sibling('td')
                equipo['propietario'] = owner_td.get_text(" ", strip=True)

            # Head Coach
            coach_row = table.find('td', class_='infobox-label', string='Head Coach')
            if coach_row:
                coach_td = coach_row.find_next_sibling('td')
                equipo['head_coach'] = coach_td.get_text(" ", strip=True)

            # Partners
            partners_row = table.find('td', class_='infobox-label', string='Partner')
            if partners_row:
                partners_td = partners_row.find_next_sibling('td')
                partners_links = partners_td.select('a')
                equipo['partners'] = equipo['partners'] = ", ".join([a.get_text(strip=True) for a in partners_links])

            # Fecha de fundación
            fecha_row = table.select_one('table.infobox-subtable td')
            if fecha_row:
                equipo['fecha_fundacion'] = fecha_row.get_text(strip=True)

            # Mostrar resultado
            print(f"Información del equipo {equipo['nombre_equipo']} extraída correctamente.") 
            informacion_equipos.append(equipo)
        except Exception as e:
            print(f"Error al intentar extraer la información del equipo: {e}")
            continue
    return informacion_equipos

if __name__ == "__main__":
    equipos_url = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")  
    
    # Obtener los datos de los Jugadores
    player_data = get_player_data(equipos_url)
    write_json(PLAYER_INSTALATION_DATA, player_data)
    
    # Obtener los datos de los equipos descargar los logos y guardarlos en un JSON
    '''team_data = get_team_info(equipos_url)
    write_json(TEAMS_INSTALATION_JSON, team_data) '''   
    
    
