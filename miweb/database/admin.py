from django.contrib import admin
from .models import Seleccion, Jugador, Partido, Equipo, Campeon, JugadorEnPartida, ObjetivoNeutral, ObjetivosNeutralesMatados

admin.site.register(Seleccion)
admin.site.register(Jugador)
admin.site.register(Partido)
admin.site.register(Equipo)
admin.site.register(Campeon)
admin.site.register(JugadorEnPartida)
admin.site.register(ObjetivoNeutral)
admin.site.register(ObjetivosNeutralesMatados)