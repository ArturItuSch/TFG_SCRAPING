"""
`importar_datos.py`

Este script centraliza y automatiza el proceso de actualización de datos extraídos desde Leaguepedia
hacia la base de datos del proyecto. Su propósito es ejecutar la lógica de scraping definida en otros
módulos y aplicar las actualizaciones correspondientes sobre los modelos `Equipo` y `Jugador`.

Puede ser ejecutado de forma manual o programado mediante un scheduler (por ejemplo, APScheduler).

### Funcionalidades principales:

- `actualizar_todo_equipos_y_jugadores()`: Ejecuta el proceso completo de actualización:
  1. Obtiene equipos históricos (`obtener_equipos_antiguos`) y los marca como inactivos.
  2. Obtiene equipos actuales (`get_team_data`) y los actualiza como activos.
  3. Extrae jugadores actuales (`get_player_data`) y sincroniza sus datos en la base de datos.

- `actualizar_info_equipos(equipos, activo)`: Actualiza una lista de equipos (actuales o antiguos) en el modelo `Equipo`.

- `actualizar_equipos_activos(lista_equipos)`: Versión específica para equipos activos, con formateo adicional.

- `actualizar_jugadores(data)`: Sincroniza los datos de jugadores actuales con la base de datos.

- `parse_fecha()` y `parse_fecha_equipo()`: Funciones auxiliares para convertir fechas desde strings variados a objetos `datetime.date`.

### Uso

Este módulo debe ejecutarse en entornos donde `Django` y los modelos del proyecto estén correctamente
configurados. Puede integrarse en tareas programadas (por ejemplo, crontab o APScheduler) para mantener
los datos actualizados automáticamente.

### Requisitos

- Conexión a Internet (para scraping).
- Acceso a los modelos Django (`Equipo`, `Jugador`) y sus serializers (`EquipoSerializer`, `JugadorSerializer`).
- Rutas correctamente configuradas en `Resources.rutas`.
"""
# Librerías estándar y externas utilizadas
import sys
import os
from datetime import datetime
import re

# Establece la raíz del proyecto para permitir importaciones absolutas fuera del directorio actual
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

# Modelos de Django utilizados para actualizar registros en la base de datos
from database.models import Jugador, Equipo
# Serializers de Django REST Framework para validación y guardado de datos
from database.serializers import *
# Funciones de scraping para obtener datos actuales de equipos y jugadores
from scraping.Leaguepedia.leaguepedia_teams_players import get_player_data, get_team_data
# Función para obtener equipos históricos desde Leaguepedia
from scraping.Leaguepedia.leguepedia_old_sesons import obtener_equipos_antiguos

def parse_fecha(fecha_str):
    """
    Intenta convertir una cadena de texto en una fecha (`datetime.date`), probando múltiples formatos posibles.

    Esta función es útil para normalizar fechas que provienen de fuentes con formatos variados, como Leaguepedia.

    Formatos soportados:
    - "%B %d, %Y" (ej. "March 21, 2022")
    - "%Y-%m-%d" (ej. "2022-03-21")
    - "%d/%m/%Y" (ej. "21/03/2022")
    - "%b %d, %Y" (ej. "Mar 21, 2022")

    Args:
        fecha_str (str): Cadena de texto que representa una fecha.

    Returns:
        datetime.date or None: Fecha convertida si el formato es válido, `None` si no se reconoce el formato.
    """
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

        soloqueue_ids = jugador_data.get('soloqueue_ids')
        if isinstance(soloqueue_ids, list):
            soloqueue_ids = ','.join(soloqueue_ids)
        soloqueue_ids = str(soloqueue_ids)[:100] if soloqueue_ids else None

        image_raw = jugador_data.get('imagen')
        if image_raw: 
            logo = image_raw.replace('\\', '/') 
        else:
            logo = None
        
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
            'imagen': logo,
            'activo': jugador_obj.activo,
        }

        serializer = JugadorSerializer(instance=jugador_obj, data=datos_actualizados)
        if serializer.is_valid():
            serializer.save()
            print(f"Jugador actualizado: {nombre}")
        else:
            print(f"Errores al actualizar {nombre}: {serializer.errors}")

def parse_fecha_equipo(fecha_str):
    """
    Actualiza los datos de jugadores en la base de datos a partir de información recolectada por scraping.

    Para cada jugador recibido:
    - Busca el equipo correspondiente.
    - Verifica que exista un único jugador con ese nombre en ese equipo.
    - Actualiza sus campos personales, competitivos y visuales (como la imagen).
    - Valida y guarda los cambios usando el `JugadorSerializer`.

    Los campos actualizados incluyen:
    - Nombre real, residencia, país, rol, fechas de contrato, imagen.
    - SoloQueue IDs y fecha de nacimiento (convertidos con `parse_fecha`).

    Si hay errores en la estructura de los datos o en la validación del serializer, se informa por consola.

    Args:
        data (list[dict]): Lista de diccionarios con los datos de jugadores obtenidos mediante scraping.
    """
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
    """
    Actualiza los registros de equipos activos en la base de datos con los datos obtenidos por scraping.

    Para cada equipo de la lista:
    - Se normaliza su nombre (`_` → espacio) y se busca en la base de datos.
    - Si existe, se actualizan los campos relevantes: país, región, propietario, entrenador,
      partners, fecha de fundación y logo.
    - El campo `activo` se establece siempre como `True`.

    Si el equipo no se encuentra o si el serializer presenta errores, se imprime el mensaje correspondiente.

    Args:
        lista_equipos (list[dict]): Lista de diccionarios con la información de los equipos extraída desde Leaguepedia.
    """
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
    """
    Actualiza la información de equipos en la base de datos, marcándolos como activos o inactivos según el parámetro.

    Esta función es versátil y se utiliza tanto para equipos actuales (activos=True) como para equipos históricos
    (activos=False). Para cada equipo:
    - Se normaliza el nombre y se busca en el modelo `Equipo`.
    - Si existe, se actualizan campos como país, región, propietario, head coach, partners, logo y fecha de fundación.
    - Se valida y guarda mediante `EquipoSerializer`.

    Args:
        equipos (list[dict]): Lista de diccionarios con información estructurada de equipos.
        activo (bool): Indica si los equipos deben marcarse como activos o inactivos en la base de datos.
    """
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
    """
    Ejecuta el flujo completo de actualización de datos en la base de datos para equipos y jugadores.

    Esta función combina todos los procesos relevantes:
    1. Obtiene y actualiza equipos antiguos desde Leaguepedia (`activo=False`).
    2. Obtiene y actualiza equipos activos de la temporada actual (`activo=True`).
    3. Obtiene y actualiza los jugadores actuales.

    Es ideal para su uso como tarea programada (scheduler) o ejecución manual periódica,
    ya que sincroniza toda la información crítica de la competición en una sola llamada.
    """
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