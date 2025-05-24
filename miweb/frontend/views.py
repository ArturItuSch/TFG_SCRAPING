from django.shortcuts import render
from django.conf import settings
import os
import sys
from pathlib import Path
from django.utils import timezone
BASE_DIR = Path(__file__).resolve().parent.parent
from database.models import *
from django.db.models import Prefetch, Sum, F, ExpressionWrapper, FloatField, Case, When, Value, Count, Q
from collections import defaultdict


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
    all_splits = SplitLEC.objects.order_by('-year', '-split_type')
    return render(request, 'splits.html', {'splits': all_splits})

def equipos(request):
    equipos = Equipo.objects.filter(activo=True).order_by('nombre')
    return render(request, 'equipos.html', {'equipos': equipos})

def jugadores(request):
    jugadores = Jugador.objects.filter(activo=True).order_by('nombre')
    return render(request, 'jugadores.html', {'jugadores': jugadores})

def partidos(request):
    partidos = Partido.objects.order_by('-serie__dia', '-hora')[:50]
    return render(request, 'partidos.html', {'partidos': partidos})