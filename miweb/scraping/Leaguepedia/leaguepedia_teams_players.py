"""
`leaguepedia_teams_players.py`

Este script realiza scraping sobre la wiki colaborativa [Leaguepedia](https://lol.fandom.com),
extrayendo información actualizada de los **equipos** y **jugadores activos** en la LEC (League of Legends
EMEA Championship) para una temporada concreta (por defecto: Spring 2025).

La información recolectada incluye:
- Enlaces a páginas de equipos.
- Datos básicos de los jugadores: nombre, país, residencia, rol, fechas de contrato, IDs de soloqueue, imagen.
- Información de equipos: nombre oficial, país, región, propietarios, patrocinadores, head coach y logo.

También descarga y organiza las **imágenes de jugadores y equipos**, genera diccionarios estructurados
y guarda datos en archivos JSON listos para su inserción en base de datos.

### Funciones destacadas:

- `get_team_links(url)`: Extrae los enlaces a todos los equipos participantes desde la página del split.
- `get_extra_player_data(url)`: Obtiene información extendida de cada jugador desde su perfil individual.
- `get_player_data()`: Itera por los equipos y compone una lista completa de los jugadores actuales.
- `get_team_data()`: Extrae información detallada de cada equipo (estructura organizativa, fundación, logo, etc).
- `download_image(ruta, url)`: Descarga una imagen desde una URL y la guarda en el disco.
- `convertir_fecha()`, `get_html()`: Funciones auxiliares para limpieza y conexión.

Este script es ejecutado directamente o bien invocado desde el scheduler o un script orquestador
(`importar_datos.py`) para mantener actualizados los datos del split actual.

**Requiere conexión a Internet y acceso a la plataforma Leaguepedia.**
"""
# Librerías estándar y externas utilizadas
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import re
from datetime import datetime
import random
import time

# Definición de directorios clave y rutas del proyecto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..'))
sys.path.insert(0, PROJECT_ROOT)

# Importación de rutas desde archivo de configuración
from Resources.rutas import * # Rutas globales del proyecto definidas externamente en el módulo Resources

# Directorios y rutas para guardar datos
TEAM_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_TEAMS)
PLAYER_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_PLAYERS)
PLAYER_INSTALATION_DATA = os.path.join(JSON_INSTALATION_PLAYERS, "players_data_leguepedia.json")
TEAMS_INSTALATION_JSON = os.path.join(JSON_INSTALATION_TEAMS, "teams_data_leguepedia.json")
LOGO_TEAMS_PATH = os.path.join(JSON_PATH_TEAMS_LOGOS, "teams_logos_path.json")


# Headers HTTP simulando navegador real para evitar bloqueos
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
    """
    Genera encabezados HTTP dinámicos para simular distintos navegadores y evitar bloqueos por scraping.

    Cambia aleatoriamente el `User-Agent` y el `Referer` para cada petición, eligiendo entre varias
    opciones populares.

    Returns:
        dict: Diccionario de encabezados HTTP con `User-Agent` y `Referer` aleatorios.
    """
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
    """
    Convierte una cadena de texto con formato de fecha en inglés (por ejemplo, 'March 10, 2002')
    al formato ISO estándar (`YYYY-MM-DD`).

    También elimina cualquier comentario entre paréntesis que acompañe la fecha (como nacionalidades o notas).

    Args:
        fecha_str (str): Fecha en formato inglés, potencialmente con anotaciones entre paréntesis.

    Returns:
        str or None: Fecha convertida al formato 'YYYY-MM-DD', o `None` si ocurre un error en el formato.
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


def get_html(url, timeout=10):
    """
    Realiza una solicitud HTTP GET a la URL especificada y devuelve la respuesta si es exitosa.

    Se utilizan encabezados dinámicos para simular navegación humana, y se maneja una amplia
    gama de excepciones para garantizar robustez ante errores comunes de red.

    Args:
        url (str): Dirección web a la que se realizará la solicitud.
        timeout (int): Tiempo máximo de espera en segundos antes de cancelar la solicitud (por defecto: 10).

    Returns:
        requests.Response or None: Objeto de respuesta si la solicitud fue exitosa, `None` si falló.
    """
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

def get_team_links(url):
    """
    Obtiene los enlaces a las páginas de todos los equipos que participan en una temporada específica
    de la LEC desde Leaguepedia.

    Esta función analiza la página principal de la temporada (`url`) y busca enlaces HTML con la clase
    `catlink-teams`, típicamente utilizada en Leaguepedia para vincular a las páginas de equipos.

    Args:
        url (str): URL de la página de la temporada en Leaguepedia (por ejemplo, Spring 2025).

    Returns:
        set: Conjunto de URLs absolutas a las páginas de los equipos. Se devuelve un set vacío si ocurre
        algún error durante la solicitud o el parseo.
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
    Extrae información adicional de un jugador desde su perfil individual en Leaguepedia.

    Esta función accede a la URL del perfil del jugador y obtiene detalles como:
    - Imagen del jugador (descargada y almacenada localmente).
    - Fecha de nacimiento (formateada como `YYYY-MM-DD`).
    - Identificadores de SoloQueue (por región).

    Se utiliza BeautifulSoup para parsear la tabla `infoboxPlayer` y descargar directamente la imagen
    desde la ruta proporcionada en el HTML.

    Args:
        url (str): URL absoluta del perfil del jugador en Leaguepedia.

    Returns:
        dict or None: Diccionario con los campos `image`, `birthday`, `soloqueue_ids` si se extraen correctamente,
        o `None` si ocurre un error en la carga o procesamiento de datos.
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
                                 
            

def get_player_data():
    """
    Extrae información detallada de todos los jugadores activos en la LEC desde Leaguepedia.

    Recorre las páginas de los equipos participantes en el split actual (por defecto: Spring 2025)
    y obtiene para cada jugador:
    - Nombre de invocador y nombre real
    - Residencia y nacionalidad
    - Rol dentro del equipo
    - Fecha de entrada y finalización de contrato
    - IDs de SoloQueue
    - Fecha de nacimiento
    - Imagen (descargada y almacenada localmente)

    Esta función hace uso de `get_team_links` para obtener los equipos, y `get_extra_player_data` para
    ampliar los datos de cada jugador desde su perfil individual.

    Returns:
        list[dict]: Lista de diccionarios, cada uno representando a un jugador con sus campos estructurados.
    """
    all_player_data = []
    urls = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")  
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
                        'equipo': re.sub(r'\s*\(.*?\)\s*', '', url.split('/')[-1].replace('_', ' ').replace('Season', '').strip()),
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
                    continue  

        except requests.exceptions.RequestException as e:
            print(f"Error de red al acceder a {url}: {e}")
            continue 

        except Exception as e:
            print(f"Error inesperado al procesar los datos del equipo en {url}: {e}")
            continue  
    return all_player_data


def download_image(ruta_completa, url_imagen):
    """
    Descarga una imagen desde una URL y la guarda en la ruta especificada dentro del sistema de archivos local.

    Si la imagen ya existe en el disco, se omite la descarga para evitar redundancias. Al finalizar,
    se devuelve la ruta relativa normalizada desde el directorio `Resources/`, compatible con el uso
    en rutas web o en base de datos.

    Args:
        ruta_completa (str): Ruta absoluta donde se debe guardar la imagen.
        url_imagen (str): URL desde la cual descargar la imagen.

    Returns:
        str or None: Ruta relativa normalizada si la descarga o verificación es exitosa, `None` si ocurre un error.
    """
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
    
def get_team_data():
    """
    Extrae información detallada de los equipos activos en la LEC para una temporada específica desde Leaguepedia.

    Recorre las páginas de cada equipo listadas en la página del split actual (por defecto: Spring 2025),
    y recopila los siguientes datos estructurados:
    - Nombre oficial del equipo (limpiado y formateado)
    - Logo del equipo (descargado localmente y guardado como ruta relativa)
    - País de origen
    - Región competitiva
    - Propietario del equipo
    - Entrenador principal (Head Coach)
    - Patrocinadores (Partners)
    - Fecha de fundación

    Returns:
        list[dict]: Lista de diccionarios con la información clave de cada equipo participante.
    """
    informacion_equipos = []
    urls = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")
    if not urls:
        print("No se encontraron enlaces de equipos.")
        return []
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
                texto = nombre.get_text(strip=True)
                # Eliminar todo lo que esté entre paréntesis y los paréntesis
                texto_sin_parentesis = re.sub(r'\s*\(.*?\)\s*', '', texto)
                equipo['nombre_equipo'] = texto_sin_parentesis.replace(' ', '_').replace('Season', '').strip()

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
    print("👤 Actualizando jugadores...")
    jugadores = get_player_data()
    print(jugadores)    

    
