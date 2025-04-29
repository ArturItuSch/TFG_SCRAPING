import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
import json
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.insert(0, PROJECT_ROOT)

from Resources.rutas import CARPETA_IMAGENES_TEAMS
TEAM_IMAGES_DIR = os.path.join(CARPETA_IMAGENES_TEAMS)

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

def get_team_data(url):
    try:
        response = get_html(url, headers)
        if response is None:
            print(f"No se pudo obtener respuesta de la URL: {url}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        tabla = soup.find('table', class_='team-members')
        if not tabla:
            print(f"No se encontró la tabla de miembros en: {url}")
            return []

        tbody = tabla.find('tbody')
        if not tbody:
            print(f"No se encontró el cuerpo de la tabla en: {url}")
            return []

        filas = tbody.find_all('tr')
        miembros = []

        for fila in filas:
            celdas = fila.find_all('td')
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

                miembros.append({
                    'residencia': residencia,
                    'pais': pais,
                    'jugador': jugador,
                    'nombre': nombre_real,
                    'rol': rol,
                    'contratodo_hasta': contrato,
                    'contratado_desde': fecha_union
                })
            except Exception as e:
                print(f"Error al procesar una fila: {e}")
                continue

        return miembros

    except requests.exceptions.RequestException as e:
        print(f"Error de red al acceder a {url}: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado al procesar los datos del equipo en {url}: {e}")
        return []

def get_teams_logos(url):
    try:
        # Realizar la solicitud HTTP
        response = requests.get(url, headers=headers)
        if not response or response.status_code != 200:
            print(f"No se pudo obtener la página: {url}")
            return set()

        # Parsear el contenido HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable tournament-roster'})
        logos = []
        nombre_equipos = []

        for table in tables:
            try:
                # Obtener el nombre del equipo
                nombre_equipo = table.find('tr').get_text(strip=True)
                nombre_equipo = nombre_equipo.replace(' ', '_').replace('/', '_')
                nombre_equipos.append(nombre_equipo)

                # Obtener el logo
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

        # Descargar las imágenes
        for nombre_equipo, logo_url in zip(nombre_equipos, logos):
            nombre_imagen = f"{nombre_equipo}_logo.png"
            ruta_imagen = os.path.join(TEAM_IMAGES_DIR, nombre_imagen)

            try:
                print(f"Descargando {nombre_imagen}...")
                img_data = requests.get(logo_url).content
                with open(ruta_imagen, 'wb') as f:
                    f.write(img_data)
                print(f"Imagen {nombre_imagen} descargada correctamente.")
            except Exception as e:
                print(f"Error al descargar la imagen {nombre_imagen}: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Error de red al acceder a {url}: {e}")
    except Exception as e:
        print(f"Error general al procesar los logos de equipos en {url}: {e}")
            
if __name__ == "__main__":
    equipos = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")  

    # Obtener los datos de los equipos
    for equipo in equipos:
        print(f"Accediendo a la página del equipo: {equipo}")
        data = get_team_data(equipo)
        if data:
            print(f"Datos del equipo {equipo}:")
            for miembro in data:
                print(miembro)
        
    # Obtener los logos de los equipos
    get_teams_logos("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")
    
    
    
