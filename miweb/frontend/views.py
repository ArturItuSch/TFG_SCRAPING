from django.shortcuts import render, get_object_or_404
from django.conf import settings
from pathlib import Path
from django.utils import timezone



BASE_DIR = Path(__file__).resolve().parent.parent
from database.models import *
from django.db.models import Prefetch, Sum, F, ExpressionWrapper, FloatField, Case, When, Value, Count, Q
from collections import defaultdict
from datetime import datetime



def safe_division(numerator, denominator):
    return Case(
        When(**{f'{denominator.name}__gt': 0}, then=ExpressionWrapper(numerator / denominator, output_field=FloatField())),
        default=Value(0),
        output_field=FloatField()
    )

def index(request):
    ultimas_series = Serie.objects.order_by('-dia').prefetch_related(
        Prefetch('partidos', queryset=Partido.objects.select_related('equipo_azul', 'equipo_rojo', 'equipo_ganador'))
    )[:20]

    resultados_por_serie = {}
    for serie in ultimas_series:
        resultados_por_serie[serie.id] = serie.resultados_por_equipos()

    year_actual = timezone.now().year
    split = SplitLEC.obtener_ultimo_split(year_actual)  
    if split:
        series_split = Serie.objects.filter(split=split).prefetch_related('partidos')
        resultados = defaultdict(lambda: {'series_ganadas': 0, 'series_perdidas': 0, 'equipo': None})

        for serie in series_split:
            resultado = serie.resultados_por_equipos()
            azul = resultado['azul']
            rojo = resultado['rojo']

            if azul['equipo'] and rojo['equipo']:
                resultados[azul['equipo'].id]['equipo'] = azul['equipo']
                resultados[rojo['equipo'].id]['equipo'] = rojo['equipo']

                if azul['victorias'] > rojo['victorias']:
                    resultados[azul['equipo'].id]['series_ganadas'] += 1
                    resultados[rojo['equipo'].id]['series_perdidas'] += 1
                elif rojo['victorias'] > azul['victorias']:
                    resultados[rojo['equipo'].id]['series_ganadas'] += 1
                    resultados[azul['equipo'].id]['series_perdidas'] += 1

        clasificacion = sorted(resultados.values(), key=lambda x: (-x['series_ganadas'], x['series_perdidas']))
        partidos_split = Partido.objects.filter(serie__split=split)

        top_jugadores = (
            JugadorEnPartida.objects
            .filter(partido__in=partidos_split)
            .values('jugador__id', 'jugador__nombre', 'jugador__equipo__nombre', 'position')
            .annotate(
                total_kills=Sum('kills'),
                total_deaths=Sum('deaths'),
                total_assists=Sum('assists'),
            )
            .annotate(
                kda=safe_division(F('total_kills') + F('total_assists'), F('total_deaths'))
            )
            .order_by('-kda')[:10]
        )

    else:
        print("No se encontró split para el año actual")
        clasificacion = []
        top_jugadores = []
        partidos_split = Partido.objects.none()

    total_partidos_split = partidos_split.count()

    # Picks por campeón
    picks_por_campeon = (
        Seleccion.objects
        .filter(partido__in=partidos_split)
        .values('campeon_seleccionado__id', 'campeon_seleccionado__nombre', 'campeon_seleccionado__imagen')
        .annotate(num_picks=Count('id'))
        .order_by('-num_picks')[:10]
    )

    # Bans por campeón
    bans_por_campeon = (
        Seleccion.objects
        .filter(partido__in=partidos_split)
        .values('campeon_baneado__id')
        .annotate(num_bans=Count('id'))
    )

    # Diccionario para bans rápido
    bans_dict = {b['campeon_baneado__id']: b['num_bans'] for b in bans_por_campeon if b['campeon_baneado__id']}

    # Construcción de lista combinada
    campeones_stats = []
    for item in picks_por_campeon:
        campeon_id = item['campeon_seleccionado__id']
        num_picks = item['num_picks']
        num_bans = bans_dict.get(campeon_id, 0)
        pick_rate = (num_picks / total_partidos_split) * 100 if total_partidos_split else 0
        ban_rate = (num_bans / total_partidos_split) * 100 if total_partidos_split else 0

        campeones_stats.append({
            'id': campeon_id,
            'nombre': item['campeon_seleccionado__nombre'],
            'imagen': item['campeon_seleccionado__imagen'],
            'num_picks': num_picks,
            'pick_rate': pick_rate,
            'num_bans': num_bans,
            'ban_rate': ban_rate,
        })

    context = {
        'ultimas_series': ultimas_series,
        'resultados_por_serie': resultados_por_serie,
        'clasificacion': clasificacion,
        'ultimo_split': split,
        'top_jugadores': top_jugadores,
        'today': timezone.localdate(),
        'campeones_stats': campeones_stats,
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'index.html', context)

def splits(request):
    # Obtener los parámetros GET para filtrar
    split_type = request.GET.get('split_type', '').strip().lower()
    league = request.GET.get('league', '').strip()
    year = request.GET.get('year', '').strip()

    # Empezar con todos los splits ordenados
    all_splits = SplitLEC.objects.order_by('-year', 'split_type')

    # Aplicar filtros si vienen en GET
    if split_type:
        all_splits = all_splits.filter(split_type__icontains=split_type)
    if league:
        all_splits = all_splits.filter(league=league)
    if year.isdigit():
        all_splits = all_splits.filter(year=int(year))

    # Agrupar por año
    splits_por_year = defaultdict(list)
    for split in all_splits:
        splits_por_year[split.year].append(split)

    year_ordenados = sorted(splits_por_year.keys(), reverse=True)

    # Obtener ligas distintas para el filtro
    ligas_disponibles = SplitLEC.objects.values_list('league', flat=True).distinct()

    context = {
        'splits_por_year': splits_por_year,
        'year_ordenados': year_ordenados,
        'ligas_disponibles': ligas_disponibles,
        'request': request,  # Para acceder a request.GET en template
    }

    return render(request, 'splits.html', context)

def split_detail(request, split_id):
    split = get_object_or_404(SplitLEC, split_id=split_id)

    # --- SERIES ---
    series_regular = Serie.objects.filter(split=split, playoffs=False).prefetch_related('partidos')
    series_playoffs = Serie.objects.filter(split=split, playoffs=True).prefetch_related('partidos')

    # --- JUGADORES DEL SPLIT (único cálculo) ---
    jugadores_por_equipo = defaultdict(dict)
    jugadores_en_split = JugadorEnPartida.objects.filter(partido__serie__split=split).select_related('jugador', 'partido', 'campeon')

    for jp in jugadores_en_split:
        if jp.side == "Blue":
            equipo = jp.partido.equipo_azul
        elif jp.side == "Red":
            equipo = jp.partido.equipo_rojo
        else:
            continue

        if equipo and jp.jugador:
            jugadores_por_equipo[equipo.id][jp.jugador.id] = {
                'nombre': jp.jugador.nombre,
                'rol': jp.jugador.rol,
                'pais': jp.jugador.pais,
                'imagen': jp.jugador.imagen,
                'equipo_nombre': equipo.nombre,
            }

    # --- PROCESAMIENTO DE ESTADÍSTICAS ---
    def procesar_estadisticas(series):
        clasificacion = defaultdict(lambda: {'equipo': None, 'victorias': 0, 'derrotas': 0})
        jugadores_en_partidas = JugadorEnPartida.objects.filter(partido__in=[p for s in series for p in s.partidos.all()]).select_related('jugador', 'partido', 'campeon')

        for serie in series:
            resultado = serie.resultados_por_equipos()
            azul = resultado['azul']
            rojo = resultado['rojo']
            for side in [azul, rojo]:
                equipo = side['equipo']
                if equipo:
                    clasificacion[equipo.id]['equipo'] = equipo

            ganador = azul['equipo'] if azul['victorias'] > rojo['victorias'] else rojo['equipo']
            perdedor = rojo['equipo'] if ganador == azul['equipo'] else azul['equipo']
            if ganador:
                clasificacion[ganador.id]['victorias'] += 1
            if perdedor:
                clasificacion[perdedor.id]['derrotas'] += 1

        # Campeones
        campeon_stats = defaultdict(lambda: {
            'nombre': '',
            'imagen': '',
            'veces_jugado': 0,
            'victorias': 0,
            'derrotas': 0,
            'pickrate': 0,
            'banrate': 0,
            'winrate': 0,
            'loserate': 0,
        })

        total_partidos = jugadores_en_partidas.values('partido_id').distinct().count()

        for jp in jugadores_en_partidas:
            c = jp.campeon
            if not c:
                continue
            stat = campeon_stats[c.id]
            stat['nombre'] = c.nombre
            stat['imagen'] = c.imagen
            stat['veces_jugado'] += 1

            if (jp.side == 'Blue' and jp.partido.equipo_azul == jp.partido.equipo_ganador) or \
               (jp.side == 'Red' and jp.partido.equipo_rojo == jp.partido.equipo_ganador):
                stat['victorias'] += 1
            else:
                stat['derrotas'] += 1

        picks = Seleccion.objects.filter(partido__in=[p for s in series for p in s.partidos.all()], campeon_seleccionado__isnull=False).values('campeon_seleccionado').annotate(picks=Count('id'))
        bans = Seleccion.objects.filter(partido__in=[p for s in series for p in s.partidos.all()], campeon_baneado__isnull=False).values('campeon_baneado').annotate(bans=Count('id'))

        for p in picks:
            cid = p['campeon_seleccionado']
            if cid in campeon_stats:
                campeon_stats[cid]['pickrate'] = (p['picks'] / (total_partidos * 2)) * 100

        for b in bans:
            cid = b['campeon_baneado']
            if cid in campeon_stats:
                campeon_stats[cid]['banrate'] = (b['bans'] / (total_partidos * 2)) * 100

        for stat in campeon_stats.values():
            total = stat['veces_jugado']
            stat['winrate'] = (stat['victorias'] / total * 100) if total else 0
            stat['loserate'] = (stat['derrotas'] / total * 100) if total else 0

        clasificacion_ordenada = sorted(
            clasificacion.values(),
            key=lambda x: x['victorias'],
            reverse=True
        )

        return clasificacion_ordenada, list(campeon_stats.values())

    # Procesar ambas fases
    clasificacion_regular, campeones_regular = procesar_estadisticas(series_regular)
    clasificacion_playoffs, campeones_playoffs = procesar_estadisticas(series_playoffs)

    # Filtros para campeones de fase regular
    search = request.GET.get('search', '').strip().lower()
    sort = request.GET.get('sort', '')
    if search:
        campeones_regular = [c for c in campeones_regular if search in c['nombre'].lower()]
    if sort in {'veces_jugado', 'pickrate', 'banrate', 'winrate'}:
        campeones_regular.sort(key=lambda c: c.get(sort, 0), reverse=True)

    context = {
        'split': split,
        'clasificacion': [
            {
                'nombre': d['equipo'].nombre,
                'logo': d['equipo'].logo,
                'victorias': d['victorias'],
                'derrotas': d['derrotas'],
                'jugadores': list(jugadores_por_equipo.get(d['equipo'].id, {}).values())
            }
            for d in clasificacion_regular if d['equipo'] is not None
        ],
        'campeones': campeones_regular,
        'playoffs_clasificacion': [
            {
                'nombre': d['equipo'].nombre,
                'logo': d['equipo'].logo,
                'victorias': d['victorias'],
                'derrotas': d['derrotas'],
                'jugadores': list(jugadores_por_equipo.get(d['equipo'].id, {}).values())
            }
            for d in clasificacion_playoffs if d['equipo'] is not None
        ],
        'playoffs_campeones': campeones_playoffs,
        'series_playoffs': list(series_playoffs),  
    }

    rondas_dict = defaultdict(list)
    for serie in series_playoffs:
        clave = serie.dia.strftime("Ronda %d/%m")
        rondas_dict[clave].append(serie)

    context['playoffs_rondas'] = sorted(rondas_dict.items(), key=lambda x: x[0])
    
    ganador_playoffs = None
    if series_playoffs.exists():
        ultima_serie = series_playoffs.order_by('-dia').first()
        resultado_final = ultima_serie.resultados_por_equipos()
        if resultado_final['azul']['victorias'] > resultado_final['rojo']['victorias']:
            ganador_playoffs = resultado_final['azul']['equipo']
        else:
            ganador_playoffs = resultado_final['rojo']['equipo']

    context['ganador_playoffs'] = ganador_playoffs
    
    return render(request, 'split_detail.html', context)



def equipos(request):
    equipos_activos = Equipo.objects.filter(activo=True)
    todos_equipos = Equipo.objects.filter(activo=False)
    return render(request, 'equipos.html', {
        'equipos_activos': equipos_activos,
        'todos_equipos': todos_equipos,
    })

def obtener_orden_rol(jugador):
    orden_roles = ['top', 'jung', 'mid', 'bot', 'supp']
    if jugador.rol:
        rol = jugador.rol.lower()
        if rol in orden_roles:
            return orden_roles.index(rol)
    return 99  

def detalle_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    jugadores = Jugador.objects.filter(
        equipo=equipo,
        activo=True
    ).exclude(rol__isnull=True).exclude(rol__exact='')

    roles_deseados = ['Top Laner', 'Jungler', 'Mid Laner', 'Bot Laner', 'Support']
    jugadores_por_rol = {rol: jugadores.filter(rol__iexact=rol) for rol in roles_deseados}

    return render(request, 'detalle_equipo.html', {
        'equipo': equipo,
        'jugadores_por_rol': jugadores_por_rol,
        'roles_deseados': roles_deseados,
    })
    
def jugadores(request):
    jugadores = Jugador.objects.filter(activo=True)

    nombre = request.GET.get('nombre')
    equipo_id = request.GET.get('equipo')
    rol = request.GET.get('rol')

    if nombre:
        jugadores = jugadores.filter(nombre__icontains=nombre)
    if equipo_id:
        jugadores = jugadores.filter(equipo__id=equipo_id)
    if rol:
        jugadores = jugadores.filter(rol=rol)

    equipos_disponibles = Equipo.objects.filter(activo=True).order_by('nombre')
    roles_disponibles = Jugador.objects.values_list('rol', flat=True).distinct().order_by('rol')

    return render(request, 'jugadores.html', {
        'jugadores': jugadores,
        'equipos_disponibles': equipos_disponibles,
        'roles_disponibles': roles_disponibles,
    })

def detalle_jugador(request, jugador_id):
    jugador = get_object_or_404(Jugador, id=jugador_id)
    year_actual = datetime.now().year
    split_actual = SplitLEC.obtener_ultimo_split(year_actual)

    # Parámetros de filtrado y orden
    campeon_filtro = request.GET.get('campeon', '').strip().lower()
    resultado_filtro = request.GET.get('resultado')
    orden = request.GET.get('orden')

    partidas_detalle = []
    if split_actual:
        partidas = (
            JugadorEnPartida.objects
            .filter(jugador=jugador, partido__serie__split=split_actual)
            .select_related('partido', 'partido__equipo_azul', 'partido__equipo_rojo', 'partido__equipo_ganador', 'campeon')
            .order_by('partido__serie__dia', 'partido__orden')
        )

        for p in partidas:
            enemigo = p.partido.equipo_rojo if p.partido.equipo_azul == jugador.equipo else p.partido.equipo_azul
            gano = p.partido.equipo_ganador == jugador.equipo
            cs_total = (p.minionkills or 0) + (p.monsterkills or 0)

            partida_dict = {
                'enemigo': enemigo.nombre if enemigo else 'Desconocido',
                'campeon': p.campeon.nombre,
                'campeon_imagen': p.campeon.imagen,
                'victoria': gano,
                'kills': p.kills or 0,
                'deaths': p.deaths or 0,
                'assists': p.assists or 0,
                'cs': cs_total,
                'gold': p.totalgold or 0,
                'damage': p.damagetochampions or 0,
                'vision': p.visionscore or 0,
            }

            partidas_detalle.append(partida_dict)

    # Estadísticas generales
    estadisticas_generales = None
    if partidas_detalle:
        total_partidas = len(partidas_detalle)
        total_wins = sum(1 for p in partidas_detalle if p['victoria'])

        estadisticas_generales = {
            'prom_kills': round(sum(p['kills'] for p in partidas_detalle) / total_partidas, 1),
            'prom_deaths': round(sum(p['deaths'] for p in partidas_detalle) / total_partidas, 1),
            'prom_assists': round(sum(p['assists'] for p in partidas_detalle) / total_partidas, 1),
            'prom_cs': round(sum(p['cs'] for p in partidas_detalle) / total_partidas, 1),
            'prom_vision': round(sum(p['vision'] for p in partidas_detalle) / total_partidas, 1),
            'winrate': round(100 * total_wins / total_partidas, 1),
        }
            
    # Filtros
    if campeon_filtro:
        partidas_detalle = [p for p in partidas_detalle if campeon_filtro in p['campeon'].lower()]
    if resultado_filtro == 'win':
        partidas_detalle = [p for p in partidas_detalle if p['victoria']]
    elif resultado_filtro == 'lose':
        partidas_detalle = [p for p in partidas_detalle if not p['victoria']]

    # Ordenamiento
    if orden in ['kills', 'deaths', 'assists', 'gold', 'damage', 'vision', 'cs']:
        partidas_detalle.sort(key=lambda x: x.get(orden, 0), reverse=True)

    return render(request, 'detalle_jugador.html', {
        'jugador': jugador,
        'split_actual': split_actual,
        'partidas_detalle': partidas_detalle,
        'orden': orden,
        'campeon_filtro': campeon_filtro,
        'resultado_filtro': resultado_filtro,
        'estadisticas_generales': estadisticas_generales if partidas_detalle else None,
    })


    

def partidos(request):
    partidos = Partido.objects.order_by('-serie__dia', '-hora')[:50]
    return render(request, 'partidos.html', {'partidos': partidos})


def campeones(request):
    from django.conf import settings

    query = request.GET.get('q', '').strip()
    year = request.GET.get('year', '').strip()
    split_type = request.GET.get('split_type', '').strip()

    splits = SplitLEC.objects.all()
    if year.isdigit():
        splits = splits.filter(year=int(year))
    if split_type:
        splits = splits.filter(split_type__iexact=split_type)

    partidos_filtrados = Partido.objects.all()
    if splits.exists():
        partidos_filtrados = partidos_filtrados.filter(serie__split__in=splits)

    total_partidos = partidos_filtrados.count()

    picks = (
        Seleccion.objects
        .filter(partido__in=partidos_filtrados, campeon_seleccionado__isnull=False)
        .values('campeon_seleccionado__id', 'campeon_seleccionado__nombre', 'campeon_seleccionado__imagen')
        .annotate(
            num_picks=Count('id'),
            num_wins=Count('id', filter=Q(equipo=F('partido__equipo_ganador')))
        )
    )

    bans = (
        Seleccion.objects
        .filter(partido__in=partidos_filtrados, campeon_baneado__isnull=False)
        .values('campeon_baneado__id')
        .annotate(num_bans=Count('id'))
    )
    bans_dict = {b['campeon_baneado__id']: b['num_bans'] for b in bans if b['campeon_baneado__id']}

    # Crear estadísticas por campeón
    campeones_stats = []
    for pick in picks:
        cid = pick['campeon_seleccionado__id']
        nombre = pick['campeon_seleccionado__nombre']
        imagen = pick['campeon_seleccionado__imagen']
        num_picks = pick['num_picks']
        num_wins = pick['num_wins']

        if not nombre or nombre.lower() == 'none' or not imagen or imagen.lower() == 'none':
            continue
        if query and query.lower() not in nombre.lower():
            continue

        campeones_stats.append({
            'id': cid,
            'nombre': nombre,
            'imagen': imagen,
            'num_picks': num_picks,
            'num_bans': bans_dict.get(cid, 0),
            'pick_rate': round((num_picks / total_partidos) * 100, 2) if total_partidos else 0,
            'ban_rate': round((bans_dict.get(cid, 0) / total_partidos) * 100, 2) if total_partidos else 0,
            'win_rate': round((num_wins / num_picks) * 100, 2) if num_picks else 0,
        })

    campeones_stats = sorted(campeones_stats, key=lambda c: c['pick_rate'], reverse=True)

    orden = request.GET.get('orden', '')

    if orden == 'nombre_asc':
        campeones_stats = sorted(campeones_stats, key=lambda c: c['nombre'].lower())
    elif orden == 'nombre_desc':
        campeones_stats = sorted(campeones_stats, key=lambda c: c['nombre'].lower(), reverse=True)
    elif orden == 'pickrate':
        campeones_stats = sorted(campeones_stats, key=lambda c: c['pick_rate'], reverse=True)
    elif orden == 'banrate':
        campeones_stats = sorted(campeones_stats, key=lambda c: c['ban_rate'], reverse=True)
    elif orden == 'winrate':
        campeones_stats = sorted(campeones_stats, key=lambda c: c['win_rate'], reverse=True)
    else:
        campeones_stats = sorted(campeones_stats, key=lambda c: c['pick_rate'], reverse=True)
        
    years_disponibles = SplitLEC.objects.order_by('-year').values_list('year', flat=True).distinct()
    splits_disponibles = ['Winter', 'Spring', 'Summer']

    return render(request, 'campeones.html', {
        'campeones': campeones_stats,
        'MEDIA_URL': settings.MEDIA_URL,
        'query': query,
        'year': year,
        'split_type': split_type,
        'years_disponibles': years_disponibles,
        'orden': orden,
        'splits_disponibles': splits_disponibles,
    })
    
    
def series_jugadas(request):
    split_id = request.GET.get('split_id')

    # Cargar splits disponibles
    splits = SplitLEC.objects.all().order_by('-year', 'split_type')

    # Si no se selecciona un split, usar el último disponible
    if not split_id and splits.exists():
        split_id = splits.first().split_id

    # Filtrar series por split
    series = Serie.objects.select_related('split').prefetch_related(
        'partidos__equipo_azul', 'partidos__equipo_rojo'
    ).filter(split__split_id=split_id).order_by('-dia')

    series_data = []
    for s in series:
        partidos = s.partidos.all().order_by('orden', 'id')
        if not partidos.exists():
            continue

        primer_partido = partidos.first()
        equipo_azul = primer_partido.equipo_azul
        equipo_rojo = primer_partido.equipo_rojo

        jugadores_primer_partido = JugadorEnPartida.objects.filter(partido=primer_partido).select_related('jugador', 'campeon')

        jugadores_equipo_azul = [jp for jp in jugadores_primer_partido if jp.side == 'Blue']
        jugadores_equipo_rojo = [jp for jp in jugadores_primer_partido if jp.side == 'Red']

        resultados = s.resultados_por_equipos()

        series_data.append({
            'id': s.id,
            'dia': s.dia,
            'playoffs': s.playoffs,
            'equipo_azul': equipo_azul,
            'equipo_rojo': equipo_rojo,
            'jugadores_azul': jugadores_equipo_azul,
            'jugadores_rojo': jugadores_equipo_rojo,
            'resultados': resultados,
        })

    return render(request, 'series_list.html', {
        'splits': splits,
        'split_id': split_id,
        'series': series_data,
    })

def detalle_serie(request, id):
    serie = get_object_or_404(
        Serie.objects.prefetch_related('partidos__equipo_azul', 'partidos__equipo_rojo'),
        id=id
    )
    partidos = serie.partidos.all().order_by('orden', 'id')
    primer_partido = partidos.first() if partidos.exists() else None
    resultados = serie.resultados_por_equipos()

    partidas_data = []
    for partido in partidos:
        jugadores = JugadorEnPartida.objects.filter(partido=partido).select_related('jugador', 'campeon')
        jugadores_azul = [jp for jp in jugadores if jp.side == 'Blue']
        jugadores_rojo = [jp for jp in jugadores if jp.side == 'Red']
        partidas_data.append({
            'partido': partido,
            'jugadores_azul': jugadores_azul,
            'jugadores_rojo': jugadores_rojo,
        })

    return render(request, 'serie_info.html', {
        'serie': serie,
        'partidos': partidos,
        'primer_partido': primer_partido,
        'resultados': resultados,
        'partidas_data': partidas_data,
    })
    
def partido_info(request, id):
    partido = get_object_or_404(Partido, id=id)

    jugadores = JugadorEnPartida.objects.filter(partido=partido).select_related('jugador', 'campeon')
    objetivos = ObjetivosNeutrales.objects.filter(partida=partido)
    selecciones = Seleccion.objects.filter(partido=partido).select_related('campeon_seleccionado', 'campeon_baneado', 'equipo')

    equipo_azul = partido.equipo_azul
    equipo_rojo = partido.equipo_rojo
    equipo_ganador = partido.equipo_ganador

    objetivos_azul = objetivos.filter(equipo=equipo_azul).first()
    objetivos_rojo = objetivos.filter(equipo=equipo_rojo).first()

    picks_azul = selecciones.filter(equipo=equipo_azul, seleccion__isnull=False).order_by('seleccion')
    bans_azul = selecciones.filter(equipo=equipo_azul, baneo__isnull=False).order_by('baneo')
    picks_rojo = selecciones.filter(equipo=equipo_rojo, seleccion__isnull=False).order_by('seleccion')
    bans_rojo = selecciones.filter(equipo=equipo_rojo, baneo__isnull=False).order_by('baneo')

    # Separar jugadores por side
    jugadores_blue = [j for j in jugadores if j.side and j.side.lower() == 'blue']
    jugadores_red = [j for j in jugadores if j.side and j.side.lower() == 'red']

    # Duración formateada
    minutos = partido.duracion // 60 if partido.duracion else 0
    segundos = partido.duracion % 60 if partido.duracion else 0
    duracion_format = f"{minutos}:{segundos:02d}"

    context = {
        'partido': partido,
        'equipo_ganador': equipo_ganador if equipo_ganador else None,
        'duracion': duracion_format,
        'equipos_data': [
            {
                'equipo': equipo_azul,
                'objetivos': objetivos_azul,
                'picks': picks_azul,
                'bans': bans_azul,
                'side_color': 'primary',
                'side': 'blue',
                'win': equipo_azul == equipo_ganador,
            },
            {
                'equipo': equipo_rojo,
                'objetivos': objetivos_rojo,
                'picks': picks_rojo,
                'bans': bans_rojo,
                'side_color': 'danger',
                'side': 'red',
                'win': equipo_rojo == equipo_ganador,
            }
        ],
        'jugadores_blue': jugadores_blue,
        'jugadores_red': jugadores_red,
    }

    return render(request, 'partido.html', context)