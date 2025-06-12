"""
Comando personalizado de Django para insertar los datos base del proyecto LEC.

Este comando se utiliza principalmente al crear una nueva base de datos desde cero.
Automatiza el proceso de carga de todos los datos esenciales necesarios para que
la plataforma funcione correctamente.

Funciones incluidas:
- Inserción de splits históricos.
- Inserción de series y partidos.
- Inserción de jugadores y sus estadísticas.
- Inserción de objetivos neutrales.
- Inserción de picks y bans.

Este comando depende de la función `insertar_datos_base` definida en `scraping.update_service`.

Uso:
    python manage.py insertar_datos_base

Ejemplo de salida:
    🚀 Insertando datos base...
    ✅ Datos base insertados correctamente
"""
from django.core.management.base import BaseCommand
from django.conf import settings

BASE_DIR = settings.BASE_DIR
from scraping.update_service import insertar_datos_base

class Command(BaseCommand):
    help = "Inserta los datos base del proyecto LEC"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Insertando datos base..."))
        insertar_datos_base()
        self.stdout.write(self.style.SUCCESS("✅ Datos base insertados correctamente"))