from django.db import models


class Capteur(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    nom = models.CharField(max_length=50, unique=True)
    piece = models.CharField(max_length=50)
    emplacement = models.CharField(max_length=100)
    def __str__(self):
        return self.nom


class MesureMaison1(models.Model):
    id = models.AutoField(primary_key=True)
    capteur = models.ForeignKey(Capteur, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField()
    temperature = models.FloatField()

class MesureMaison2(models.Model):
    id = models.AutoField(primary_key=True)
    capteur = models.ForeignKey(Capteur, on_delete=models.DO_NOTHING)
    timestamp = models.DateTimeField()
    temperature = models.FloatField()