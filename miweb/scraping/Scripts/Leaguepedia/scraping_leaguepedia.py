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
    team_data = []  # Lista para almacenar los datos de los equipos
    for url in urls:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'class': 'infobox InfoboxTeam'}, id='infoboxTeam')
            if not table:
                print(f"❌ No se encontró la tabla en {url}")
                continue
            else:
                rows = table.find_all('tr')
                
                # Extraer datos de las filas de la tabla
                for row in rows:
                    cells = row.find_all('th')
                    if len(cells) > 1:
                        team_info = {
                            '''"nombre": #Si el th class se llama infobox-title, entonces extraer el texto
                                cells[0].text.strip() if 'infobox-title' not in cells[0]['class'] else cells[1].text.strip(),
                            "ubicacion": # Si el td text es Org Location entonces extraer del td el primer span title
                            "region": # Si el tr class se llama infobox-region, entonces extraer el texto del primer div
                            "entrenador": #Si el td test es Head Coach entonces extraer todo el texto del td 
                            "creacion": cells[4].text.strip()'''
                        }
                team_data.append(team_info)  # Añadir la información a la lista
                print(f"✅ Datos extraídos de {url}")
        except requests.HTTPError as e:
            print(f"❌ Error HTTP: {e}")
        except requests.RequestException as e:
            print(f"❌ Error al realizar la solicitud: {e}")
        except Exception as e:
            print(f"❌ Error al procesar la página: {e}")
    
    return team_data

# Conseguir los enlaces de los equipos
# de la LEC 2025 Spring Season desde Leaguepedia
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

if __name__ == "__main__":
    equipos = get_team_links("https://lol.fandom.com/wiki/LEC/2025_Season/Spring_Season")  

    # Mostrar los resultados
    for equipo in equipos:
        print(equipo)
    team_data = get_team_data(equipos)
    for equipo in team_data:
        print(equipo)