import unicodedata
import re
import os
import django
import sys
import math

# Ruta a tu proyecto Django (donde está settings.py)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from database.models import *
from scraping.driver import iniciar_driver
from scraping.OracleElexir.csv_process import *
from scraping.GOL.scraping_gol import get_champions_information
from database.serializers import *
from Resources.rutas import DICCIONARIO_CLAVES


def limpiar_valor(valor):
    if isinstance(valor, float) and math.isnan(valor):
        return None
    return valor

def importar_campeones():
    driver = iniciar_driver()
    campeones_data = get_champions_information(driver)
    driver.quit()

    campeones_nuevos = []
    campeones_actualizados = 0

    for champ in campeones_data:
        try:
            obj = Campeon.objects.get(nombre=champ['nombre'])
            actualizado = False
            if obj.imagen is None and champ['ruta_imagen']:
                obj.imagen = champ['ruta_imagen']
                actualizado = True

            if actualizado:
                obj.save()
                campeones_actualizados += 1

        except Campeon.DoesNotExist:
            if champ['ruta_imagen']:  # Solo intentamos insertar si tiene ruta válida
                serializer = CampeonSerializer(data={
                    'id': champ['id'],
                    'nombre': champ['nombre'],
                    'imagen': champ['ruta_imagen'],
                })
                if serializer.is_valid():
                    campeones_nuevos.append(Campeon(**serializer.validated_data))
                else:
                    print(f"❌ Error en datos de {champ['nombre']}: {serializer.errors}")
            else:
                print(f"⏭️ Campeón '{champ['nombre']}' omitido: sin ruta de imagen.")
    if campeones_nuevos:
        Campeon.objects.bulk_create(campeones_nuevos)

    print(f"✅ Insertados {len(campeones_nuevos)} campeones nuevos.")
    
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
            'playoffs': serie_data.get('playoffs', False),
        })

        if serializer.is_valid():
            series_objs.append(Serie(**serializer.validated_data))
        else:
            print(f"Error en datos de la serie {serie_id}: {serializer.errors}")

    BATCH_SIZE = 1000
    for i in range(0, len(series_objs), BATCH_SIZE):
        with transaction.atomic():
            Serie.objects.bulk_create(series_objs[i:i + BATCH_SIZE])
        print(f"✅ Insertadas {min(i + BATCH_SIZE, len(series_objs))} de {len(series_objs)} series.")

    print(f"✅ Insertadas {len(series_objs)} series nuevas.")
    print(f"❌ Series omitidas por split no encontrado: {num_omitted_series}")

    series_cache = {serie.id: serie for serie in Serie.objects.all()}

    for partido_id, partido_data in partidos_dict.items():
        if partido_id in partidos_existentes:
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

def importar_jugadores_en_partida():
    jugadores_en_partida_data = extract_all_jugadores_en_partida()
    jugadores_en_partida_objs = []
    actualizados = 0
    insertados = 0


    # Cache para FK
    jugadores_cache = {j.id: j for j in Jugador.objects.all()}
    partidos_cache = {p.id: p for p in Partido.objects.all()}
    campeones_cache = {c.nombre.replace("'", "").lower(): c for c in Campeon.objects.all()}

    print(f"Cache jugadores cargados: {len(jugadores_cache)}")
    print(f"Cache partidos cargados: {len(partidos_cache)}")
    print(f"Cache campeones cargados: {len(campeones_cache)}")

    # Pre-cargar combinaciones existentes para evitar get() en loop
    claves_existentes = set(
        JugadorEnPartida.objects.values_list('jugador_id', 'partido_id', 'campeon_id')
    )

    batch_size = 1000
    DEFAULT_JUGADOR_ID = "unknown"
    for i, data in enumerate(jugadores_en_partida_data):
        jugador_id = data['jugador']
        partido_id = data['partido']
        campeon_nombre = data['campeon'].replace("'", "").lower()
        if campeon_nombre == 'nunu & willump':
            campeon_nombre = 'nunu'

        if not jugador_id or str(jugador_id).lower() == 'nan':
            print(f"⚠️  ID inválido detectado: '{jugador_id}', se usará jugador Unknown por defecto.")
            jugador_id = DEFAULT_JUGADOR_ID
            
        jugador_obj = jugadores_cache.get(jugador_id)
        partido_obj = partidos_cache.get(partido_id)
        campeon_obj = campeones_cache.get(campeon_nombre)

        if not jugador_obj:
            jugador_obj, _ = Jugador.objects.get_or_create(
                id=jugador_id,
                defaults={"nombre": "Unknown"},
            )
            jugadores_cache[jugador_id] = jugador_obj

        
        if not partido_obj:
            print(f"❌ No se encontró partido en cache para id: '{partido_id}' (tipo: {type(partido_id)})")
            print(f"   Repr partido_id: {repr(partido_id)}")
            continue

        if not campeon_obj:
            print(f"❌ No se encontró campeón en cache para nombre: '{campeon_nombre}' (tipo: {type(campeon_nombre)})")
            print(f"   Repr campeon_nombre: {repr(campeon_nombre)}")
            continue

        clave = (jugador_obj.pk, partido_obj.pk, campeon_obj.pk)
        if clave in claves_existentes:
            actualizados += 1
            continue  # Ya existe, no insertar

        # Crear instancia para bulk_create
        obj = JugadorEnPartida(
            jugador=jugador_obj,
            partido=partido_obj,
            campeon=campeon_obj,
            position=limpiar_valor(data.get('position')),
            side=limpiar_valor(data.get('side')),
            kills=limpiar_valor(data.get('kills')),
            deaths=limpiar_valor(data.get('deaths')),
            assists=limpiar_valor(data.get('assists')),
            doublekills=limpiar_valor(data.get('doublekills')),
            triplekills=limpiar_valor(data.get('triplekills')),
            quadrakills=limpiar_valor(data.get('quadrakills')),
            pentakills=limpiar_valor(data.get('pentakills')),
            firstbloodkill=limpiar_valor(data.get('firstbloodkill')),
            firstbloodassist=limpiar_valor(data.get('firstbloodassist')),
            firstbloodvictim=limpiar_valor(data.get('firstbloodvictim')),
            damagetochampions=limpiar_valor(data.get('damagetochampions')),
            damagetaken=limpiar_valor(data.get('damagetaken')),
            wardsplaced=limpiar_valor(data.get('wardsplaced')),
            wardskilled=limpiar_valor(data.get('wardskilled')),
            controlwardsbought=limpiar_valor(data.get('controlwardsbought')),
            visionscore=limpiar_valor(data.get('visionscore')),
            totalgold=limpiar_valor(data.get('totalgold')),
            total_cs=limpiar_valor(data.get('total_cs')),
            minionkills=limpiar_valor(data.get('minionkills')),
            monsterkills=limpiar_valor(data.get('monsterkills')),
            goldat10=limpiar_valor(data.get('goldat10')),
            xpat10=limpiar_valor(data.get('xpat10')),
            csat10=limpiar_valor(data.get('csat10')),
            killsat10=limpiar_valor(data.get('killsat10')),
            assistsat10=limpiar_valor(data.get('assistsat10')),
            deathsat10=limpiar_valor(data.get('deathsat10')),
            goldat15=limpiar_valor(data.get('goldat15')),
            xpat15=limpiar_valor(data.get('xpat15')),
            csat15=limpiar_valor(data.get('csat15')),
            killsat15=limpiar_valor(data.get('killsat15')),
            assistsat15=limpiar_valor(data.get('assistsat15')),
            deathsat15=limpiar_valor(data.get('deathsat15')),
            goldat20=limpiar_valor(data.get('goldat20')),
            xpat20=limpiar_valor(data.get('xpat20')),
            csat20=limpiar_valor(data.get('csat20')),
            killsat20=limpiar_valor(data.get('killsat20')),
            assistsat20=limpiar_valor(data.get('assistsat20')),
            deathsat20=limpiar_valor(data.get('deathsat20')),
            goldat25=limpiar_valor(data.get('goldat25')),
            xpat25=limpiar_valor(data.get('xpat25')),
            csat25=limpiar_valor(data.get('csat25')),
            killsat25=limpiar_valor(data.get('killsat25')),
            assistsat25=limpiar_valor(data.get('assistsat25')),
            deathsat25=limpiar_valor(data.get('deathsat25')),
        )
        jugadores_en_partida_objs.append(obj)

        # Insertar en bloques para evitar usar demasiada memoria
        if len(jugadores_en_partida_objs) >= batch_size:
            JugadorEnPartida.objects.bulk_create(jugadores_en_partida_objs)
            insertados += len(jugadores_en_partida_objs)
            jugadores_en_partida_objs = []

    # Insertar los restantes
    if jugadores_en_partida_objs:
        JugadorEnPartida.objects.bulk_create(jugadores_en_partida_objs)
        insertados += len(jugadores_en_partida_objs)
    
    print(f"✅ Insertados {insertados} registros nuevos de jugadores en partida.")
    print(f"🔄 Actualizados {actualizados} registros existentes.")
    
def importar_selecciones(batch_size=1000):
    datos = extraer_all_baneos_picks()
    actualizados = 0
    errores = 0
    insertados = 0
    lote_actual = []
    selecciones_vistas = set()

    # Cache
    equipos_cache = {eq.id: eq for eq in Equipo.objects.all()}
    equipos_nombre_cache = {eq.nombre.strip().lower(): eq for eq in Equipo.objects.all()}
    partidos_cache = {p.id: p for p in Partido.objects.all()}

    def normalizar_nombre(nombre):
        if not nombre:
            return ""

        nombre = nombre.lower().strip()
        nombre = nombre.replace("&", "and")
        nombre = nombre.replace("'", "")
        nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode('utf-8')
        nombre = re.sub(r'[^a-z0-9]', '', nombre)

        if nombre == "nunuandwillump":
            return "nunu"

        return nombre
    
    campeones_cache = {
        normalizar_nombre(c.nombre): c
        for c in Campeon.objects.all()
    }
    print(f"📦 Procesando {len(datos)} registros de selecciones en lotes de {batch_size}...")

    for i, registro in enumerate(datos):
        equipo_id = registro['equipo']
        equipo_nombre = registro.get('equipo_nombre', '').strip().lower()
        partido_id = registro['partido']
        nombre_baneado = normalizar_nombre(registro.get('campeon_baneado'))
        nombre_seleccionado = normalizar_nombre(registro.get('campeon_seleccionado'))

        equipo = equipos_cache.get(equipo_id)
        if not equipo and equipo_nombre:
            equipo = equipos_nombre_cache.get(equipo_nombre)

        partido = partidos_cache.get(partido_id)

        if not equipo or not partido:
            print(f"[{i}] ⚠️ FK faltante: game={partido_id}, equipo_id={equipo_id}, nombre='{equipo_nombre}'")
            errores += 1
            continue

        campeon_baneado = campeones_cache.get(nombre_baneado)
        campeon_seleccionado = campeones_cache.get(nombre_seleccionado)

        if nombre_baneado and not campeon_baneado:
            print(f"[{i}] ❗ Campeón baneado no encontrado: '{nombre_baneado}' (original: '{registro.get('campeon_baneado')}')")

        if nombre_seleccionado and not campeon_seleccionado:
            print(f"[{i}] ❗ Campeón seleccionado no encontrado: '{nombre_seleccionado}' (original: '{registro.get('campeon_seleccionado')}')")

        if not campeon_baneado and not campeon_seleccionado:
            print(f"[{i}] ⛔ Sin pick ni ban válido → se omite.")
            errores += 1
            continue

        if campeon_seleccionado:
            existe = Seleccion.objects.filter(
                equipo=equipo,
                partido=partido,
                campeon_seleccionado=campeon_seleccionado
            ).exists()
            if existe:
                actualizados += 1
                continue

        clave_unica = (equipo.id, partido.id, campeon_seleccionado.id if campeon_seleccionado else None)
        if clave_unica in selecciones_vistas:
            continue

        selecciones_vistas.add(clave_unica)

        lote_actual.append(Seleccion(
            equipo=equipo,
            partido=partido,
            seleccion=registro.get('seleccion'),
            campeon_seleccionado=campeon_seleccionado,
            baneo=registro.get('ban'),
            campeon_baneado=campeon_baneado
        ))

        if len(lote_actual) >= batch_size:
            Seleccion.objects.bulk_create(lote_actual)
            insertados += len(lote_actual)
            print(f"✅ Insertado lote de {len(lote_actual)} → Total: {insertados}")
            lote_actual = []

    # Lote final
    if lote_actual:
        Seleccion.objects.bulk_create(lote_actual)
        insertados += len(lote_actual)
        print(f"✅ Insertado lote final de {len(lote_actual)} → Total: {insertados}")

    # Resumen
    print("\n📊 RESUMEN FINAL")
    print(f"✅ Selecciones nuevas insertadas: {insertados}")
    print(f"🔄 Ya existentes (omitidos): {actualizados}")
    print(f"❌ Registros descartados por errores: {errores}")


def importar_objetivos_neutrales(batch_size=1000):
    datos = extract_objetivos_neutrales_matados()  # Ahora devuelve lista con dicts agrupados por equipo y partida

    objs_to_create = []
    objs_to_update = []
    ya_existentes = 0

    for dato in datos:
        gameid = dato['gameid']
        teamid = dato['teamid']
        teamname = dato.get('teamname')

        try:
            partido = Partido.objects.get(id=gameid)

            try:
                equipo = Equipo.objects.get(id=teamid)
            except Equipo.DoesNotExist:
                if teamname:
                    try:
                        equipo = Equipo.objects.get(nombre=teamname)
                    except Equipo.DoesNotExist:
                        print(f"❌ No se encontró Equipo con id {teamid} ni con nombre '{teamname}'")
                        continue
                else:
                    print(f"❌ No se encontró Equipo con id {teamid} y no se proporcionó teamname")
                    continue

            # Buscamos si ya existe registro para esa partida y equipo
            try:
                obj = ObjetivosNeutrales.objects.get(partida=partido, equipo=equipo)
                # Actualizamos campos con datos del diccionario
                for campo, valor in dato.items():
                    if campo not in ['gameid', 'teamid', 'teamname']:
                        setattr(obj, campo, int(valor))
                objs_to_update.append(obj)
                ya_existentes += 1
            except ObjetivosNeutrales.DoesNotExist:
                # Creamos uno nuevo
                campos = {campo: int(valor) for campo, valor in dato.items() if campo not in ['gameid', 'teamid', 'teamname']}
                obj = ObjetivosNeutrales(partida=partido, equipo=equipo, **campos)
                objs_to_create.append(obj)

        except Partido.DoesNotExist:
            print(f"❌ No se encontró Partido con id {gameid}")
            continue
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            continue

        # Insertar/actualizar en lotes
        if len(objs_to_create) >= batch_size:
            ObjetivosNeutrales.objects.bulk_create(objs_to_create)
            print(f"✅ Insertados {len(objs_to_create)} Objetivos Neutrales en lote.")
            objs_to_create = []

        if len(objs_to_update) >= batch_size:
            ObjetivosNeutrales.objects.bulk_update(objs_to_update, fields=[
                'firstdragon', 'dragons', 'elementaldrakes', 'infernals', 'mountains', 'clouds', 'oceans',
                'chemtechs', 'hextechs', 'dragons_type_unknown', 'elders', 'firstherald', 'heralds',
                'void_grubs', 'firstbaron', 'barons', 'firsttower', 'towers', 'firstmidtower',
                'firsttothreetowers', 'turretplates', 'inhibitors'
            ])
            print(f"🔄 Actualizados {len(objs_to_update)} registros en lote.")
            objs_to_update = []

    # Insertar o actualizar lo que queda
    if objs_to_create:
        ObjetivosNeutrales.objects.bulk_create(objs_to_create)
        print(f"✅ Insertados {len(objs_to_create)} registros de Objetivos Neutrales.")

    if objs_to_update:
        ObjetivosNeutrales.objects.bulk_update(objs_to_update, fields=[
            'firstdragon', 'dragons', 'elementaldrakes', 'infernals', 'mountains', 'clouds', 'oceans',
            'chemtechs', 'hextechs', 'dragons_type_unknown', 'elders', 'firstherald', 'heralds',
            'void_grubs', 'firstbaron', 'barons', 'firsttower', 'towers', 'firstmidtower',
            'firsttothreetowers', 'turretplates', 'inhibitors'
        ])
        print(f"🔄 Actualizados {len(objs_to_update)} registros finales.")

    print(f"🔄 Ignorados {ya_existentes} registros ya existentes.")

