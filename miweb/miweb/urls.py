"""
urls.py
=======

Configuración de rutas (URL routing) principal del proyecto `miweb`.

Este archivo centraliza todas las rutas que redirigen a las vistas del proyecto.
Es el punto de entrada para determinar cómo se manejan las URLs dentro de la aplicación Django.

Rutas incluidas:
- `/admin/`: Acceso al panel de administración de Django.
- `/` (raíz): Delegada al módulo de rutas de la app `frontend`.

Este archivo utiliza la función `include()` para permitir que cada aplicación
gestione sus propias rutas, manteniendo una arquitectura modular y mantenible.

Para más información sobre el enrutamiento en Django:
https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('frontend.urls')),  
]
