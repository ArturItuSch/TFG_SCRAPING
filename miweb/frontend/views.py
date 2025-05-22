from django.shortcuts import render
import os
import sys
from pathlib import Path
from django.utils import timezone
BASE_DIR = Path(__file__).resolve().parent.parent
from database.models import *


def index(request):
    ultimas_series = Serie.objects.order_by('-dia')[:10]

    # Prepara un diccionario con resultados por serie para acceso rápido en template
    resultados_por_serie = {}
    for serie in ultimas_series:
        resultados_por_serie[str(serie.id)] = serie.resultados_por_equipos()

    context = {
        'ultimas_series': ultimas_series,
        'resultados_por_serie': resultados_por_serie,
        'today': timezone.localdate(),  
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