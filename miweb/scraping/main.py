import os
import django
import sys

# Ruta a tu proyecto Django (donde está settings.py)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miweb.settings')
django.setup()
from database.models import *
from scraping.driver import iniciar_driver
from scraping.GOL.scraping_gol import get_champions_information



def importar_campeones():
    driver = iniciar_driver()
    campeones_data = get_champions_information(driver)
    driver.quit()

    campeones_objs = []
    for champ in campeones_data:
        if not Campeon.objects.filter(nombre=champ['nombre']).exists():
            campeones_objs.append(Campeon(nombre=champ['nombre'], ruta_imagen=champ['ruta_imagen']))

    Campeon.objects.bulk_create(campeones_objs)
    print(f"✅ Insertados {len(campeones_objs)} campeones nuevos.")
    
if __name__ == '__main__':
    importar_campeones()