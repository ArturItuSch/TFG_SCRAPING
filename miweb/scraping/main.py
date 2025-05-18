import os
import django
import sys
import math
import numpy as np

# Ruta a tu proyecto Django (donde está settings.py)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miweb.settings')
django.setup()
from database.models import *
from scraping.driver import iniciar_driver
from scraping.OracleElexir.csv_process import extract_all_splits, extract_all_series_and_partidos, extract_all_teams, extract_all_players
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

def importar_series_y_partidos():
    from django.db import transaction

    series_dict, partidos_dict = extract_all_series_and_partidos()
    series_objs = []
    partidos_objs = []
    omitted_partidos_ids = []
    num_omitted_series = 0
    num_omitted_partidos = 0

    # 🔹 Cacheamos splits y series existentes
    splits = {split.split_id: split for split in SplitLEC.objects.all()}
    series_existentes = set(Serie.objects.values_list('id', flat=True))
    partidos_existentes = set(Partido.objects.values_list('id', flat=True))

    # 🔸 Primero importar series
    for serie_id, serie_data in series_dict.items():
        if serie_id in series_existentes:
            print(f"La serie {serie_id} ya existe, no se inserta.")
            continue
        raw_split_id = str(serie_data['split_id']).strip().lower()
        if raw_split_id.endswith('nan') or raw_split_id in ('', 'none'):
            year_part = ''.join(filter(str.isdigit, raw_split_id[:4])) or serie_data.get('year', 'unknown')
            split_id_fixed = f"{year_part}unknown"
        else:
            split_id_fixed = raw_split_id

        split_obj = splits.get(split_id_fixed)
        if not split_obj:
            print(f"Split {split_id_fixed} no existe para la serie {serie_id}, se omite.")
            num_omitted_series += 1
            continue

        patch = serie_data.get('patch')
        if patch is not None and (isinstance(patch, float) and math.isnan(patch)):
            patch = None

        serializer = SerieSerializer(data={
            'id': serie_id,
            'split': split_obj.pk,
            'num_partidos': serie_data.get('num_partidos'),
            'patch': patch,
            'dia': serie_data.get('dia'),
        })

        if serializer.is_valid():
            series_objs.append(Serie(**serializer.validated_data))
        else:
            print(f"Error en datos de la serie {serie_id}: {serializer.errors}")

    # 🔹 Insertar series en lote
    BATCH_SIZE = 1000
    for i in range(0, len(series_objs), BATCH_SIZE):
        with transaction.atomic():
            Serie.objects.bulk_create(series_objs[i:i + BATCH_SIZE])
        print(f"✅ Insertadas {min(i + BATCH_SIZE, len(series_objs))} de {len(series_objs)} series.")

    print(f"✅ Total series insertadas: {len(series_objs)}")
    print(f"❌ Series omitidas por split no encontrado: {num_omitted_series}")

    # 🔸 Cacheamos las series ya en base de datos (incluyendo recién insertadas)
    series_cache = {serie.id: serie for serie in Serie.objects.all()}

    # 🔸 Ahora importar partidos
    for partido_id, partido_data in partidos_dict.items():
        if partido_id in partidos_existentes:
            print(f"El partido {partido_id} ya existe, no se inserta.")
            continue

        serie_obj = series_cache.get(partido_data['serie_id'])
        if not serie_obj:
            print(f"La serie {partido_data['serie_id']} no existe para el partido {partido_id}, se omite.")
            num_omitted_partidos += 1
            omitted_partidos_ids.append(partido_id)
            continue

        def get_equipo_obj(equipo_id):
            if str(equipo_id).startswith("Unknown_"):
                nombre_equipo = equipo_id.split("Unknown_")[1]
                try:
                    return Equipo.objects.get(nombre=nombre_equipo)
                except Equipo.DoesNotExist:
                    return None
            try:
                return Equipo.objects.get(id=equipo_id)
            except Equipo.DoesNotExist:
                return None

        equipo_azul_obj = get_equipo_obj(partido_data['equipo_azul'])
        equipo_rojo_obj = get_equipo_obj(partido_data['equipo_rojo'])
        equipo_ganador_obj = get_equipo_obj(partido_data['equipo_ganador'])

        # Si alguno de los equipos no existe, omitimos este partido
        if None in (equipo_azul_obj, equipo_rojo_obj, equipo_ganador_obj):
            print(f"⚠️ Uno o más equipos no encontrados para el partido {partido_id}")
            num_omitted_partidos += 1
            omitted_partidos_ids.append(partido_id)
            continue

        serializer = PartidoSerializer(data={
            'id': partido_id,
            'serie': serie_obj.pk,
            'hora': partido_data['hora'],
            'orden': partido_data['orden'],
            'duracion': partido_data['duracion'],
            'equipo_azul': equipo_azul_obj.pk,
            'equipo_rojo': equipo_rojo_obj.pk,
            'equipo_ganador': equipo_ganador_obj.pk
        })

        if serializer.is_valid():
            partidos_objs.append(Partido(**serializer.validated_data))
        else:
            print(f"Error en datos del partido {partido_id}: {serializer.errors}")

    for i in range(0, len(partidos_objs), BATCH_SIZE):
        with transaction.atomic():
            Partido.objects.bulk_create(partidos_objs[i:i + BATCH_SIZE])
        print(f"✅ Insertados {min(i + BATCH_SIZE, len(partidos_objs))} de {len(partidos_objs)} partidos.")

    print(f"✅ Total partidos insertados: {len(partidos_objs)}")
    print(f"❌ Partidos omitidos por serie no encontrada: {num_omitted_partidos}")
    if omitted_partidos_ids:
        print(f"IDs de partidos omitidos por serie no encontrada: {omitted_partidos_ids}")

def importar_equipos():
    equipos_dict = extract_all_teams()

    equipos_objs = []
    for equipo_id, equipo_data in equipos_dict.items():
        if not Equipo.objects.filter(id=equipo_id).exists():
            serializer = EquipoSerializer(data={
                'id': equipo_data['id'],
                'nombre': equipo_data['name'],
                'pais': None,
                'region': None,
                'propietario': None,
                'head_coach': None,
                'partners': None,
                'fecha_fundacion': None,
                'logo': None,
                'activo': equipo_data.get('activo', False)
            })
            if serializer.is_valid():
                equipos_objs.append(Equipo(**serializer.validated_data))
            else:
                print(f"❌ Error en datos del equipo {equipo_id}: {serializer.errors}")

    if equipos_objs:
        Equipo.objects.bulk_create(equipos_objs)
    print(f"✅ Insertados {len(equipos_objs)} equipos nuevos.")

def importar_jugadores():
    jugadores_dict = extract_all_players()  
    jugadores_objs = []
    actualizados = 0

    # Cacheamos equipos para asignar FK sin consultas repetidas
    equipos_cache = {eq.id: eq for eq in Equipo.objects.all()}

    for jugador_id, jugador_data in jugadores_dict.items():
        equipo_obj = equipos_cache.get(jugador_data['equipo_id'])

        jugador_qs = Jugador.objects.filter(id=jugador_id)
        if jugador_qs.exists():
            # Actualizamos equipo si cambió
            jugador = jugador_qs.first()
            if jugador.equipo != equipo_obj:
                jugador.equipo = equipo_obj
                jugador.save(update_fields=['equipo'])
                actualizados += 1
        else:
            serializer = JugadorSerializer(data={
                'id': jugador_id,
                'nombre': jugador_data.get('nombre'),
                'equipo': equipo_obj.pk if equipo_obj else None,
                'real_name': None,
                'residencia': None,
                'rol': None,
                'pais': None,
                'nacimiento': None,
                'soloqueue_ids': None,
                'contratado_hasta': None,
                'contratado_desde': None,
                'imagen': None,
                'activo': jugador_data.get('activo', False)
            })
            if serializer.is_valid():
                jugadores_objs.append(Jugador(**serializer.validated_data))
            else:
                print(f"❌ Error en datos del jugador {jugador_id}: {serializer.errors}")

    if jugadores_objs:
        Jugador.objects.bulk_create(jugadores_objs)

    print(f"✅ Insertados {len(jugadores_objs)} jugadores nuevos.")
    print(f"🔄 Actualizados {actualizados} jugadores existentes con nuevo equipo.")
           
if __name__ == '__main__':
    #importar_campeones()
    #importar_splits()
    importar_equipos()
    importar_jugadores() 
    importar_series_y_partidos()