from datetime import datetime
import pandas as pd
import sys
import os
import json
import uuid
import re

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)
from Resources.rutas import *

CARPETA_CSV = os.path.join(CARPETA_CSV_GAMES)
CARPETA_CSV_LEC = os.path.join(CARPETA_CSV, 'LEC')
CARPETA_CSV_LCK = os.path.join(CARPETA_CSV, 'LCK')
IDS_EQUIPOS_DICCIONARIO = os.path.join(DICCIONARIO_CLAVES, 'taem_ids.json')
IDS_PLAYER_DICCIONARIO = os.path.join(DICCIONARIO_CLAVES, 'player_ids.json')
IDS_PARTIDOS_DICCIONARIO = os.path.join(DICCIONARIO_CLAVES, 'partidos_ids.json')
JSON_EQUIPOS = os.path.join(JSON_INSTALATION_TEAMS, 'teams_data_leguepedia.json')
JSON_JUGADORES = os.path.join(JSON_INSTALATION_PLAYERS, 'players_data_leguepedia.json')
JSON_PARTIDOS = os.path.join(JSON_GAMES)
JSON_SPLITS_LEC = os.path.join(JSON_INSTALATION_SPLITS_LEC)

def borrar_csv_2025_lol_esports(carpeta_base):
    for root, dirs, files in os.walk(carpeta_base):
        for file in files:
            if file.startswith("2025_LoL_esports") and file.endswith(".csv"):
                ruta_completa = os.path.join(root, file)
                try:
                    os.remove(ruta_completa)
                    print(f"Archivo eliminado: {ruta_completa}")
                except Exception as e:
                    print(f"No se pudo eliminar {ruta_completa}: {e}")
                    
def filtrar_ligas_automaticamente(carpeta_csv, carpeta_salida_base, project_root):
    os.makedirs(carpeta_salida_base, exist_ok=True)

    equivalencias_ligas = {
        'EU LCS': 'LEC',
        'LEC': 'LEC',
        # Puedes añadir más equivalencias aquí si quieres agrupar otras ligas
    }

    archivos_csv = [
        os.path.relpath(os.path.join(carpeta_csv, archivo), start=project_root)
        for archivo in os.listdir(carpeta_csv)
        if archivo.endswith('.csv') and os.path.isfile(os.path.join(carpeta_csv, archivo))
    ]

    for archivo in archivos_csv:
        ruta_absoluta = os.path.join(project_root, archivo)
        try:
            df = pd.read_csv(ruta_absoluta, dtype={2: str})

            if 'league' in df.columns:
                nombre_base = os.path.splitext(os.path.basename(archivo))[0]
                anio = nombre_base[:4] if nombre_base[:4].isdigit() else 'unknown'

                # Obtener las ligas únicas reales
                ligas_reales = df['league'].unique()

                # Crear un diccionario para agrupar ligas por equivalencia
                ligas_agrupadas = {}
                for liga_real in ligas_reales:
                    grupo = equivalencias_ligas.get(liga_real, liga_real)
                    if grupo not in ligas_agrupadas:
                        ligas_agrupadas[grupo] = []
                    ligas_agrupadas[grupo].append(liga_real)

                # Ahora iteramos por grupos (por ejemplo, 'LEC') y procesamos todos los archivos que pertenezcan a esos nombres originales
                for grupo, ligas_del_grupo in ligas_agrupadas.items():
                    datos_filtrados = df[df['league'].isin(ligas_del_grupo)]

                    if not datos_filtrados.empty:
                        carpeta_salida = os.path.join(carpeta_salida_base, grupo, anio)
                        os.makedirs(carpeta_salida, exist_ok=True)

                        nombre_archivo = f"{nombre_base}_{grupo}.csv"
                        ruta_salida = os.path.join(carpeta_salida, nombre_archivo)

                        datos_filtrados.to_csv(ruta_salida, index=False)
                        print(f"Archivo guardado: {ruta_salida}")
            else:
                print(f"El archivo {archivo} no contiene la columna 'league'.")
        except Exception as e:
            print(f"Error procesando {archivo}: {e}")
 
# Función para cargar o inicializar un diccionario desde JSON
def cargar_diccionario(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            dic = json.load(f)
            print(f"Diccionario cargado de {ruta} con {len(dic)} entradas.")
            return dic
    print(f"No existe el archivo {ruta}, se crea diccionario vacío.")
    return {}

# Función para guardar un diccionario en JSON
def guardar_diccionario(diccionario, ruta):
    try:
        directorio = os.path.dirname(ruta)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)

        with open(ruta, 'w', encoding='utf-8') as f:
            json.dump(diccionario, f, ensure_ascii=False, indent=4)

        print(f"✅ Diccionario guardado correctamente en {ruta} con {len(diccionario)} entradas.")
    except Exception as e:
        print(f"❌ Error al guardar el diccionario en {ruta}: {e}")
        
        
def es_uuid(valor):
    if not isinstance(valor, str):
        return False
    patron_uuid = re.compile(
        r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.I
    )
    return bool(patron_uuid.match(valor))

def extraer_hash_o_uuid(valor):
    if not isinstance(valor, str):
        return None
    valor = valor.strip()

    if es_uuid(valor):
        return valor

    # Si el valor es tipo "oe:player:..." -> extrae la parte final
    if ":" in valor:
        partes = valor.split(":")
        posible_hash = partes[-1]
        if re.fullmatch(r"[a-fA-F0-9]{32}", posible_hash):
            return posible_hash

    # Si parece ser un hash directamente (32 chars hex)
    if re.fullmatch(r"[a-fA-F0-9]{32}", valor):
        return valor

    return None  # No se puede usar como clave

def obtener_o_crear_id(diccionario, valor_original):
    id_base = extraer_hash_o_uuid(valor_original)

    if id_base is None:
        # Aquí usamos el valor original como clave para mapear un UUID persistente
        if valor_original not in diccionario:
            nuevo_uuid = str(uuid.uuid4())
            diccionario[valor_original] = nuevo_uuid
            print(f"Clave no estándar '{valor_original}' añadida con UUID: {nuevo_uuid}")
        return diccionario[valor_original]

    if es_uuid(valor_original):
        return valor_original

    if id_base not in diccionario:
        nuevo_uuid = str(uuid.uuid4())
        diccionario[id_base] = nuevo_uuid
        print(f"Añadido nuevo mapeo: {id_base} -> {nuevo_uuid}")

    return diccionario[id_base]
         
def obtener_rutas_csv(carpeta):
    rutas_csv = []
    for year in os.listdir(carpeta):
        year_path = os.path.join(carpeta, year)
        if os.path.isdir(year_path):
            for archivo in os.listdir(year_path):
                if archivo.endswith('.csv'):
                    archivo_path = os.path.join(year_path, archivo)
                    rutas_csv.append(archivo_path)
    rutas_csv.sort() 
    return rutas_csv

def reemplazar_ids(df, columna, diccionario):
    if columna not in df.columns:
        return
    nuevos_ids = []
    for val in df[columna]:
        nuevos_ids.append(obtener_o_crear_id(diccionario, val))
    df[columna] = nuevos_ids

def procesar_todos_los_csvs_en_lec():
    dicc_teams = cargar_diccionario(IDS_EQUIPOS_DICCIONARIO)
    dicc_players = cargar_diccionario(IDS_PLAYER_DICCIONARIO)
    dicc_games = cargar_diccionario(IDS_PARTIDOS_DICCIONARIO)

    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)
    for ruta in rutas_csv:
        df = pd.read_csv(ruta, dtype=str)

        if 'teamid' in df.columns and 'teamname' in df.columns:
            reemplazar_ids(df, 'teamid', dicc_teams)
        if 'playerid' in df.columns and 'playername' in df.columns:
            reemplazar_ids(df, 'playerid', dicc_players)
        if 'gameid' in df.columns:
            reemplazar_ids(df, 'gameid', dicc_games)

        df.to_csv(ruta, index=False)

    guardar_diccionario(dicc_teams, IDS_EQUIPOS_DICCIONARIO)
    guardar_diccionario(dicc_players, IDS_PLAYER_DICCIONARIO)
    guardar_diccionario(dicc_games, IDS_PARTIDOS_DICCIONARIO)

    return f"✅ Procesados {len(rutas_csv)} CSVs y actualizados los IDs."
        
            
def extract_all_splits():
    all_splits = {}

    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)

    for csv_file_path in rutas_csv:
        try:
            nombre_archivo = os.path.basename(csv_file_path)
            year_from_filename = nombre_archivo.split('_')[0]
            df = pd.read_csv(csv_file_path)
            if 'year' in df.columns:
                df = df[df['year'].astype(str) == year_from_filename]
            else:
                continue

            if df.empty:
                continue
            df['split'] = df['split'].fillna('unknown')
            splits = df['split'].drop_duplicates()
            year = os.path.basename(csv_file_path).split('_')[0]
            league = df['league'].iloc[0] if 'league' in df.columns else 'unknown'

            for split in splits:
                split = str(split).strip().lower() if split else 'unknown'
                split_id = f"{year}{split}"

                if split_id not in all_splits:
                    all_splits[split_id] = {
                        "id": split_id,
                        "league": league,
                        "year": year,
                        "season": split
                    }

        except Exception as e:
            print(f"Error al procesar el archivo {csv_file_path}: {e}")

    return all_splits

def extract_all_series_and_partidos():
    all_series = {}
    all_partidos = {}

    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)
    serie_counters = {}

    for csv_file_path in rutas_csv:
        try:
            df = pd.read_csv(csv_file_path)
            df = df.reset_index(drop=True)

            current_serie_id = None
            current_serie_partidos = []
            last_gameid = None

            for idx, row in df.iterrows():
                gameid = row['gameid']
                game = row['game']
                year = os.path.basename(csv_file_path).split('_')[0]
                split = str(row['split']).strip().lower()
                patch = row.get('patch')
                fecha_completa = row.get('date')
                fecha_solo_dia = None
                playoffs = bool(row.get('playoffs', 0))

                if pd.notna(fecha_completa):
                    try:
                        fecha_solo_dia = datetime.strptime(fecha_completa, '%Y-%m-%d %H:%M:%S').date()
                    except ValueError:
                        print(f"❌ Formato de fecha inválido: {fecha_completa}")

                if (gameid != last_gameid and game == 1) or current_serie_id is None:
                    # Guardar la serie anterior
                    if current_serie_id and current_serie_partidos:
                        all_series[current_serie_id] = {
                            'split_id': f"{year}{split}",
                            'num_partidos': len(current_serie_partidos),
                            'patch': patch,
                            'dia': fecha_solo_dia,
                            'playoffs': playoffs
                        }

                        df_serie = df[df['gameid'].isin(current_serie_partidos)]
                        partidos_en_serie = extract_partidos_de_serie(current_serie_id, df_serie)
                        all_partidos.update(partidos_en_serie)
                    
                    # Nueva serie
                    key = (year, split)
                    serie_counters[key] = serie_counters.get(key, 0) + 1
                    current_serie_id = f"{year}_{split}_{serie_counters[key]}"
                    current_serie_partidos = [gameid]
                    current_playoffs = playoffs
                else:
                    if gameid not in current_serie_partidos:
                        current_serie_partidos.append(gameid)

                last_gameid = gameid

            # Guardar última serie
            if current_serie_id and current_serie_partidos:
                all_series[current_serie_id] = {
                    'split_id': f"{year}{split}",
                    'num_partidos': len(current_serie_partidos),
                    'patch': patch,
                    'dia': fecha_solo_dia,
                    'playoffs': current_playoffs
                }

                df_serie = df[df['gameid'].isin(current_serie_partidos)]
                partidos_en_serie = extract_partidos_de_serie(current_serie_id, df_serie)
                all_partidos.update(partidos_en_serie)

        except Exception as e:
            print(f"❌ Error al procesar archivo {csv_file_path}: {e}")

    print(f"📊 Total series extraídas: {len(all_series)}")
    print(f"📊 Total partidos extraídos: {len(all_partidos)}")
    return all_series, all_partidos



def extract_partidos_de_serie(serie_id, serie_df):
    partidos = {}

    grouped = serie_df.groupby('gameid')

    for gameid, group in grouped:
        try:
            hora = datetime.strptime(group.iloc[0]['date'], "%Y-%m-%d %H:%M:%S").time()
        except Exception as e:
            print(f"⚠️ Error al parsear hora para gameid {gameid}: {e}")
            hora = None

        equipo_azul = None
        equipo_rojo = None
        equipo_ganador = None
        orden = group.iloc[0].get('game')
        duracion = group.iloc[0].get('gamelength')

        for _, row in group.iterrows():
            side = row.get('side')
            team_id = row.get('teamid')
            team_name = row.get('teamname')

            # Verificamos si el team_id está vacío, es nulo o NaN
            if pd.isna(team_id) or team_id in [None, '', 'nan']:
                team_id = f"Unknown_{team_name}"

            result = row.get('result')

            if side == 'Blue':
                equipo_azul = team_id
                if result == 1:
                    equipo_ganador = team_id
            elif side == 'Red':
                equipo_rojo = team_id
                if result == 1:
                    equipo_ganador = team_id

        # Validar que los campos mínimos existen
        if None in (equipo_azul, equipo_rojo, equipo_ganador):
            print(f"⚠️ Datos incompletos para partido {gameid}, se omite.")
            continue

        partidos[gameid] = {
            'serie_id': serie_id,
            'hora': hora,
            'orden': int(orden),
            'duracion': int(duracion),
            'equipo_azul': equipo_azul,
            'equipo_rojo': equipo_rojo,
            'equipo_ganador': equipo_ganador
        }

    return partidos


def extract_all_teams():
    all_teams = {}
    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)

    if not rutas_csv:
        return all_teams

    # La ruta más reciente será la última en la lista
    latest_csv_path = rutas_csv[-1]
    latest_team_ids = set()

    for csv_file_path in rutas_csv:
        try:
            df = pd.read_csv(csv_file_path)

            if 'teamname' not in df.columns or 'teamid' not in df.columns:
                print(f"⚠️  El archivo {csv_file_path} no contiene columnas 'teamname' o 'teamid'.")
                continue

            df_filtered = df[['teamid', 'teamname']].dropna().drop_duplicates()

            for _, row in df_filtered.iterrows():
                team_id = str(row['teamid']).strip()
                team_name = str(row['teamname']).strip()

                if csv_file_path == latest_csv_path:
                    latest_team_ids.add(team_id)

                if team_id not in all_teams:
                    all_teams[team_id] = {
                        'id': team_id,
                        'name': team_name,
                        'activo': False
                    }

        except Exception as e:
            print(f"❌ Error al procesar el archivo {csv_file_path}: {e}")

    for team_id in latest_team_ids:
        if team_id in all_teams:
            all_teams[team_id]['activo'] = True

    return all_teams

def extract_all_players():
    all_players = {} 
    last_appearance = {} 

    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)

    max_year = 0

    for csv_file_path in rutas_csv:
        try:
            df = pd.read_csv(csv_file_path)
            df_players = df[df['playerid'].notna() & df['teamid'].notna()]

            for _, row in df_players.iterrows():
                player_id = row['playerid']
                player_name = row['playername']
                team_id = row['teamid']
                year = int(row['year'])

                if not player_id:
                    continue

                if player_id not in last_appearance or year > last_appearance[player_id]:
                    last_appearance[player_id] = year

                all_players[player_id] = {
                    'id': player_id,
                    'nombre': player_name,
                    'equipo_id': team_id
                }
                max_year = max(max_year, year)

        except Exception as e:
            print(f"⚠️ Error al procesar el archivo {csv_file_path}: {e}")

    for player_id in all_players:
        all_players[player_id]['activo'] = last_appearance[player_id] == max_year

    return all_players

def extract_all_jugadores_en_partida():
    all_jugadores_en_partida = []
    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)

    if not rutas_csv:
        return all_jugadores_en_partida

    for csv_file_path in rutas_csv:
        try:
            df = pd.read_csv(csv_file_path)

            # Asegurarse que las columnas necesarias existen
            required_columns = ['gameid', 'playerid', 'champion', 'kills', 'deaths', 'assists']
            if not all(col in df.columns for col in required_columns):
                print(f"⚠️ El archivo {csv_file_path} no tiene las columnas necesarias.")
                continue

            grouped = df.groupby('gameid')

            for gameid, group in grouped:
                if len(group) < 10:
                    continue  # No tiene suficientes jugadores

                jugadores = group.iloc[:10]
                posiciones = ["top", "jng", "mid", "bot", "sup"]

                for i, (_, row) in enumerate(jugadores.iterrows()):
                    jugador_data = {
                        'jugador': row["playerid"],
                        'partido': row.get("gameid"),
                        'campeon': row.get("champion"),
                        'position': str(row.get("position")).strip() if row.get("position") in posiciones else posiciones[i % len(posiciones)],
                        'kills': row.get('kills'),
                        'deaths': row.get('deaths'),
                        'assists': row.get('assists'),
                        'doublekills': row.get('doublekills'),
                        'triplekills': row.get('triplekills'),
                        'quadrakills': row.get('quadrakills'),
                        'pentakills': row.get('pentakills'),
                        'firstbloodkill': bool(row.get('firstbloodkill')),
                        'firstbloodassist': bool(row.get('firstbloodassist')),
                        'firstbloodvictim': bool(row.get('firstbloodvictim')),
                        'damagetochampions': float(row.get('damagetochampions', 0)) if pd.notna(row.get('damagetochampions')) else None,
                        'damagetaken': float(row.get('damagetaken', 0)) * float(row.get('gamelength', 0)) if pd.notna(row.get('damagetaken')) and pd.notna(row.get('gamelength')) else None,
                        'wardsplaced': row.get('wardsplaced'),
                        'wardskilled': row.get('wardskilled'),
                        'controlwardsbought': row.get('controlwardsbought'),
                        'visionscore': row.get('visionscore'),
                        'totalgold': row.get('totalgold'),
                        'total_cs': row.get('total_cs'),
                        'minionkills': row.get('minionkills'),
                        'monsterkills': row.get('monsterkills'),
                        "goldat10": row.get("goldat10"),
                        "xpat10": row.get("xpat10"),
                        "csat10": row.get("csat10"),
                        "killsat10": row.get("killsat10"),
                        "assistsat10": row.get("assistsat10"),
                        "deathsat10": row.get("deathsat10"),

                        "goldat15": row.get("goldat15"),
                        "xpat15": row.get("xpat15"),
                        "csat15": row.get("csat15"),
                        "killsat15": row.get("killsat15"),
                        "assistsat15": row.get("assistsat15"),
                        "deathsat15": row.get("deathsat15"),

                        "goldat20": row.get("goldat20"),
                        "xpat20": row.get("xpat20"),
                        "csat20": row.get("csat20"),
                        "killsat20": row.get("killsat20"),
                        "assistsat20": row.get("assistsat20"),
                        "deathsat20": row.get("deathsat20"),

                        "goldat25": row.get("goldat25"),
                        "xpat25": row.get("xpat25"),
                        "csat25": row.get("csat25"),
                        "killsat25": row.get("killsat25"),
                        "assistsat25": row.get("assistsat25"),
                        "deathsat25": row.get("deathsat25"),
                    }

                    all_jugadores_en_partida.append(jugador_data)

        except Exception as e:
            print(f"❌ Error al procesar el archivo {csv_file_path}: {e}")

    return all_jugadores_en_partida


def extraer_all_baneos_picks():
    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)
    resultados = []

    for csv_file_path in rutas_csv:
        try:
            df = pd.read_csv(csv_file_path)
            df_teams = df[df['position'] == 'team']

            for _, row in df_teams.iterrows():
                game_id = row['gameid']
                team_id = row['teamid']
                team_name = row['teamname']

                # Extraer picks del equipo
                picks = []
                for i in range(1, 6):
                    champ_s = row.get(f'pick{i}')
                    if pd.notna(champ_s) and champ_s.strip():
                        picks.append((i, champ_s.strip()))

                if len(picks) < 5:
                    # Intentar recuperar picks desde la sección de jugadores
                    df_jugadores = df[
                        (df['position'].isin(['top', 'jng', 'mid', 'bot', 'sup'])) &
                        (df['teamid'] == team_id)
                    ]
                    picks = []
                    for i, (_, jugador_row) in enumerate(df_jugadores.iterrows(), start=1):
                        champ_jugador = jugador_row.get('champion')
                        if pd.notna(champ_jugador) and champ_jugador.strip():
                            picks.append((i, champ_jugador.strip()))
                        if len(picks) == 5:
                            break

                # Añadir 5 registros: pick + ban (si existe) en la misma fila
                for i in range(1, 6):
                    champ_s = next((c for j, c in picks if j == i), None)
                    champ_b = row.get(f'ban{i}')
                    if pd.notna(champ_b) and champ_b.strip():
                        champ_b = champ_b.strip()
                    else:
                        champ_b = None

                    if champ_s:  # solo incluir si hay pick
                        resultados.append({
                            'equipo': team_id,
                            'partido': game_id,
                            'campeon_baneado': champ_b,
                            'ban': i if champ_b else None,
                            'campeon_seleccionado': champ_s,
                            'seleccion': i,
                            'equipo_nombre': team_name,
                        })

        except Exception as e:
            print(f"❌ Error procesando {csv_file_path}: {e}")

    return resultados


def extract_objetivos_neutrales_matados():
    try:
        with open(os.path.join(DICCIONARIO_CLAVES, 'objetivosneutrales.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error cargando JSON: {e}")
        return []

    # Extraemos solo los nombres de objetivos neutrales
    nombres_objetivos = [obj['nombre'] for obj in data]
    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)
    agrupados = {}

    for ruta_csv in rutas_csv:
        try:
            df = pd.read_csv(ruta_csv)
            df_filtrado = df[df['position'] == 'team']
            if not all(x in df_filtrado.columns for x in ['gameid', 'teamid']):
                print(f"Faltan columnas 'gameid' o 'teamid' en {ruta_csv}")
                continue

            columnas_objetivos = [col for col in nombres_objetivos if col in df_filtrado.columns]

            for _, fila in df_filtrado.iterrows():
                gameid = str(fila['gameid'])
                teamid = str(fila['teamid'])
                teamname = str(fila['teamname'])
                key = (gameid, teamid)

                if key not in agrupados:
                    agrupados[key] = {obj: 0 for obj in nombres_objetivos}

                for objetivo in columnas_objetivos:
                    cantidad = fila[objetivo]
                    if pd.isna(cantidad):
                        cantidad = 0
                    agrupados[key][objetivo] = int(cantidad)

        except Exception as e:
            print(f"Error procesando {ruta_csv}: {e}")

    resultados = []
    for (gameid, teamid), objetivos in agrupados.items():
        registro = {
            "gameid": gameid,
            "teamid": teamid,
            "teamname": teamname
        }
        registro.update({k: str(v) for k, v in objetivos.items()})
        resultados.append(registro)

    return resultados
        


   
if __name__ == "__main__":
    data = extraer_all_baneos_picks()
    for item in data:
        print(item)