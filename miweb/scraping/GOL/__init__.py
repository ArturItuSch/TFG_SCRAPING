"""
El submódulo `Gol` contiene la lógica de scraping dedicada a la plataforma [gol.gg](https://gol.gg),
una fuente clave de estadísticas competitivas de League of Legends.

### Archivo principal

- `scraping_gol.py`: Encargado de extraer datos detallados sobre campeones utilizados en partidas
  profesionales, como frecuencia de selección, bloqueos y winrates. Además, gestiona la interacción
  inicial con la página, incluyendo la aceptación automática de cookies y políticas de uso mediante
  el navegador controlado (ChromeDriver).

### Características

- Uso de scraping dinámico mediante Selenium para interactuar con la web.
- Extracción estructurada de estadísticas de campeones.
- Integración con `driver.py` para cargar la extensión y navegar automáticamente.
- Lógica robusta para manejar banners, políticas de privacidad y eventos emergentes.

Este submódulo forma parte esencial del pipeline de scraping de datos competitivos, asegurando
que la información de campeones esté siempre actualizada y correctamente extraída.
"""