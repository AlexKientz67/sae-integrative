from datetime import datetime

from django.db import DatabaseError

from .models import MesureMaison1, MesureMaison2


MAISONS = [
    {"id": "1", "nom": "Maison 1"},
    {"id": "2", "nom": "Maison 2"},
]


def convertir_date(texte):
    if not texte:
        return None

    try:
        return datetime.strptime(texte, "%Y-%m-%d").date()
    except ValueError:
        return None


def charger_une_maison(modele, maison_id, maison_nom):
    mesures = []

    try:
        donnees = modele.objects.select_related("capteur").all()

        for donnee in donnees:
            mesures.append(
                {
                    "maison_id": maison_id,
                    "maison": maison_nom,
                    "capteur_id": donnee.capteur.id,
                    "nom_affiche": donnee.capteur.nom,
                    "piece": donnee.capteur.piece,
                    "emplacement": donnee.capteur.emplacement,
                    "timestamp": donnee.timestamp,
                    "date": donnee.timestamp.strftime("%Y-%m-%d"),
                    "heure": donnee.timestamp.strftime("%H:%M:%S"),
                    "temperature": donnee.temperature,
                }
            )
    except DatabaseError:
        pass

    return mesures


def charger_mesures(maison=""):
    mesures = []

    if maison == "" or maison == "1":
        mesures += charger_une_maison(MesureMaison1, "1", "Maison 1")

    if maison == "" or maison == "2":
        mesures += charger_une_maison(MesureMaison2, "2", "Maison 2")

    return mesures


def filtrer_mesures(request):
    maison = request.GET.get("house", "").strip()
    recherche = request.GET.get("sensor", "").strip().lower()
    date_debut = convertir_date(request.GET.get("start", ""))
    date_fin = convertir_date(request.GET.get("end", ""))
    resultat = []

    for mesure in charger_mesures(maison):
        texte = (
            mesure["capteur_id"]
            + mesure["nom_affiche"]
            + mesure["piece"]
            + mesure["emplacement"]
        ).lower()
        date_mesure = mesure["timestamp"].date()

        if recherche and recherche not in texte:
            continue
        if date_debut and date_mesure < date_debut:
            continue
        if date_fin and date_mesure > date_fin:
            continue

        resultat.append(mesure)

    resultat.sort(key=lambda mesure: mesure["timestamp"], reverse=True)
    return resultat


def calculer_moyennes(mesures):
    groupes = {}

    for mesure in mesures:
        cle = (mesure["maison_id"], mesure["capteur_id"])

        if cle not in groupes:
            groupes[cle] = {
                "maison": mesure["maison"],
                "capteur": mesure["capteur_id"],
                "nom_affiche": mesure["nom_affiche"],
                "total": 0,
                "nombre": 0,
            }

        groupes[cle]["total"] += mesure["temperature"]
        groupes[cle]["nombre"] += 1

    moyennes = []

    for groupe in groupes.values():
        groupe["moyenne"] = round(groupe["total"] / groupe["nombre"], 1)
        moyennes.append(groupe)

    return moyennes
