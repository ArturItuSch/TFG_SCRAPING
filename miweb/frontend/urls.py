"""
urls.py
=======

Este módulo define las rutas URL principales para la aplicación `frontend` de Django.
Agrupa todas las vistas públicas del proyecto que componen el frontend de la plataforma
de visualización de datos de la LEC.

Incluye redirecciones, listados de splits, equipos, jugadores, campeones, y vistas 
detalladas de series y partidas.

Estructura de rutas:
--------------------

- `/` → Redirige a `/index/`
- `/index/` → Página principal
- `/splits/` → Vista de todos los splits disponibles
- `/splits/<split_id>/` → Detalle de un split específico
- `/equipos/` → Listado de equipos activos e históricos
- `/equipos/detalle/<equipo_id>/` → Información detallada de un equipo
- `/jugadores/` → Listado de jugadores
- `/jugador/<jugador_id>/` → Detalle de un jugador
- `/campeones/` → Información general de campeones
- `/series/` → Historial de series jugadas
- `/series/<id>/` → Información de una serie específica
- `/partido/<id>/` → Información detallada de un partido

Notas:
------
- Durante desarrollo (`DEBUG=True`), se sirve contenido estático y media desde el propio Django.
- Se usa `redirect()` para redireccionar la raíz del sitio a `/index/`.

"""
from django.urls import path, include
from django.shortcuts import redirect
from django.conf.urls.static import static
from django.conf import settings

from . import views



urlpatterns = [
    path('', lambda request: redirect('index', permanent=False)),
    path('index/', views.index, name='index'),
    path('splits/', views.splits, name='splits'),
    path('splits/<str:split_id>/', views.detalle_split, name='detalle_split'),
    
    path('equipos/', views.equipos, name='equipos'),
    path('equipos/detalle/<str:equipo_id>/', views.detalle_equipo, name='detalle_equipo'),

    path('jugadores/', views.jugadores, name='jugadores'),
    path('jugador/<uuid:jugador_id>/', views.detalle_jugador, name='detalle_jugador'),   

    path('campeones/', views.campeones, name='campeones'),
    
    path('series/', views.series_jugadas, name='series_jugadas'),
    path('series/<str:id>/', views.detalle_serie, name='serie_info'),
    path('partido/<str:id>/', views.partido_info, name='partido_info'),

]

# Rutas para servir archivos en entorno de desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)