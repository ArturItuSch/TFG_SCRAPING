from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings

from . import views



urlpatterns = [
    path('', lambda request: redirect('index', permanent=False)),
    path('index/', views.index, name='index'),
    path('splits/', views.splits, name='splits'),
    #path('splits/<int:year>/<str:split_type>/', views.detalle_split, name='detalle_split'),
    
    path('equipos/', views.equipos, name='equipos'),
    path('equipos/detalle/<str:equipo_id>/', views.detalle_equipo, name='detalle_equipo'),
    #path('equipos/<str:id>/jugadores/', views.jugadores_equipo, name='jugadores_equipo'),

    path('jugadores/', views.jugadores, name='jugadores'),
    path('jugador/<uuid:jugador_id>/', views.detalle_jugador, name='detalle_jugador'),   

    path('partidos/', views.partidos, name='partidos'),
    #path('partidos/<str:id>/', views.detalle_partido, name='detalle_partido'),

    #path('series/<str:id>/', views.detalle_serie, name='detalle_serie'),
    path('campeones/', views.campeones, name='campeones'),
    
    path('series/', views.series_jugadas, name='series_jugadas'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)