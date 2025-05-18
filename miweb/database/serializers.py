from rest_framework import serializers
from .models import *

class CampeonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campeon
        fields = ['id', 'nombre', 'imagen']

class SplitLECSerializer(serializers.ModelSerializer):
    class Meta:
        model = SplitLEC
        fields = ['split_type', 'year', 'league', 'split_id']
        
class SerieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Serie
        fields = ['id', 'split', 'num_partidos', 'patch', 'dia']

class PartidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partido
        fields = ['id', 'serie', 'hora', 'orden', 'duracion', 'equipo_azul', 'equipo_rojo', 'equipo_ganador']
        
class EquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipo
        fields = ['id', 'nombre', 'pais', 'region', 'propietario', 'head_coach', 'partners', 'fecha_fundacion', 'logo', 'activo']
        
    
class JugadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Jugador
        fields = ['id', 'nombre', 'real_name', 'equipo', 'residencia', 'rol', 'pais', 'nacimiento', 'soloqueue_ids', 'contratado_hasta', 'contratado_desde', 'imagen', 'activo']