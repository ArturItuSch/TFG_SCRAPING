from django.db import models

from django.db import models

# ------------------ CAMPEONES Y SU ROL ------------------

class Campeon(models.Model):
    # Campeones disponibles para jugar
    ROLES = [
        ('Top', 'Top'),
        ('Jungle', 'Jungle'),
        ('Mid', 'Mid'),
        ('ADC', 'ADC'),
        ('Support', 'Support'),
    ]
    nombre = models.CharField(max_length=100)
    rol = models.CharField(max_length=10, choices=ROLES)  # Rol principal del campeón
    imagen_url = models.URLField(blank=True, null=True)
    veces_jugado = models.IntegerField(default=0)
    veces_baneado = models.IntegerField(default=0)
    winrate = models.FloatField(default=0.0)

    def __str__(self):
        return self.nombre


# ------------------ EQUIPOS Y JUGADORES ------------------

class Equipo(models.Model):
    # Representa a un equipo del LOL
    nombre = models.CharField(max_length=100)
    region = models.CharField(max_length=50)
    pais = models.CharField(max_length=50)
    ano_fundacion = models.IntegerField(null=True, blank=True)
    logo_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Jugador(models.Model):
    # Jugadores que pertenecen a un equipo
    ROLES = [
        ('Top', 'Top'),
        ('Jungle', 'Jungle'),
        ('Mid', 'Mid'),
        ('ADC', 'ADC'),
        ('Support', 'Support'),
    ]
    nombre_real = models.CharField(max_length=100)
    nickname = models.CharField(max_length=50)
    rol = models.CharField(max_length=10, choices=ROLES)
    equipo = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, related_name='jugadores')
    nacimiento = models.DateField(null=True, blank=True)
    nacionalidad = models.CharField(max_length=50)

    def __str__(self):
        return self.nickname

# ------------------ TEMPORADAS Y SPLITS ------------------

class TemporadaLEC(models.Model):
    # Define una temporada específica de la LEC
    año = models.IntegerField()
    nombre = models.CharField(max_length=50, default="LEC")
    
    def __str__(self):
        return f"{self.nombre} {self.año}"


class SplitLEC(models.Model):
    # Ej: Spring, Summer, Winter
    nombre = models.CharField(max_length=50)
    temporada = models.ForeignKey(TemporadaLEC, on_delete=models.CASCADE, related_name='splits')
    inicio = models.DateField()
    fin = models.DateField()

    def __str__(self):
        return f"{self.nombre} ({self.temporada})"


class JornadaLEC(models.Model):
    # Una jornada representa un día o grupo de partidas
    split = models.ForeignKey(SplitLEC, on_delete=models.CASCADE, related_name='jornadas')
    numero = models.IntegerField()
    fecha = models.DateField()

    def __str__(self):
        return f"Jornada {self.numero} - {self.split}"

# ------------------ SERIE Y PARTIDOS ------------------

class Partido(models.Model):
    fecha = models.DateField()
    equipo1 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_equipo1')
    equipo2 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_equipo2')
    ganador = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, related_name='partidos_ganados')
    duracion = models.DurationField()
    serie = models.ForeignKey('Serie', on_delete=models.CASCADE, related_name='partidos', null=True, blank=True)
    numero_en_serie = models.IntegerField(default=1)  # Ej: 1º partido de un BO3
    fase = models.CharField(max_length=100)
    ladoequipo1 = models.CharField(max_length=10, choices=[('Blue', 'Blue'), ('Red', 'Red')])
    ladoequipo1 = models.CharField(max_length=10, choices=[('Blue', 'Blue'), ('Red', 'Red')])
    mvp = models.ForeignKey(Jugador, on_delete=models.SET_NULL, null=True, blank=True, related_name='mvps')
    parche = models.CharField(max_length=20, blank=True, null=True)
    kills_equipo1 = models.IntegerField(default=0)
    kills_equipo2 = models.IntegerField(default=0)
    primera_sangre = models.ForeignKey(Jugador, on_delete=models.SET_NULL, null=True, blank=True, related_name='primeras_sangres')
    primera_torre = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='primeras_torres')

    def __str__(self):
        return f"{self.equipo1} vs {self.equipo2} ({self.fecha})"


class Serie(models.Model):
    # Serie entre dos equipos (puede tener varios partidos si es BO3 o BO5)
    jornada = models.ForeignKey(JornadaLEC, on_delete=models.CASCADE, related_name='series')
    equipo1 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='series_como_equipo1')
    equipo2 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='series_como_equipo2')
    ganador = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='series_ganadas')
    tipo = models.CharField(max_length=10, choices=[('BO1', 'BO1'), ('BO3', 'BO3'), ('BO5', 'BO5')])
    
    def __str__(self):
        return f"{self.equipo1} vs {self.equipo2} ({self.tipo})"


# ------------------ RANKING ------------------

class ClasificacionLEC(models.Model):
    posicion = models.IntegerField()
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    split = models.ForeignKey(SplitLEC, on_delete=models.CASCADE, related_name='clasificacion')
    victorias = models.IntegerField(default=0)
    derrotas = models.IntegerField(default=0)

    class Meta:
        unique_together = ('equipo', 'split')
        ordering = ['-victorias']

    def __str__(self):
        return f"{self.equipo.nombre} en {self.split}"

    @property
    def registro(self):
        return f"{self.victorias}:{self.derrotas}"   

# ------------------ JUGADOR EN PARTIDO ------------------

class JugadorEnPartido(models.Model):
    # Representa la actuación de un jugador en un partido específico
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='jugadores_en_partido')
    campeon = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True)
    
    # Estadísticas
    kills = models.IntegerField()
    deaths = models.IntegerField()
    assists = models.IntegerField()
    cs = models.IntegerField()
    oro = models.IntegerField()
    damage_total = models.IntegerField()
    ward_colocados = models.IntegerField()
    nivel = models.IntegerField()
    damage_estructuras = models.IntegerField()

    @property
    def rol(self):
        return self.jugador.rol

    @property
    def resultado(self):
        if self.partido.ganador == self.jugador.equipo:
            return True
        return False

    def __str__(self):
        return f"{self.jugador.nickname} con {self.campeon.nombre} en {self.partido}"

# ------------------ LADOS, BANEOS Y PICKS ------------------

class LadoEquipoEnPartido(models.Model):
    # Relaciona el equipo con su lado en el mapa (Blue/Red) y orden de pickeo
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='lados')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='lados_en_partido')
    lado = models.CharField(max_length=10, choices=[('Blue', 'Blue'), ('Red', 'Red')])
    orden_pick = models.IntegerField()  # 1 o 2

    class Meta:
        unique_together = ('partido', 'equipo')

    def __str__(self):
        return f"{self.equipo.nombre} en {self.lado} ({self.partido})"


class Baneo(models.Model):
    # Campeones baneados por equipo en un partido
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='baneos')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    campeon = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True)
    orden = models.IntegerField()  # del 1 al 5
    lado = models.CharField(max_length=10, choices=[('Blue', 'Blue'), ('Red', 'Red')])


class Pick(models.Model):
    # Campeones seleccionados por cada jugador en un partido
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='picks')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    jugador = models.ForeignKey(Jugador, on_delete=models.SET_NULL, null=True)
    campeon = models.ForeignKey(Campeon, on_delete=models.SET_NULL, null=True)
    orden = models.IntegerField()
    lado = models.CharField(max_length=10, choices=[('Blue', 'Blue'), ('Red', 'Red')])


# ------------------ OBJETOS ------------------

class Objetos(models.Model):
    # Objetos comprables dentro del juego
    nombre = models.CharField(max_length=100)
    costo = models.IntegerField()
    imagen_url = models.URLField(blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class ObjetosComprados(models.Model):
    # Objetos comprados por un jugador durante el partido
    jugador_partido = models.ForeignKey(JugadorEnPartido, on_delete=models.CASCADE, related_name='objetos_comprados')
    objeto = models.ForeignKey(Objetos, on_delete=models.SET_NULL, null=True)
    minuto = models.IntegerField()
    orden_compra = models.IntegerField()


# ------------------ OBJETIVOS NEUTRALES ------------------

class ObjetivoNeutral(models.Model):
    TIPO_OBJETIVO = [
        ('Baron', 'Barón Nashor'),
        ('Dragon', 'Dragón'),
        ('Heraldo', 'Heraldo de la Grieta'),
        ('Torre', 'Torre'),
        ('Inhibidor', 'Inhibidor'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_OBJETIVO)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE)
    minuto = models.IntegerField()

class Dragon(ObjetivoNeutral):  # Hereda de ObjetivoNeutral
    TIPO_DRAGON = [
        ('Infernal', 'Infernal'),
        ('Oceano', 'Océano'),
        ('Nube', 'Nube'),
        ('Montaña', 'Montaña'),
        ('Hextech', 'Hextech'),
        ('Quimtech', 'Quimtech'),
        ('Anciano', 'Elder'),
    ]
    subtipo = models.CharField(max_length=20, choices=TIPO_DRAGON)


