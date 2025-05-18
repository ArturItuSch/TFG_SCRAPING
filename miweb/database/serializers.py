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
        
from rest_framework import serializers
from .models import JugadorEnPartida

class JugadorEnPartidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = JugadorEnPartida
        fields = [
            'jugador',
            'partido',
            'campeon',
            'position',
            'kills',
            'deaths',
            'assists',
            'doublekills',
            'triplekills',
            'quadrakills',
            'pentakills',
            'firstbloodkill',
            'firstbloodassist',
            'firstbloodvictim',
            'damagetochampions',
            'damagetaken',
            'wardsplaced',
            'wardskilled',
            'controlwardsbought',
            'visionscore',
            'totalgold',
            'total_cs',
            'minionkills',
            'monsterkills',
            'goldat10',
            'xpat10',
            'csat10',
            'killsat10',
            'assistsat10',
            'deathsat10',
            'goldat15',
            'xpat15',
            'csat15',
            'killsat15',
            'assistsat15',
            'deathsat15',
            'goldat20',
            'xpat20',
            'csat20',
            'killsat20',
            'assistsat20',
            'deathsat20',
            'goldat25',
            'xpat25',
            'csat25',
            'killsat25',
            'assistsat25',
            'deathsat25',
        ]