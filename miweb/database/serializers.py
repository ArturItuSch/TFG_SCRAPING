"""
serializers.py
==============

Este módulo define los serializadores para los modelos del proyecto, utilizando
el framework `Django REST Framework`.

Cada clase representa un serializador para un modelo específico, permitiendo
convertir instancias de modelos Django en formatos JSON (u otros formatos
compatibles con REST), y viceversa.

Serializadores definidos:
- CampeonSerializer
- SplitLECSerializer
- SerieSerializer
- PartidoSerializer
- EquipoSerializer
- JugadorSerializer
- JugadorEnPartidaSerializer
- SeleccionSerializer (con relaciones explícitas)
- ObjetivosNeutralesSerializer

Algunos serializadores definen relaciones foráneas con `PrimaryKeyRelatedField`
para facilitar la validación e inserción desde peticiones externas.

Estos serializadores son fundamentales para las vistas API o para importar datos
de manera controlada desde fuentes externas.
"""
from rest_framework import serializers
from .models import *

class CampeonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campeon
        fields = '__all__'

class SplitLECSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitLEC
        fields = '__all__'
        
class SerieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serie
        fields = '__all__'

class PartidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partido
        fields = '__all__'
        
class EquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipo
        fields = '__all__'
        
    
class JugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = '__all__'


class JugadorEnPartidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = JugadorEnPartida
        fields = fields = '__all__'

class SeleccionSerializer(serializers.ModelSerializer):
    equipo = serializers.PrimaryKeyRelatedField(queryset=Equipo.objects.all())
    partido = serializers.PrimaryKeyRelatedField(queryset=Partido.objects.all())
    campeon_seleccionado = serializers.PrimaryKeyRelatedField(queryset=Campeon.objects.all())
    campeon_baneado = serializers.PrimaryKeyRelatedField(
        queryset=Campeon.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Seleccion
        fields = fields = '__all__'
        
class ObjetivosNeutralesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjetivosNeutrales
        fields = '__all__'

