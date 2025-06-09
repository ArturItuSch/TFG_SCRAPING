from django.core.management.base import BaseCommand
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings

BASE_DIR = settings.BASE_DIR
from scraping.update_service import actualizar_datos_desde_ultimo_csv  

import signal
import time

class Command(BaseCommand):
    help = 'Inicia el scheduler para importar el último CSV automáticamente'

    def add_arguments(self, parser):
        parser.add_argument('--now', action='store_true', help='Ejecutar la importación inmediatamente')

    def handle(self, *args, **options):
        if options['now']:
            self.stdout.write(self.style.SUCCESS("⚡ Ejecutando importación inmediata..."))
            try:
                actualizar_datos_desde_ultimo_csv()
                self.stdout.write(self.style.SUCCESS("✅ Importación completada con éxito."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error durante la importación: {e}"))
            return

        scheduler = BackgroundScheduler()
        scheduler.add_job(actualizar_datos_desde_ultimo_csv, CronTrigger(hour=6, minute=0))

        self.stdout.write(self.style.SUCCESS("⏳ Scheduler iniciado. Ejecutando diariamente a las 6:00 AM."))

        scheduler.start()

        def detener_scheduler(signal_num, frame):
            scheduler.shutdown()
            self.stdout.write(self.style.WARNING("🚫 Scheduler detenido manualmente."))
            exit(0)

        signal.signal(signal.SIGINT, detener_scheduler)
        signal.signal(signal.SIGTERM, detener_scheduler)

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            detener_scheduler(None, None)