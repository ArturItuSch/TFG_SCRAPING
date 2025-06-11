from rest_framework import serializers
from .models import *
import urllib.parse

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

