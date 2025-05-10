import pandas as pd
import sys
import os
import json
import uuid

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, PROJECT_ROOT)

from Resources.rutas import *

CARPETA_CSV = os.path.join(CARPETA_CSV_GAMES)
CARPETA_CSV_LEC = os.path.join(CARPETA_CSV, 'LEC', '2025')
IDS_EQUIPOS_DICCIONARIO = os.path.join(DICCIONARIO_CLAVES, 'taem_ids.json')
IDS_PLAYER_DICCIONARIO = os.path.join(DICCIONARIO_CLAVES, 'player_ids.json')
JSON_EQUIPOS = os.path.join(JSON_INSTALATION_TEAMS, 'teams_data_leguepedia.json')
JSON_JUGADORES = os.path.join(JSON_INSTALATION_PLAYERS, 'players_data_leguepedia.json')
JSON_PARTIDOS = os.path.join(JSON_GAMES)


def filtrar_ligas_automaticamente(carpeta_csv, carpeta_salida_base, project_root):
    os.makedirs(carpeta_salida_base, exist_ok=True)

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

                # Filtrar por cada liga encontrada en el archivo
                for liga in df['league'].unique():
                    datos_filtrados = df[df['league'] == liga]

                    if not datos_filtrados.empty:
                        carpeta_salida = os.path.join(carpeta_salida_base, liga, anio)
                        os.makedirs(carpeta_salida, exist_ok=True)

                        nombre_archivo = f"{nombre_base}_{liga}.csv"
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
            # Cambiar 'nombre_jugador' por 'jugador' aquí
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


             
if __name__ == '__main__':
    #filtrar_ligas_automaticamente(CARPETA_CSV, CARPETA_CSV, PROJECT_ROOT)
    equipos = obtener_equipos_o_jugadores(CARPETA_CSV_LEC, 'teamid', 'teamname')
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
    agregar_ids_jugadores(JSON_JUGADORES, lista_final_jugadores)