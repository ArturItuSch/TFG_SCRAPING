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
