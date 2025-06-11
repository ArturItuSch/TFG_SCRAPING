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