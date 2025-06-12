"""
`leaguepedia_old_sesions.py`

Este módulo realiza scraping sobre Leaguepedia para recopilar información histórica de equipos que han
participado en temporadas pasadas de la LEC (anteriormente EU LCS). Su propósito es construir un
registro completo de los equipos antiguos que han competido en la región EMEA desde las primeras
temporadas hasta la actual.

### Funcionalidades principales:

- `get_urls_sesons()`: Obtiene todas las URLs de las páginas de temporadas anteriores (EU LCS y LEC).
- `extraer_equipos(url)`: Extrae los nombres de equipos participantes en una temporada específica, así como
  su logo correspondiente.
- `extraer_imagen_equipo(url)`: Obtiene la URL del logo de un equipo accediendo a su página individual
  y descargándolo localmente.
- `obtener_equipos_antiguos()`: Función orquestadora que recorre todas las temporadas pasadas, extrae los
  equipos y guarda sus datos en una lista de diccionarios con los campos: `name`, `season`, `imagen_url`.

### Datos extraídos:

- Nombre del equipo formateado (sin espacios, sin caracteres especiales).
- Temporada en la que participó.
- Ruta relativa a la imagen descargada del logo del equipo.

### Uso

Este script es usado para generar los registros históricos de equipos y logos que ya no están activos
en la escena competitiva actual. Puede ser ejecutado manualmente o invocado desde scripts de actualización
como `importar_datos.py`.

**Nota:** Este módulo requiere conexión a Internet y acceso a las rutas estructuradas de Leaguepedia.

"""
# Librerías estándar y externas utilizadas
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import re

# Definición de directorios clave, rutas del proyecto y funciones del script leaguepedia_teams_players
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..','..'))
sys.path.insert(0, PROJECT_ROOT)

from .leaguepedia_teams_players import download_image, get_html #  Funciones reutilizadas para poder descargar imágenes y hace peticiones con request
from Resources.rutas import * # Rutas globales del proyecto definidas externamente en el módulo Resources

# Directorios y rutas para guardar datos
TEAMS_INSTALATION_JSON = os.path.join(JSON_INSTALATION_TEAMS, "teams_data_leguepedia.json")
TEAMS_OLD_INSTALATION_JSON = os.path.join(JSON_INSTALATION_TEAMS, "teams_inSeson_leguepedia_data.json")
LOGO_TEAMS_PATH = os.path.join(JSON_PATH_TEAMS_LOGOS, "teams_logos_path.json")
TEAM_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_TEAMS)

# Ruta base para hacer scraping.
BASE_URL = "https://lol.fandom.com/wiki/LoL_EMEA_Championship"

    

def get_urls_sesons():
    """
    Extrae las URLs de todas las temporadas pasadas de la LEC (y antiguamente EU LCS) desde Leaguepedia.

    Accede a la página principal de la competición y localiza los enlaces a cada temporada mediante
    un análisis del contenido HTML. Filtra solo aquellos enlaces que pertenecen a temporadas válidas,
    como `/wiki/LEC/2021_Season` o `/wiki/EU_LCS/2018_Season`.

    Returns:
        set: Conjunto de URLs absolutas correspondientes a las páginas de temporadas históricas.
              Devuelve un set vacío si no se encuentran enlaces válidos o ocurre algún error.
    """
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
    """
    Extrae la URL del logo de un equipo desde su página individual en Leaguepedia.

    Esta función accede a la página del equipo, busca la tabla de información principal (`infoboxTeam`)
    y localiza la primera imagen dentro de ella. Devuelve la URL del logo, que puede usarse para su descarga.

    Args:
        url (str): URL absoluta de la página del equipo en Leaguepedia.

    Returns:
        str or None: URL del logo del equipo si se encuentra correctamente, o `None` si no se puede extraer.
    """
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
            print("Logo encontrado:", logo_url)
            return logo_url
        else:
            print("No se encontró ninguna imagen en la tabla.")
            return None

    except Exception as e:
        print(f"Error al procesar imagen del equipo en {url}: {e}")
        return None

        
def extraer_equipos(url):
    """
    Extrae los equipos que participaron en una temporada específica de la LEC (o EU LCS) desde Leaguepedia.

    Esta función accede a la página de la temporada indicada, localiza los nombres de los equipos y
    recopila información relevante como:
    - Nombre del equipo (normalizado y sin espacios)
    - Temporada a la que pertenece
    - Ruta relativa de la imagen del logo descargada localmente

    Args:
        url (str): URL de la página de la temporada histórica en Leaguepedia.

    Returns:
        list[dict]: Lista de diccionarios con los campos `name`, `season` e `imagen_url` para cada equipo encontrado.
    """
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
    """
    Orquesta el scraping de temporadas históricas de la LEC (y EU LCS) para obtener todos los equipos antiguos.

    Esta función:
    - Obtiene todas las URLs de temporadas anteriores mediante `get_urls_sesons()`.
    - Extrae los equipos de cada temporada usando `extraer_equipos(url)`.
    - Evita duplicados gracias a un conjunto de nombres ya procesados.

    El resultado es una lista consolidada de todos los equipos que han participado históricamente,
    incluyendo sus nombres, temporadas y logos.

    Returns:
        list[dict]: Lista de diccionarios con los datos de equipos antiguos (`name`, `season`, `imagen_url`).
    """
    print("⏳ Obteniendo URLs de temporadas...")
    urls = get_urls_sesons()
    if not urls:
        print("⚠️ No se encontraron URLs de temporadas.")
        return []

    equipos_totales = []
    equipos_procesados = set()

    for url in urls:
        print(f"🔎 Procesando temporada desde URL: {url}")
        equipos = extraer_equipos(url)

        for equipo in equipos:
            nombre = equipo.get("name")
            if not nombre or nombre in equipos_procesados:
                continue

            equipos_totales.append(equipo)
            equipos_procesados.add(nombre)

    print(f"✅ Equipos antiguos extraídos: {len(equipos_totales)}")
    return equipos_totales