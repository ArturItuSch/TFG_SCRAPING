"""
Archivo `scraping.apps.py`

Aquí se configura la aplicación `scraping` y lanza un **scheduler automático** mediante 
APScheduler al iniciar el proyecto Django.

Clases:
-------
- `ScrapingConfig`: 
    Configuración principal de la app `scraping`. Al ejecutarse, inicia un `BackgroundScheduler`
    que se encarga de programar tareas automáticas.

Tareas programadas:
-------------------
- `actualizar_datos_desde_ultimo_csv`:
    Función que se ejecuta automáticamente cada día a las 06:00 AM, definida en `scraping.update_service`.
    Se encarga de detectar y procesar el último CSV descargado desde Google Drive para mantener la base de datos actualizada.

Notas:
------
- El scheduler se inicia solo una vez gracias a la verificación `hasattr(self, 'scheduler_started')`.
- El sistema usa `CronTrigger` para ejecutar la tarea diaria en segundo plano sin bloquear el hilo principal.

Este mecanismo es útil para mantener sincronizados los datos del sistema sin necesidad de intervención manual.
"""
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
                CronTrigger(hour=6, minute=0),  
                id='actualizar_csv_diario',
                replace_existing=True
            )

            scheduler.start()
            self.scheduler_started = True

            logging.getLogger(__name__).info("⏳ Scheduler iniciado desde AppConfig.")
