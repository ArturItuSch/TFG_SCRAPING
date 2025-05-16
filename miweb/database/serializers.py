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
        fields = ['id', 'split', 'num_partidos', 'patch']

class PartidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partido
        fields = ['id', 'serie', 'fecha', 'orden', 'duracion']