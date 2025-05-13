from django.db import models
from django.forms.models import model_to_dict


class SplitLEC(models.Model):
    split_type = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    league = models.CharField(max_length=10)
    split_id = models.CharField(max_length=200, unique=True, blank=True)  

    def save(self, *args, **kwargs):
        # Generar el split_id combinando split_type y year
        self.split_id = f"{self.split_type}_{self.year}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.split_type} {self.year}"
    
    def to_dict(self):
        return model_to_dict(self)

class Serie(models.Model):
    split = models.ForeignKey(SplitLEC, on_delete=models.CASCADE, related_name='series')
    num_partidos = models.IntegerField(null=True, blank=True)
    patch = models.FloatField(null=True, blank=True)
    
    def to_dict(self):
        return model_to_dict(self)  

class Partido(models.Model):
    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, related_name='partidos')
    fecha = models.DateTimeField(null=True, blank=True)
    orden = models.IntegerField(null=True, blank=True)
    duracion = models.IntegerField(null=True, blank=True)
    
    def to_dict(self):
        return model_to_dict(self)
    
class Equipo(models.Model):
    nombre = models.CharField(max_length=100)
    pais =  models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    propietario = models.CharField(max_length=100, null=True, blank=True)
    head_coach = models.CharField(max_length=100, null=True, blank=True)
    partners = models.CharField(max_length=100, null=True, blank=True)
    fecha_fundacion = models.DateField(null=True, blank=True)
    logo = models.CharField(max_length=100, null=True, blank=True)
    
    def to_dict(self):
        return model_to_dict(self)
    
class Jugador(models.Model):
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

    def to_dict(self):
        return model_to_dict(self)
    
class Campeon(models.Model):
    nombre = models.CharField(max_length=100, primary_key=True)  # Usamos 'nombre' como el ID principal
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
    jugador = models.OneToOneField(Jugador, on_delete=models.SET_NULL, null=True, blank=True)
    partido = models.OneToOneField(Partido, on_delete=models.SET_NULL, null=True, blank=True)
    campeon = models.OneToOneField(Campeon, on_delete=models.SET_NULL, null=True, blank=True)
    side = models.CharField(max_length=10, null=True, blank=True)
    position = models.CharField(max_length=10, null=True, blank=True)

    kills = models.PositiveIntegerField(null=True, blank=True)
    deaths = models.PositiveIntegerField(null=True, blank=True)
    assists = models.PositiveIntegerField(null=True, blank=True)
    doublekills = models.PositiveIntegerField(null=True, blank=True)
    triplekills = models.PositiveIntegerField(null=True, blank=True)
    quadrakills = models.PositiveIntegerField(null=True, blank=True)
    pentakills = models.PositiveIntegerField(null=True, blank=True)
    firstbloodkill = models.BooleanField(null=True, blank=True)
    firstbloodassist = models.BooleanField(null=True, blank=True)
    firstbloodvictim = models.BooleanField(null=True, blank=True)

    damagetochampions = models.PositiveIntegerField(null=True, blank=True)
    wardsplaced = models.PositiveIntegerField(null=True, blank=True)
    wardskilled = models.PositiveIntegerField(null=True, blank=True)
    controlwardsbought = models.PositiveIntegerField(null=True, blank=True)
    visionscore = models.PositiveIntegerField(null=True, blank=True)
    totalgold = models.PositiveIntegerField(null=True, blank=True)
    total_cs = models.PositiveIntegerField(null=True, blank=True)
    minionkills = models.PositiveIntegerField(null=True, blank=True)
    monsterkills = models.PositiveIntegerField(null=True, blank=True)

    goldat10 = models.IntegerField(null=True, blank=True)
    xpat10 = models.IntegerField(null=True, blank=True)
    csat10 = models.IntegerField(null=True, blank=True)

    killsat10 = models.IntegerField(null=True, blank=True)
    assistsat10 = models.IntegerField(null=True, blank=True)
    deathsat10 = models.IntegerField(null=True, blank=True)

    goldat15 = models.IntegerField(null=True, blank=True)
    xpat15 = models.IntegerField(null=True, blank=True)
    csat15 = models.IntegerField(null=True, blank=True)

    killsat15 = models.IntegerField(null=True, blank=True)
    assistsat15 = models.IntegerField(null=True, blank=True)
    deathsat15 = models.IntegerField(null=True, blank=True)

    goldat20 = models.IntegerField(null=True, blank=True)
    xpat20 = models.IntegerField(null=True, blank=True)
    csat20 = models.IntegerField(null=True, blank=True)

    killsat20 = models.IntegerField(null=True, blank=True)
    assistsat20 = models.IntegerField(null=True, blank=True)
    deathsat20 = models.IntegerField(null=True, blank=True)

    goldat25 = models.IntegerField(null=True, blank=True)
    xpat25 = models.IntegerField(null=True, blank=True)
    csat25 = models.IntegerField(null=True, blank=True)

    killsat25 = models.IntegerField(null=True, blank=True)
    assistsat25 = models.IntegerField(null=True, blank=True)
    deathsat25 = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.jugador} en {self.partido} ({self.position})"

    def get_opponent(self):
        return JugadorEnPartida.objects.filter(
            partido=self.partido,
            position=self.position
        ).exclude(jugador__equipo=self.jugador.equipo).first()
        
    class Meta:
        unique_together = ('jugador', 'partido', 'campeon')

class Seleccion(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True)
    partido = models.ForeignKey(Partido, on_delete=models.SET_NULL, null=True, blank=True)
    campeon = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True, blank=True, related_name='selecciones_base')
    
    seleccion = models.IntegerField()  # Orden de selección 1, 2, 3, 4, 5
    campeon_seleccionado = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True, blank=True, related_name='selecciones')
    
    baneo = models.IntegerField(null=True, blank=True)  # Orden de baneo
    campeon_baneado = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True, blank=True, related_name='baneos')

    class Meta:
        unique_together = ('equipo', 'partido', 'campeon')

    def __str__(self):
        return f"{self.equipo} seleccionó {self.campeon_seleccionado} y baneó {self.campeon_baneado} en {self.partido}"