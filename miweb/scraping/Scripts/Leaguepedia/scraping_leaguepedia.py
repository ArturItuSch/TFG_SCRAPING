import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin




headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1", # Do Not Track Request Header
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

def get_team_data(urls):
    team_data = []
    for url in urls:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            soup = BeautifulSoup(response.content, 'html.parser')
            
            nombre = soup.find('h1', {'id': 'firstHeading'}).text.strip()
            logo_img = soup.find('a', {'class': 'image'}).find('img')
            logo_url = 'https:' + logo_img['src'] if logo_img else None
            
        except requests.RequestException as e:
            print(f"❌ Error al realizar la solicitud: {e}")
        except Exception as e:
            print(f"❌ Error al procesar la página: {e}")
    return team_data

# Conseguir los enlaces de los equipos
# de la LEC 2025 Spring Season desde Leaguepedia
def get_team_links():
    url = 'https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season'
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

if __name__ == "__main__":
    equipos = get_team_links()

    # Mostrar los resultados
    for equipo in equipos:
        print(equipo)