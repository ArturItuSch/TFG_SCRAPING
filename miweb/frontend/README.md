# Carpeta `templates`

Esta carpeta contiene todas las plantillas HTML utilizadas por la aplicación Django para renderizar las vistas del frontend. Cada archivo representa una sección específica del sitio o una vista concreta relacionada con los datos de la LEC (League of Legends EMEA Championship).

## Estructura de plantillas

| Archivo HTML         | Descripción                                                                     |
|----------------------|---------------------------------------------------------------------------------|
| `base.html`          | Plantilla base principal que heredan todas las demás. Define el layout general. |
| `index.html`         | Página de inicio con resumen de estadísticas, últimos partidos y splits.        |
| `campeones.html`     | Vista con todos los campeones y estadísticas asociadas.                         |
| `equipos.html`       | Muestra todos los equipos activos de la LEC.                                    |
| `detalle_equipo.html`| Detalle individual de un equipo: jugadores, estadísticas, logo, etc.            |
| `jugadores.html`     | Página con todos los jugadores activos y sus estadísticas generales.            |
| `detalle_jugador.html`| Vista detallada por jugador con estadísticas individuales y comparativas.      |   
| `splits.html`        | Listado de splits históricos y su filtrado por año/liga.                        |
| `detalle_split.html` | Vista detallada de un split con todas sus series y estadísticas.                |
| `serie_list.html`    | Listado de series jugadas, con filtros por split y resultados.                  |
| `serie_info.html`    | Detalle de una serie: equipos enfrentados, resultado global, fecha.             |
| `partido.html`       | Estadísticas completas de un partido: objetivos, picks, jugadores, etc.         |

## Uso en Django

Todas las vistas en `views.py` de la app `frontend` renderizan estos archivos HTML usando `render(request, "archivo.html", context)`.

---

**Nota:** Esta carpeta debe ser incluida en la configuración de `TEMPLATES['DIRS']` del archivo `settings.py`.

```python
'DIRS': [os.path.join(BASE_DIR, 'frontend', 'templates')],