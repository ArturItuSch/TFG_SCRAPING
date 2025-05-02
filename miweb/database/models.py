from django.db import models

class SplitLEC(models.Model):
    SPLIT_CHOICES = [
        ('Spring', 'Spring'),
        ('Summer', 'Summer'),
        ('Winter', 'Winter'),
    ]
    
    nombre = models.CharField(max_length=10, choices=SPLIT_CHOICES)
    año = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    class Meta:
        unique_together = ('nombre', 'año')

    def __str__(self):
        return f"{self.nombre} {self.año}"

class Serie(models.Model):
    split = models.ForeignKey(SplitLEC, on_delete=models.CASCADE, related_name='series')
    fecha = models.DateTimeField()
    mejor_de = models.IntegerField(choices=[(1, 'Bo1'), (3, 'Bo3'), (5, 'Bo5')])

    class Meta:
        ordering = ['fecha']

class Partido(models.Model):
    serie = models.ForeignKey(Serie, on_delete=models.CASCADE, related_name='partidos')
    fecha = models.DateTimeField()
    equipo_azul = models.ForeignKey('Equipo', on_delete=models.CASCADE, related_name='partidos_azul')
    equipo_rojo = models.ForeignKey('Equipo', on_delete=models.CASCADE, related_name='partidos_rojo')
    duracion = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"{self.equipo_azul.nombre} vs {self.equipo_rojo.nombre} - {self.fecha}"
    
class Equipo(models.Model):
    nombre = models.CharField(max_length=100)
    

class Jugador(models.Model):
    nombre = models.CharField(max_length=100)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='jugadores')

class Campeon(models.Model):
    nombre = models.CharField(max_length=100)

class ObjetivoNeutral(models.Model):
    nombre = models.CharField(max_length=100)

class Objeto(models.Model):
    nombre = models.CharField(max_length=100)

class JugadorEnPartida(models.Model):
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='partidas')
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='jugadores_en_partida')
    campeon = models.ForeignKey(Campeon, on_delete=models.CASCADE, related_name='jugadores_en_partida')
    side = models.CharField(max_length=10)  # blue o red
    posicion = models.CharField(max_length=10)
    resultado = models.BooleanField()  # True si ganó
    kills = models.IntegerField()
    deaths = models.IntegerField()
    assists = models.IntegerField()
    double_kills = models.IntegerField()
    triple_kills = models.IntegerField()
    quadra_kills = models.IntegerField()
    penta_kills = models.IntegerField()
    first_blood = models.BooleanField()
    wards_placed = models.IntegerField()
    wards_killed = models.IntegerField()
    vision_score = models.IntegerField()
    total_gold = models.IntegerField()
    damage_to_champions = models.IntegerField()
    cs_total = models.IntegerField()
    minion_kills = models.IntegerField()
    monster_kills = models.IntegerField()
    monster_kills_own_jungle = models.IntegerField()
    monster_kills_enemy_jungle = models.IntegerField()

    objetos_comprados = models.ManyToManyField(Objeto, related_name='jugadores_en_partida')
    objetivos_neutrales_matados = models.ManyToManyField(ObjetivoNeutral, related_name='jugadores_en_partida')

    class Meta:
        unique_together = ('jugador', 'partido')  # un jugador solo puede aparecer una vez por partida

# Relación tripartita: Equipo - Partido 
class Seleccion(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    campeon = models.ForeignKey(Campeon, on_delete=models.CASCADE)
    orden_seleccion = models.IntegerField()
    orden_baneo = models.IntegerField(null=True, blank=True) 

    class Meta:
        unique_together = ('equipo', 'partido', 'campeon')