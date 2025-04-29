import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import sys
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


# Conseguir los enlaces de los equipos de la LEC 2025 Spring Season desde Leaguepedia
def get_team_links(url):
    base_url = 'https://lol.fandom.com/'
    response = requests.get(url, headers=headers)
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

def get_teams_logos(url):
    # Realizar la solicitud HTTP
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error al acceder a la página: {response.status_code}")
        return

    # Parsear el contenido HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    tables = soup.find_all('table', {'class': 'wikitable tournament-roster'})
    logos = []
    nombre_equipos = []
    
    for table in tables:
        # Obtener el nombre del equipo
        nombre_equipo = table.find('tr').get_text(strip=True)
        nombre_equipo = nombre_equipo.replace(' ', '_').replace('/', '_')  # Limpiar nombre
        nombre_equipos.append(nombre_equipo)

        # Obtener el logo
        row = table.find('tr', {'class': 'RosterLogos'})
        logo_url = row.find('img')
        if logo_url:
            logo = logo_url.get('data-src') or logo_url.get('src')
            if logo:
                logos.append(logo)

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
            
if __name__ == "__main__":
    equipos = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")  

    # Mostrar los resultados
    '''for equipo in equipos:
        print(equipo)'''
        
    # Obtener los logos de los equipos
    get_teams_logos("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")
    
