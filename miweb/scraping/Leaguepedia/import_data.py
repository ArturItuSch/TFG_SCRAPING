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
from scraping.Leaguepedia.leguepedia_old_sesons import obtener_equipos_antiguos

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
        equipo_nombre = jugador_data.get('equipo')

        if not nombre or not equipo_nombre:
            print(f"Faltan datos clave para el jugador: nombre={nombre}, equipo={equipo_nombre}")
            continue

        equipo_obj = Equipo.objects.filter(nombre__iexact=equipo_nombre).first()
        if not equipo_obj:
            print(f"Equipo no encontrado para el jugador: {nombre} (equipo: {equipo_nombre})")
            continue

        jugadores = Jugador.objects.filter(nombre=nombre, equipo=equipo_obj)
        if jugadores.count() == 1:
            jugador_obj = jugadores.first()
        elif jugadores.count() == 0:
            print(f"Jugador no encontrado: {nombre} en equipo: {equipo_nombre}")
            continue
        else:
            print(f"Jugador duplicado: múltiples resultados para '{nombre}' en '{equipo_nombre}', omitiendo actualización.")
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

        equipo_obj = Equipo.objects.filter(nombre__iexact=nombre_equipo).first()

        if not equipo_obj:
            print(f"Equipo no encontrado en la base de datos: {nombre_equipo}, se omite.")
            continue

        fecha = parse_fecha_equipo(equipo_data.get('fecha_fundacion'))

        logo_raw = equipo_data.get('logo')
        # Normalizar ruta logo para usar barras /
        logo = logo_raw.replace('\\', '/') if logo_raw else None

        datos = {
            'id': equipo_obj.id,
            'nombre': nombre_equipo,
            'pais': equipo_data.get('pais'),
            'region': equipo_data.get('region'),
            'propietario': equipo_data.get('propietario'),
            'head_coach': equipo_data.get('head_coach'),
            'partners': equipo_data.get('partners')[:100] if equipo_data.get('partners') else None,
            'fecha_fundacion': fecha,
            'logo': logo,
            'activo': True,
        }

        serializer = EquipoSerializer(instance=equipo_obj, data=datos)

        if serializer.is_valid():
            serializer.save()
            print(f"Equipo actualizado: {nombre_equipo}")
        else:
            print(f"Errores al actualizar {nombre_equipo}: {serializer.errors}")

def actualizar_info_equipos(equipos, activo=False):
    for eq in equipos:
        nombre = eq.get("name", "").replace("_", " ") or eq.get("nombre_equipo", "").replace("_", " ")
        if not nombre:
            print("⚠️ Equipo sin nombre, se omite.")
            continue

        equipo_obj = Equipo.objects.filter(nombre__iexact=nombre).first()
        if not equipo_obj:
            print(f"❌ Equipo no encontrado: {nombre}")
            continue

        logo = eq.get("imagen_url") or eq.get("logo")
        if logo:
            logo = logo.replace("\\", "/")

        datos = {
            'id': equipo_obj.id,
            'nombre': nombre,
            'pais': eq.get('pais'),
            'region': eq.get('region'),
            'propietario': eq.get('propietario'),
            'head_coach': eq.get('head_coach'),
            'partners': eq.get('partners')[:100] if eq.get('partners') else None,
            'fecha_fundacion': parse_fecha_equipo(eq.get('fecha_fundacion')),
            'logo': logo,
            'activo': activo,
        }

        serializer = EquipoSerializer(instance=equipo_obj, data=datos)
        if serializer.is_valid():
            serializer.save()
            print(f"🔄 Equipo actualizado: {nombre} {'(activo)' if activo else '(inactivo)'}")
        else:
            print(f"❌ Error al actualizar {nombre}: {serializer.errors}")

def actualizar_todo_equipos_y_jugadores():
    print("📄 Actualizando info de equipos antiguos...")
    antiguos = obtener_equipos_antiguos()
    actualizar_info_equipos(antiguos, activo=False)

    print("🚀 Actualizando info de equipos actuales...")
    actuales = get_team_data()
    actualizar_info_equipos(actuales, activo=True)

    print("👤 Actualizando jugadores...")
    jugadores = get_player_data()
    actualizar_jugadores(jugadores)

    print("✅ Todo actualizado correctamente.")
                          
if __name__ == "__main__":
    actualizar_todo_equipos_y_jugadores()