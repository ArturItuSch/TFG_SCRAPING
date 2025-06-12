"""
miweb
=====

Este paquete contiene los archivos de configuración del proyecto Django, incluyendo:

- **settings.py**: Configuración principal del proyecto Django (bases de datos, apps, rutas estáticas, autenticación, etc.).
- **urls.py**: Enrutamiento principal del proyecto (vincula las URLs globales con las aplicaciones).
- **wsgi.py**: Punto de entrada para servidores WSGI (usado en producción por servidores como Gunicorn o uWSGI).
- **asgi.py**: Punto de entrada para servidores ASGI (para soporte asíncrono con WebSockets o tareas concurrentes).
- **__init__.py**: Archivo necesario para tratar `miweb` como un módulo de Python.

Este módulo actúa como el **núcleo de configuración del proyecto Django**, permitiendo que se comuniquen correctamente las aplicaciones internas, los servicios externos (bases de datos, autenticación, almacenamiento) y el servidor de despliegue.
"""