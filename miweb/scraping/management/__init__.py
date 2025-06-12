"""
Módulo de inicialización para la carpeta `scraping/management`.

Este paquete contiene comandos personalizados de Django utilizados para la automatización
de tareas relacionadas con el procesamiento y actualización de datos en el proyecto LEC Stats.

Los comandos permiten ejecutar funcionalidades clave del sistema de scraping directamente
desde la línea de comandos de Django mediante `manage.py`.

Estructura de uso:
    - Cada comando debe ubicarse dentro del submódulo `scraping/management/commands/`
    - Los scripts dentro de `commands/` deben extender `BaseCommand` de Django.
    - Los comandos disponibles pueden ejecutarse mediante: `python manage.py <comando>`

Este paquete forma parte del sistema de integración y mantenimiento de datos de la plataforma.
"""