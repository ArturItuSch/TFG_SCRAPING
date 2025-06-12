"""
El submódulo `OracleElexir` contiene la lógica de procesamiento de archivos CSV descargados desde
Google Drive, específicamente los publicados por Oracle's Elixir, una de las principales fuentes de
datos estadísticos del competitivo de League of Legends.

### Script principal

- `csv_process.py`: Contiene funciones para procesar, transformar y estructurar los datos provenientes
  de los archivos CSV, como partidas, estadísticas de jugadores, eventos en partida, entre otros.

Este módulo se utiliza como parte del proceso automatizado de ingestión de datos históricos y
actuales, permitiendo transformar archivos descargados desde Google Drive (API) en información
estructurada lista para análisis o visualización.

**Requisitos**: Los archivos CSV deben provenir del formato estándar definido por Oracle's Elixir.

"""