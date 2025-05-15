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