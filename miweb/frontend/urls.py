from django.urls import path
from . import views


urlpatterns = [
    path('index/', views.index, name='index'),
    path('splits/', views.splits, name='splits'),
    path('equipos/', views.equipos, name='equipos'),
    path('jugadores/', views.jugadores, name='jugadores'),
    path('partidos/', views.partidos, name='partidos'),
]