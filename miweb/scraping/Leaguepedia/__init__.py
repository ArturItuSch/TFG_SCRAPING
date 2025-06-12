"""
El submódulo `Leaguepedia` se encarga de realizar scraping sobre la plataforma [Leaguepedia](https://lol.fandom.com),
una wiki colaborativa muy utilizada en el ecosistema competitivo de League of Legends.

Este módulo recopila tanto información **actual** como **histórica** de equipos y jugadores profesionales
de la LEC (League of Legends EMEA Championship), facilitando el análisis y visualización de trayectorias,
plantillas y cambios de temporada en la plataforma.

### Archivos principales

- `leaguepedia_teams_players.py`: Extrae datos actualizados de equipos y jugadores activos. Se centra en
  el split actual y plantillas vigentes.
  
- `leaguepedia_old_sesions.py`: Realiza scraping de sesiones históricas anteriores, recopilando datos de
   equipos.

- `importar_datos.py`: Script auxiliar que ejecuta y coordina los scripts anteriores para actualizar los
  datos desde Leaguepedia. Es utilizado tanto de forma manual como programada (por el scheduler APScheduler).

### Características destacadas

- Extracción completa y estructurada de plantillas activas e históricas.
- Mapeo de jugadores a equipos por split y año.
- Compatible con tareas programadas y procesos automáticos de actualización.
- Manejo robusto de datos faltantes o estructuras cambiantes en la wiki.

Este submódulo es clave para enriquecer la base de datos con contexto histórico y actual del entorno
competitivo profesional, ofreciendo una fuente alternativa y complementaria a gol.gg.
"""