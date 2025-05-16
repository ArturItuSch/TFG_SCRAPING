import pandas as pd
import sys
import os
import json
import uuid
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from Resources.rutas import *

CARPETA_CSV = os.path.join(CARPETA_CSV_GAMES)
CARPETA_CSV_LEC = os.path.join(CARPETA_CSV, 'LEC')
IDS_EQUIPOS_DICCIONARIO = os.path.join(DICCIONARIO_CLAVES, 'taem_ids.json')
IDS_PLAYER_DICCIONARIO = os.path.join(DICCIONARIO_CLAVES, 'player_ids.json')
JSON_EQUIPOS = os.path.join(JSON_INSTALATION_TEAMS, 'teams_data_leguepedia.json')
JSON_JUGADORES = os.path.join(JSON_INSTALATION_PLAYERS, 'players_data_leguepedia.json')
JSON_PARTIDOS = os.path.join(JSON_GAMES)
JSON_SPLITS_LEC = os.path.join(JSON_INSTALATION_SPLITS_LEC)

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
            
            
def obtener_equipos_o_jugadores(carpeta_csv, columna_id, columna_nombre):
    archivos_csv = [
        os.path.relpath(os.path.join(carpeta_csv, archivo), start=PROJECT_ROOT)
        for archivo in os.listdir(carpeta_csv)
        if archivo.endswith('.csv') and os.path.isfile(os.path.join(carpeta_csv, archivo))
    ]

    elementos = {}
    
    for archivo in archivos_csv:
        ruta_absoluta = os.path.join(PROJECT_ROOT, archivo)
        try:
            df = pd.read_csv(ruta_absoluta, dtype=str)
            if columna_id in df.columns and columna_nombre in df.columns:
                for _, row in df[[columna_id, columna_nombre]].dropna().drop_duplicates().iterrows():
                    elementos[row[columna_id]] = row[columna_nombre]
            else:
                print(f"El archivo {archivo} no contiene las columnas necesarias.")
        except Exception as e:
            print(f"Error procesando {archivo}: {e}")
    
    lista_elementos = [{'id': tid.strip().split(':')[-1], 'nombre': nombre} for tid, nombre in elementos.items()]
    return lista_elementos

def ids_nuevos(lista, archivo_salida):
    if os.path.exists(archivo_salida):
        with open(archivo_salida, "r", encoding="utf-8") as f:
            id_dict = json.load(f)
    else:
        id_dict = {}
    nuevos = 0
    for entry in lista:
        old_id = entry["id"]
        if old_id not in id_dict:
            id_dict[old_id] = uuid.uuid4().hex
            nuevos += 1
    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(id_dict, f, indent=4)

    print(f"{nuevos} nuevos IDs añadidos.")
    print(f"Archivo actualizado guardado en {archivo_salida}")
    
def nombre_newIDs(nombres, archivo_ids):
    if not os.path.exists(archivo_ids):
        print("El archivo de IDs no existe.")
        return []

    with open(archivo_ids, "r", encoding="utf-8") as f:
        id_dict = json.load(f)

    resultado = []
    for nombre in nombres:
        old_id = nombre["id"]
        name = nombre["nombre"]
        nuevo_id = id_dict.get(old_id)
        if nuevo_id:
            resultado.append({'nombre': name, 'nuevo_id': nuevo_id})
        else:
            print(f"ID antiguo no encontrado en el archivo: {old_id}")

    return resultado

def normalizar_nombre(nombre):
    """Convierte un nombre a minúsculas, reemplaza guiones bajos por espacios y quita espacios extras."""
    return nombre.lower().replace('_', ' ').strip()

def agregar_ids_equipos(archivo, nuevos_ids):
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            equipos_original = json.load(f)

        id_dict = {
            normalizar_nombre(e['nombre']): e['nuevo_id']
            for e in nuevos_ids
        }

        no_encontrados = []

        for equipo in equipos_original:
            nombre_eq = normalizar_nombre(equipo.get('nombre_equipo', ''))
            nuevo_id_calculado = id_dict.get(nombre_eq)

            if nuevo_id_calculado:
                if equipo.get('nuevo_id') != nuevo_id_calculado:
                    equipo['nuevo_id'] = nuevo_id_calculado
            else:
                no_encontrados.append(equipo.get('nombre_equipo', 'NOMBRE DESCONOCIDO'))

        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(equipos_original, f, ensure_ascii=False, indent=4)

        print(f"IDs añadidos correctamente en: {archivo}")
        if no_encontrados:
            print("⚠️ No se encontraron IDs para los siguientes equipos:")
            for nombre in no_encontrados:
                print(f" - {nombre}")

    except Exception as e:
        print(f"Error al procesar el archivo '{archivo}': {e}")

def ids_nuevos_jugadores(lista, archivo_salida):
    """Genera nuevos IDs para jugadores que no tengan uno y los guarda en el archivo de salida."""
    if os.path.exists(archivo_salida):
        with open(archivo_salida, "r", encoding="utf-8") as f:
            id_dict = json.load(f)
    else:
        id_dict = {}
    
    nuevos = 0
    for entry in lista:
        old_id = entry["id"]
        if old_id not in id_dict:
            id_dict[old_id] = uuid.uuid4().hex  # Genera un nuevo ID único
            nuevos += 1

    # Guarda los nuevos IDs en el archivo
    with open(archivo_salida, "w", encoding="utf-8") as f:
        json.dump(id_dict, f, indent=4)

    print(f"{nuevos} nuevos IDs añadidos a los jugadores.")
    print(f"Archivo actualizado guardado en {archivo_salida}") 

def agregar_ids_jugadores(archivo, nuevos_ids):
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            jugadores_original = json.load(f)

        id_dict = {
            normalizar_nombre(j['nombre']): j['nuevo_id']
            for j in nuevos_ids
        }

        no_encontrados = []

        for jugador in jugadores_original:
            nombre_jugador = normalizar_nombre(jugador.get('jugador', ''))
            nuevo_id_calculado = id_dict.get(nombre_jugador)

            if nuevo_id_calculado:
                if jugador.get('nuevo_id') != nuevo_id_calculado:
                    jugador['nuevo_id'] = nuevo_id_calculado
            else:
                no_encontrados.append(jugador.get('jugador', 'NOMBRE DESCONOCIDO'))

        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(jugadores_original, f, ensure_ascii=False, indent=4)

        print(f"IDs añadidos correctamente en: {archivo}")
        if no_encontrados:
            print("⚠️ No se encontraron IDs para los siguientes jugadores:")
            for nombre in no_encontrados:
                print(f" - {nombre}")

    except Exception as e:
        print(f"Error al procesar el archivo '{archivo}': {e}")

def obtener_rutas_csv(carpeta):
    rutas_csv = []
    for year in os.listdir(carpeta):
        year_path = os.path.join(carpeta, year)

        if os.path.isdir(year_path):
            for archivo in os.listdir(year_path):
                if archivo.endswith('.csv'):
                    archivo_path = os.path.join(year_path, archivo) 
                    rutas_csv.append(archivo_path)  

    return rutas_csv

def extract_all_splits():
    all_splits = {}

    rutas_csv = obtener_rutas_csv(CARPETA_CSV_LEC)

    for csv_file_path in rutas_csv:
        archivo_nombre = os.path.basename(csv_file_path)
        year = archivo_nombre.split('_')[0]

        try:
            df = pd.read_csv(csv_file_path)
            df['split'] = df['split'].fillna('unknown')
            splits = df['split'].drop_duplicates()

            for split in splits:
                split = str(split).strip().lower() if split else 'unknown'
                split_id = f"{year}{split}"

                # Evitamos sobreescribir si ya existe
                if split_id not in all_splits:
                    all_splits[split_id] = {
                        "id": split_id,
                        "league": "LEC",
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
                year = row['year']
                split = str(row['split']).strip().lower()
                patch = row.get('patch')

                # Condición de nueva serie: cambia el gameid Y el game es 1
                if (gameid != last_gameid and game == 1) or current_serie_id is None:
                    # Guardar serie anterior si existía
                    if current_serie_id and current_serie_partidos:
                        all_series[current_serie_id] = {
                            'split_id': f"{year}{split}",
                            'num_partidos': len(current_serie_partidos),
                            'patch': patch
                        }
                        for orden, partida_gameid in enumerate(current_serie_partidos, start=1):
                            all_partidos[partida_gameid] = {
                                'serie_id': current_serie_id,
                                'orden': orden
                            }

                    # Nueva serie
                    key = (year, split)
                    serie_counters[key] = serie_counters.get(key, 0) + 1
                    current_serie_id = f"{year}_{split}_{serie_counters[key]}"
                    current_serie_partidos = [gameid]
                else:
                    # Seguimos en la misma serie
                    if gameid not in current_serie_partidos:
                        current_serie_partidos.append(gameid)

                last_gameid = gameid

            # Guardar la última serie al final del archivo
            if current_serie_id and current_serie_partidos:
                all_series[current_serie_id] = {
                    'split_id': f"{year}{split}",
                    'num_partidos': len(current_serie_partidos),
                    'patch': patch
                }
                for orden, partida_gameid in enumerate(current_serie_partidos, start=1):
                    all_partidos[partida_gameid] = {
                        'serie_id': current_serie_id,
                        'orden': orden
                    }

        except Exception as e:
            print(f"❌ Error al procesar archivo {csv_file_path}: {e}")

    print(f"📊 Total series extraídas: {len(all_series)}")
    print(f"📊 Total partidos extraídos: {len(all_partidos)}")

    return all_series, all_partidos


def extract_partidos_de_serie(serie_id, serie_df):
    partidos = {}
    for gameid in serie_df['gameid'].unique():
        # Puedes extraer más datos si quieres
        partidos[gameid] = {
            'serie_id': serie_id,
            # 'fecha': ...,
            # 'orden': ...,
            # 'duracion': ...,
        }
    return partidos

if __name__ == '__main__':
    filtrar_ligas_automaticamente(CARPETA_CSV, CARPETA_CSV, PROJECT_ROOT)
    '''equipos = obtener_equipos_o_jugadores(CARPETA_CSV_LEC, 'teamid', 'teamname')
    ids_nuevos(equipos, IDS_EQUIPOS_DICCIONARIO)
    lista_final = nombre_newIDs(equipos, IDS_EQUIPOS_DICCIONARIO)
    for item in lista_final:
        print(item)
    agregar_ids_equipos(JSON_EQUIPOS, lista_final)
    jugadores = obtener_equipos_o_jugadores(CARPETA_CSV_LEC, 'playerid', 'playername')
    ids_nuevos_jugadores(jugadores, IDS_PLAYER_DICCIONARIO)
    
    # Mapeo de IDs antiguos a nuevos
    lista_final_jugadores = nombre_newIDs(jugadores, IDS_PLAYER_DICCIONARIO)
    for item in lista_final_jugadores:
        print(item)
    
    # Agregar los nuevos IDs a los jugadores
    agregar_ids_jugadores(JSON_JUGADORES, lista_final_jugadores)'''

   
    extract_all_series_and_partidos()      