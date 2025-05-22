import sys
import os
import django
from datetime import datetime
import re
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miweb.settings')
django.setup()

from database.models import Jugador, Equipo
from database.serializers import *
from scraping.Leaguepedia.leaguepedia_teams_players import get_player_data, get_team_data

def parse_fecha(fecha_str):
    if not fecha_str:
        return None

    formatos = ["%B %d, %Y", "%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y"] 

    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            continue

    print(f"Formato de fecha desconocido: {fecha_str}")
    return None

def actualizar_jugadores(data):
    for jugador_data in data:
        nombre = jugador_data.get('jugador')

        try:
            jugador_obj = Jugador.objects.get(nombre=nombre)
        except Jugador.DoesNotExist:
            print(f"Jugador no encontrado en la base de datos: {nombre}")
            continue

        equipo_nombre = jugador_data.get('equipo')
        equipo_obj = Equipo.objects.filter(nombre__iexact=equipo_nombre).first()

        if not equipo_obj:
            print(f"Equipo no encontrado para el jugador: {nombre} (equipo: {equipo_nombre})")
            continue

        # Limitar soloqueue_ids a 100 caracteres
        soloqueue_ids = jugador_data.get('soloqueue_ids')
        if isinstance(soloqueue_ids, list):
            soloqueue_ids = ','.join(soloqueue_ids)
        soloqueue_ids = str(soloqueue_ids)[:100] if soloqueue_ids else None

        # Preparar los datos para el serializer
        datos_actualizados = {
            'id': jugador_obj.id,
            'nombre': jugador_data.get('jugador'),
            'real_name': jugador_data.get('nombre'),
            'equipo': equipo_obj.id,
            'residencia': jugador_data.get('residencia'),
            'rol': jugador_data.get('rol'),
            'pais': jugador_data.get('pais'),
            'nacimiento': parse_fecha(jugador_data.get('nacimiento')),
            'soloqueue_ids': soloqueue_ids,
            'contratado_hasta': parse_fecha(jugador_data.get('contratado_hasta')),
            'contratado_desde': parse_fecha(jugador_data.get('contratado_desde')),
            'imagen': jugador_data.get('imagen'),
            'activo': jugador_obj.activo,
        }

        serializer = JugadorSerializer(instance=jugador_obj, data=datos_actualizados)
        if serializer.is_valid():
            serializer.save()
            print(f"Jugador actualizado: {nombre}")
        else:
            print(f"Errores al actualizar {nombre}: {serializer.errors}")

def parse_fecha_equipo(fecha_str):
    if not fecha_str:
        return None
    # Intenta extraer la parte (YYYY-MM-DD) si está en formato "Texto (YYYY-MM-DD)"
    match = re.search(r'(\d{4}-\d{2}-\d{2})', fecha_str)
    if match:
        return match.group(1)
    try:
        return datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            return datetime.strptime(fecha_str, '%B %d, %Y').date()
        except ValueError:
            return None  # No se pudo parsear
        
def actualizar_equipos_activos(lista_equipos):
    for equipo_data in lista_equipos:
        nombre_equipo_raw = equipo_data.get('nombre_equipo')
        nombre_equipo = nombre_equipo_raw.replace('_', ' ') if nombre_equipo_raw else None
        if not nombre_equipo:
            print("Nombre de equipo no proporcionado, se omite.")
            continue

        # Buscar el equipo por nombre (ignorando mayúsculas/minúsculas)
        equipo_obj = Equipo.objects.filter(nombre__iexact=nombre_equipo).first()

        if not equipo_obj:
            print(f"Equipo no encontrado en la base de datos: {nombre_equipo}, se omite.")
            continue  # Continúa con el siguiente sin crear nuevo equipo

        fecha = parse_fecha_equipo(equipo_data.get('fecha_fundacion'))

        datos = {
            'id': equipo_obj.id,  # Mantener el mismo id existente
            'nombre': nombre_equipo,
            'pais': equipo_data.get('pais'),
            'region': equipo_data.get('region'),
            'propietario': equipo_data.get('propietario'),
            'head_coach': equipo_data.get('head_coach'),
            'partners': equipo_data.get('partners')[:100] if equipo_data.get('partners') else None,
            'fecha_fundacion': fecha,
            'logo': equipo_data.get('logo'),
            'activo': True,
        }

        serializer = EquipoSerializer(instance=equipo_obj, data=datos)

        if serializer.is_valid():
            serializer.save()
            print(f"Equipo actualizado: {nombre_equipo}")
        else:
            print(f"Errores al actualizar {nombre_equipo}: {serializer.errors}")
                       
if __name__ == "__main__":
    #data = get_player_data()
    #actualizar_jugadores(data)
    data = get_team_data()
    actualizar_equipos_activos(data)