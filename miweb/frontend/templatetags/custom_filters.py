"""
custom_filters.py
=================

Este módulo define filtros personalizados para plantillas Django que amplían 
la funcionalidad estándar del sistema de templates.

Los filtros registrados permiten realizar operaciones útiles directamente desde
las plantillas HTML, como acceder a diccionarios por clave, dividir cadenas y
acceder a índices de listas.

Filtros disponibles:
--------------------
- `dictget`: Permite acceder a un valor dentro de un diccionario usando una clave.
- `split`: Divide una cadena por un delimitador y devuelve una lista.
- `index`: Devuelve el elemento de una lista dado un índice.

"""
from django import template

register = template.Library()

@register.filter
def dictget(dictionary, key):
    return dictionary.get(key)


@register.filter
def split(value, delimiter=","):
    """Divide una cadena usando el delimitador dado."""
    return value.split(delimiter)

@register.filter
def index(sequence, position):
    """Devuelve el elemento en la posición dada de una lista."""
    try:
        return sequence[int(position)]
    except (IndexError, ValueError, TypeError):
        return ''