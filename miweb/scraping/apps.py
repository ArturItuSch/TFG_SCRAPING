from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

class ScrapingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scraping'

    def ready(self):
        from scraping.update_service import actualizar_datos_desde_ultimo_csv

        if not hasattr(self, 'scheduler_started'):
            scheduler = BackgroundScheduler()
            scheduler.add_job(
                actualizar_datos_desde_ultimo_csv,
                CronTrigger(hour=14, minute=45),  
                id='actualizar_csv_diario',
                replace_existing=True
            )

            scheduler.start()
            self.scheduler_started = True

            logging.getLogger(__name__).info("⏳ Scheduler iniciado desde AppConfig.")
