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
from scraping.OracleElexir.csv_process import extract_all_splits
from scraping.GOL.scraping_gol import get_champions_information
from database.serializers import *



def importar_campeones():
    driver = iniciar_driver()
    campeones_data = get_champions_information(driver)
    driver.quit()
    
    campeones_objs = []
    for champ in campeones_data:
        if not Campeon.objects.filter(nombre=champ['nombre']).exists():
            serializer = CampeonSerializer(data={
                'id': champ['id'],
                'nombre': champ['nombre'],
                'ruta_imagen': champ['ruta_imagen'],
            })
            if serializer.is_valid():
                campeones_objs.append(Campeon(**serializer.validated_data))
            else:
                print(f"Error en datos de {champ['nombre']}: {serializer.errors}")
    
    if campeones_objs:
        Campeon.objects.bulk_create(campeones_objs)
    print(f"✅ Insertados {len(campeones_objs)} campeones nuevos.")
    
def importar_splits():
    splits_dict = extract_all_splits()
    
    splits_objs = []
    for split_id, split_data in splits_dict.items():
        if not SplitLEC.objects.filter(split_id=split_id).exists():
            serializer = SplitLECSerializer(data={
                'split_type': split_data['season'],
                'year': int(split_data['year']),
                'league': split_data['league'],
                'split_id': split_data['id'],
            })
            if serializer.is_valid():
                splits_objs.append(SplitLEC(**serializer.validated_data))
            else:
                print(f"Error en datos del split {split_id}: {serializer.errors}")
    
    if splits_objs:
        SplitLEC.objects.bulk_create(splits_objs)
    print(f"✅ Insertados {len(splits_objs)} splits nuevos.")

if __name__ == '__main__':
    importar_campeones()
    importar_splits()