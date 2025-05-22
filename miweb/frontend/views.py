from django.shortcuts import render
from django.conf import settings
import os
import sys
from pathlib import Path
from django.utils import timezone
BASE_DIR = Path(__file__).resolve().parent.parent
from database.models import *
from django.db.models import Prefetch
from collections import defaultdict


def index(request):
    ultimas_series = Serie.objects.order_by('-dia').prefetch_related(
        Prefetch('partidos', queryset=Partido.objects.distinct())
    )[:20]

    # Prepara un diccionario con resultados por serie para acceso rápido en template
    resultados_por_serie = {}
    for serie in ultimas_series:
        resultados_por_serie[serie.id] = serie.resultados_por_equipos()

    # Calcular clasificación para el último split del año actual
    year_actual = timezone.now().year
    split = SplitLEC.objects.filter(year=year_actual).order_by('-split_type').first()

    clasificacion = []
    if split:
        series_split = Serie.objects.filter(split=split).prefetch_related('partidos')

        # Inicializar conteo
        resultados = defaultdict(lambda: {'victorias': 0, 'derrotas': 0, 'equipo': None})

        for serie in series_split:
            resultado = serie.resultados_por_equipos()
            azul = resultado['azul']
            rojo = resultado['rojo']

            if azul['equipo'] and rojo['equipo']:
                resultados[azul['equipo'].id]['equipo'] = azul['equipo']
                resultados[rojo['equipo'].id]['equipo'] = rojo['equipo']

                if azul['victorias'] > rojo['victorias']:
                    resultados[azul['equipo'].id]['victorias'] += 1
                    resultados[rojo['equipo'].id]['derrotas'] += 1
                elif rojo['victorias'] > azul['victorias']:
                    resultados[rojo['equipo'].id]['victorias'] += 1
                    resultados[azul['equipo'].id]['derrotas'] += 1

        # Convertir a lista y ordenar
        clasificacion = sorted(resultados.values(), key=lambda x: (-x['victorias'], x['derrotas']))

    context = {
        'ultimas_series': ultimas_series,
        'resultados_por_serie': resultados_por_serie,
        'clasificacion': clasificacion,
        'ultimo_split': split,
        'today': timezone.localdate(),
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