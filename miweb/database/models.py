from django.db import models
from django.forms.models import model_to_dict

class SplitLEC(models.Model):
    split_id = models.CharField(max_length=200, primary_key=True, blank=True)
    split_type = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    league = models.CharField(max_length=10)

    def save(self, *args, **kwargs):
        self.split_id = f"{self.split_type}_{self.year}"
        super().save(*args, **kwargs)

class Serie(models.Model):
    id = models.CharField(max_length=200, primary_key=True)    
    split = models.ForeignKey(SplitLEC, on_delete=models.CASCADE, related_name='series')
    num_partidos = models.IntegerField(null=True, blank=True)
    patch = models.FloatField(null=True, blank=True)
    dia = models.DateField(null=True, blank=True)
    
    def to_dict(self):
        return model_to_dict(self)  
    
class Equipo(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    nombre = models.CharField(max_length=100)
    pais =  models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    propietario = models.CharField(max_length=100, null=True, blank=True)
    head_coach = models.CharField(max_length=100, null=True, blank=True)
    partners = models.CharField(max_length=100, null=True, blank=True)
    fecha_fundacion = models.DateField(null=True, blank=True)
    logo = models.CharField(max_length=100, null=True, blank=True)
    activo = models.BooleanField(default=True)
    def to_dict(self):
        return model_to_dict(self)

class Partido(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, related_name='partidos')
    hora = models.TimeField(null=True, blank=True)
    orden = models.IntegerField(null=True, blank=True)
    duracion = models.IntegerField(null=True, blank=True)
    equipo_azul = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidos_azul')
    equipo_rojo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidos_rojo')
    equipo_ganador = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidos_ganados')

    def to_dict(self):
        return model_to_dict(self)
    def to_dict(self):
        return model_to_dict(self)
 
class Jugador(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    nombre = models.CharField(max_length=100)
    real_name = models.CharField(max_length=100, null=True, blank=True)
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True)
    residencia = models.CharField(max_length=100, null=True, blank=True)
    rol = models.CharField(max_length=100, null=True, blank=True)
    pais = models.CharField(max_length=100, null=True, blank=True)
    nacimiento = models.DateField(null=True, blank=True)
    soloqueue_ids = models.CharField(max_length=100, null=True, blank=True)
    contratado_hasta = models.DateField(null=True, blank=True)
    contratado_desde = models.DateField(null=True, blank=True)
    imagen = models.CharField(max_length=100, null=True, blank=True)
    activo = models.BooleanField(default=True)
    def to_dict(self):
        return model_to_dict(self)
    
class Campeon(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    nombre = models.CharField(max_length=100, null=True, blank=True) 
    imagen = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nombre
    
    
class ObjetivoNeutral(models.Model):
    nombre = models.CharField(max_length=100, primary_key=True)
    imagen = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.nombre

class ObjetivosNeutralesMatados(models.Model):
    partida = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='objetivos_neutrales_matados')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='objetivos_neutrales_matados')
    objetivo_neutral = models.ForeignKey(ObjetivoNeutral, on_delete=models.CASCADE, related_name='muertes')
    cantidad = models.PositiveIntegerField(null=True, blank=True)
    firstdragon = models.BooleanField(null=True, blank=True)
    class Meta:
        unique_together = ('partida', 'equipo', 'objetivo_neutral')

    def __str__(self):
        return f"{self.partida.id} - {self.equipo.nombre} - {self.objetivo_neutral.nombre} x{self.cantidad}" 


class JugadorEnPartida(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.SET_NULL, null=True, blank=True)
    partido = models.ForeignKey(Partido, on_delete=models.SET_NULL, null=True, blank=True)
    campeon = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True, blank=True) #champion
    position = models.CharField(max_length=10, null=True, blank=True) #position
    kills = models.PositiveIntegerField(null=True, blank=True) #kills
    deaths = models.PositiveIntegerField(null=True, blank=True) #deaths
    assists = models.PositiveIntegerField(null=True, blank=True) #assists
    doublekills = models.PositiveIntegerField(null=True, blank=True) #doublekills
    triplekills = models.PositiveIntegerField(null=True, blank=True) #triplekills
    quadrakills = models.PositiveIntegerField(null=True, blank=True) #quadrakills
    pentakills = models.PositiveIntegerField(null=True, blank=True) #pentakills
    firstbloodkill = models.BooleanField(null=True, blank=True) #firstbloodkill
    firstbloodassist = models.BooleanField(null=True, blank=True) #firstbloodassist   
    firstbloodvictim = models.BooleanField(null=True, blank=True) #firstbloodvictim

    damagetochampions = models.FloatField(null=True, blank=True) #damagetochampions
    damagetaken = models.FloatField(null=True, blank=True) #damagetaken
    wardsplaced = models.PositiveIntegerField(null=True, blank=True) #wardsplaced
    wardskilled = models.PositiveIntegerField(null=True, blank=True) #wardskilled 
    controlwardsbought = models.PositiveIntegerField(null=True, blank=True) #controlwardsbought
    visionscore = models.PositiveIntegerField(null=True, blank=True) #visionscore
    totalgold = models.PositiveIntegerField(null=True, blank=True) #totalgold
    total_cs = models.PositiveIntegerField(null=True, blank=True) #total_cs
    minionkills = models.PositiveIntegerField(null=True, blank=True) #minionkills
    monsterkills = models.PositiveIntegerField(null=True, blank=True) #monsterkills

    goldat10 = models.FloatField(null=True, blank=True) 
    xpat10 = models.FloatField(null=True, blank=True)
    csat10 = models.FloatField(null=True, blank=True)

    killsat10 = models.FloatField(null=True, blank=True)
    assistsat10 = models.FloatField(null=True, blank=True)
    deathsat10 = models.FloatField(null=True, blank=True)

    goldat15 = models.FloatField(null=True, blank=True)
    xpat15 = models.FloatField(null=True, blank=True)
    csat15 = models.FloatField(null=True, blank=True)

    killsat15 = models.FloatField(null=True, blank=True)
    assistsat15 = models.FloatField(null=True, blank=True)
    deathsat15 = models.FloatField(null=True, blank=True)

    goldat20 = models.FloatField(null=True, blank=True)
    xpat20 = models.FloatField(null=True, blank=True)
    csat20 = models.FloatField(null=True, blank=True)

    killsat20 = models.FloatField(null=True, blank=True)
    assistsat20 = models.FloatField(null=True, blank=True)
    deathsat20 = models.FloatField(null=True, blank=True)

    goldat25 = models.FloatField(null=True, blank=True)
    xpat25 = models.FloatField(null=True, blank=True)
    csat25 = models.FloatField(null=True, blank=True)

    killsat25 = models.FloatField(null=True, blank=True)
    assistsat25 = models.FloatField(null=True, blank=True)
    deathsat25 = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.jugador} en {self.partido} ({self.position})"

    def get_opponent(self):
        return JugadorEnPartida.objects.filter(
            partido=self.partido,
            position=self.position
        ).exclude(jugador__equipo=self.jugador.equipo).first()
        
    class Meta:
        unique_together = ('jugador', 'partido')

class Seleccion(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True)
    partido = models.ForeignKey(Partido, on_delete=models.SET_NULL, null=True, blank=True)    
    seleccion = models.IntegerField() 
    campeon_seleccionado = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True, blank=True, related_name='selecciones')
    baneo = models.IntegerField(null=True, blank=True)  
    campeon_baneado = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True, blank=True, related_name='baneos')

    class Meta:
        unique_together = ('equipo', 'partido', 'campeon_seleccionado')

    def __str__(self):
        return f"{self.equipo} seleccionó {self.campeon_seleccionado} y baneó {self.campeon_baneado} en {self.partido}"