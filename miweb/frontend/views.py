from django.shortcuts import render
import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
from database.models import *

def index(request):
    return render(request, 'index.html')

def index(request):
    # Podrías mostrar últimos partidos, resumen
    latest_splits = SplitLEC.objects.order_by('-year', '-split_type')[:3]
    return render(request, 'index.html', {'splits': latest_splits})

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