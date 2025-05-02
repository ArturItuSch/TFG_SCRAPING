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
PLAYER_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_PLAYERS)
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

def convertir_fecha(fecha_str):
    """
    Convierte una fecha en formato de texto (por ejemplo, "March 10, 2022") 
    a un formato estándar de fecha (YYYY-MM-DD). Si la fecha contiene
    información adicional como la edad, esta será eliminada antes de la conversión.

    Parámetros:
    fecha_str (str): La fecha en formato de texto que se desea convertir.

    Retorna:
    str: La fecha convertida al formato YYYY-MM-DD si la conversión es exitosa.
         Retorna None si ocurre un error o la fecha no tiene el formato esperado.
    
    Excepciones:
    Si la fecha no puede ser convertida debido a un error en el formato o 
    cualquier otro tipo de excepción, la función maneja el error y retorna None.
    """
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



def write_json(nombre_archivo, datos):
    """
    Guarda un diccionario de datos en un archivo JSON con un formato legible 
    (con indentación y sin caracteres ASCII). Si ocurre un error durante 
    el proceso de escritura, se manejan las excepciones correspondientes.

    Parámetros:
    nombre_archivo (str): El nombre o ruta del archivo donde se guardarán los datos en formato JSON.
    datos (dict): Los datos a escribir en el archivo. Deben ser un objeto serializable en JSON.

    Excepciones:
    - IOError, OSError: Se generan si ocurre un error al intentar escribir en el archivo.
    - TypeError: Se genera si los datos proporcionados no son serializables en JSON.

    Retorna:
    None: La función no retorna ningún valor, pero imprime un mensaje de éxito o error.
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
    Realiza una solicitud HTTP GET a la URL proporcionada y devuelve la respuesta 
    si la solicitud es exitosa. Si ocurre un error durante la solicitud, se 
    maneja adecuadamente mostrando un mensaje de error según el tipo de excepción.

    Parámetros:
    url (str): La URL a la que se realiza la solicitud GET.
    headers (dict, opcional): Los encabezados HTTP adicionales que se incluyen en la solicitud. Por defecto es None.
    timeout (int, opcional): El tiempo máximo de espera (en segundos) antes de que la solicitud se agote. Por defecto es 10 segundos.

    Excepciones:
    - Timeout: Si se agota el tiempo de espera de la solicitud.
    - TooManyRedirects: Si hay demasiadas redirecciones.
    - SSLError: Si ocurre un error relacionado con SSL.
    - ConnectionError: Si hay problemas de conexión.
    - HTTPError: Si la respuesta HTTP indica un error (por ejemplo, código 404 o 500).
    - RequestException: Para cualquier otro error desconocido durante la solicitud.

    Retorna:
    response (requests.Response): El objeto de respuesta si la solicitud es exitosa. Si ocurre un error, retorna None.
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

    
    
def get_team_links(url):
    """
    Obtiene los enlaces a las páginas de los equipos de la temporada 2025 de la LEC 
    desde la URL proporcionada.

    La función realiza una solicitud HTTP a la URL especificada, extrae los enlaces 
    correspondientes a los equipos y devuelve un conjunto de URLs completas.

    Parámetros:
    url (str): La URL de la página que contiene los enlaces de los equipos.

    Excepciones:
    - RequestException: Si ocurre un error en la solicitud HTTP (por ejemplo, problemas de red).
    - Exception: Para cualquier otro error inesperado durante el procesamiento de los enlaces.

    Retorna:
    set: Un conjunto de URLs completas de los equipos, o un conjunto vacío si ocurre un error.
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

def get_extra_player_data(url):
    """
    Obtiene los datos específicos de un jugador a partir de su página de perfil.

    La función realiza una solicitud HTTP a la URL proporcionada, procesa la página HTML
    y extrae información relevante del jugador, incluyendo su cumpleaños, imagen y apodos 
    de SoloQ.

    Parámetros:
    url (str): La URL de la página del jugador de la que se extraerán los datos.

    Excepciones:
    - RequestException: Si ocurre un error en la solicitud HTTP (por ejemplo, problemas de red).
    - Exception: Para cualquier otro error inesperado durante el procesamiento de los datos del jugador.

    Retorna:
    dict: Un diccionario con los datos del jugador. Puede contener las claves:
        - 'birthday': La fecha de nacimiento del jugador en formato YYYY-MM-DD.
        - 'soloqueue_ids': Una lista de apodos de SoloQ y sus respectivas regiones.
        - 'image': La ruta de la imagen descargada del jugador o None si no se pudo descargar.

    Si ocurre algún error durante el proceso, se retorna None.
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

                                 
            

def get_player_data(urls):
    """
    Obtiene los datos de los jugadores de los equipos a partir de una lista de URLs.

    La función realiza solicitudes HTTP a las URLs proporcionadas, procesa la página HTML de cada una,
    extrae los datos de los jugadores de las tablas y llama a la función `get_extra_player_data` para obtener
    información adicional como el cumpleaños, los apodos de SoloQ y la imagen.

    Parámetros:
    urls (list of str): Lista de URLs de las páginas de los equipos de la LEC.

    Excepciones:
    - RequestException: Si ocurre un error en la solicitud HTTP (por ejemplo, problemas de red).
    - Exception: Para cualquier otro error inesperado durante el procesamiento de los datos de los jugadores.

    Retorna:
    list: Una lista de diccionarios, donde cada diccionario contiene la información de un jugador, con las siguientes claves:
        - 'jugador': Nombre del jugador.
        - 'nombre': Nombre real del jugador.
        - 'residencia': Residencia del jugador.
        - 'rol': Rol del jugador en el equipo.
        - 'equipo': Nombre del equipo al que pertenece el jugador.
        - 'pais': País de origen del jugador.
        - 'nacimiento': Fecha de nacimiento del jugador (si está disponible).
        - 'soloqueue_ids': Apodos de SoloQ del jugador y las regiones correspondientes (si están disponibles).
        - 'contratado_hasta': Fecha de finalización del contrato del jugador.
        - 'contratado_desde': Fecha de inicio del contrato del jugador.
        - 'imagen': Enlace a la imagen del jugador (si está disponible).
        
    Si ocurre algún error durante el proceso, la función saltará esa URL y continuará con las siguientes.
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
    Descarga una imagen desde una URL y la guarda localmente en la ruta especificada.

    Esta función realiza una solicitud HTTP para obtener la imagen de la URL dada,
    la guarda como un archivo binario en la ruta proporcionada y devuelve la ruta
    relativa al directorio actual del proyecto si la descarga fue exitosa.

    Parámetros:
        ruta_completa (str): Ruta absoluta donde se guardará la imagen descargada.
        url_imagen (str): URL directa de la imagen a descargar.

    Retorna:
        str | None: Ruta relativa al proyecto si la descarga fue exitosa; 
                    None si ocurrió algún error durante el proceso.
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
    
def get_team_info(urls):
    """
    Extrae información detallada de equipos desde una lista de URLs de páginas web.

    Esta función realiza el scraping de cada página web correspondiente a un equipo, 
    extrayendo información relevante como el nombre, logo, país, región, propietario, 
    entrenador principal, socios y fecha de fundación. Utiliza `BeautifulSoup` para 
    analizar el contenido HTML y devuelve una lista de diccionarios con los datos recolectados.

    Parámetros:
        urls (list[str]): Lista de URLs (una por equipo) desde donde se extraerá la información.

    Retorna:
        list[dict]: Lista de diccionarios. Cada diccionario contiene información detallada
                    sobre un equipo, incluyendo:
                        - nombre_equipo
                        - logo (ruta de la imagen descargada)
                        - pais
                        - region
                        - propietario
                        - head_coach
                        - partners
                        - fecha_fundacion
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
    '''player_data = get_player_data(equipos_url)
    write_json(PLAYER_INSTALATION_DATA, player_data)'''  
    
    # Obtener los datos de los equipos descargar los logos y guardarlos en un JSON
    team_data = get_team_info(equipos_url)
    write_json(TEAMS_INSTALATION_JSON, team_data)    
    
    
