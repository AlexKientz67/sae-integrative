from django.db import models

class TemperatureDataM1(models.Model):
    id = models.AutoField(primary_key=True)
    capteur_Id = models.CharField(max_length=32)
    piece = models.CharField(max_length=80)
    date = models.CharField(max_length=20)
    heure = models.CharField(max_length=20)
    temp = models.FloatField()

class TemperatureDataM2(models.Model):
    id = models.AutoField(primary_key=True)
    capteur_Id = models.CharField(max_length=32)
    piece = models.CharField(max_length=80)
    date = models.CharField(max_length=20)
    heure = models.CharField(max_length=20)
    temp = models.FloatField()
