from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings

BASE_DIR = settings.BASE_DIR
from database.models import Equipo
from scraping.Leaguepedia.leguepedia_old_sesons import (
    get_urls_sesons,
    extraer_equipos,
    quitar_duplicados
)

class Command(BaseCommand):
    help = 'Scrapea y actualiza los equipos históricos en la base de datos.'

    def handle(self, *args, **options):
        # 1. Obtener todas las URLs de temporadas antiguas
        temporadas = get_urls_sesons()
        if not temporadas:
            self.stdout.write(self.style.WARNING('No se obtuvieron URLs de temporadas.'))
            return

        all_teams = []
        # 2. Extraer equipos de cada temporada
        for url in temporadas:
            equipos = extraer_equipos(url)
            all_teams.extend(equipos)

        # 3. Quitar duplicados en memoria (comparando por 'name')
        before = len(all_teams)
        equipos_unicos = quitar_duplicados(all_teams, clave='name')
        after = len(equipos_unicos)
        self.stdout.write(f'Equipos extraídos: {before} → tras deduplicar: {after}')

        # 4. Para cada dict único, crear/actualizar Equipo
        for data in equipos_unicos:
            # a) Normaliza nombre y genera un id slug
            nombre_raw = data['name']           
            nombre     = nombre_raw.replace('_', ' ')
            equipo_id  = slugify(nombre)          

            # b) Extrae la URL de la imagen
            logo_url = data.get('imagen_url') or ''

            # c) update_or_create
            equipo, created = Equipo.objects.update_or_create(
                id=equipo_id,
                defaults={
                    'nombre': nombre,
                    'logo': logo_url,
                    'activo': False,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creado histórico: {nombre}'))
            else:
                self.stdout.write(f'Actualizado histórico: {nombre}')

        self.stdout.write(self.style.NOTICE('Proceso concluido.'))