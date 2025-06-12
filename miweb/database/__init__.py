"""
database
========

Este paquete contiene todos los modelos y serializadores asociados con la base de datos
de la aplicación LEC Stats.

Módulos incluidos:
------------------
- models.py: Define los modelos Django que representan las entidades del dominio,
  tales como Jugadores, Equipos, Partidos, Campeones, Splits, Selecciones, etc.
- serializers.py: Proporciona serializadores DRF (Django REST Framework) para
  transformar los modelos en formatos JSON y viceversa.

Uso:
----
Este paquete es utilizado por vistas de Django, scripts de scraping, y comandos de
gestión para consultar, insertar y actualizar los datos de forma estructurada.

Relacionado:
------------
- Utilizado extensivamente por el módulo `scraping` para insertar datos.
- Integrado con las vistas del módulo `frontend` para mostrar estadísticas.

"""