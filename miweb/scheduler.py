from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from scraping.update_service import actualizar_datos_desde_ultimo_csv  # importa tu función principal

def start():
    scheduler = BlockingScheduler()
    
    # Ejecuta cada día a las 6 AM (hora local)
    scheduler.add_job(actualizar_datos_desde_ultimo_csv, CronTrigger(hour=6, minute=0))
    
    print("⏳ APScheduler iniciado... Esperando tareas programadas.")
    scheduler.start()

if __name__ == "__main__":
    start()