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