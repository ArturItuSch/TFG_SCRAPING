"""
Este paquete contiene filtros personalizados de Django utilizados en las plantillas HTML
del frontend del proyecto.

Actualmente incluye:
- `custom_filters.py`: define filtros personalizados utilizados en las vistas para 
  mejorar la presentación de datos como porcentajes, formatos de fecha, etc.

Para que los filtros estén disponibles en las plantillas, asegúrate de usar:
    {% load custom_filters %}
"""