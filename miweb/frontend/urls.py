from django.urls import path
from django.shortcuts import redirect
from . import views


urlpatterns = [
    path('', lambda request: redirect('index', permanent=False)),
    path('index/', views.index, name='index'),
    path('splits/', views.splits, name='splits'),
    path('equipos/', views.equipos, name='equipos'),
    path('jugadores/', views.jugadores, name='jugadores'),
    path('partidos/', views.partidos, name='partidos'),
]