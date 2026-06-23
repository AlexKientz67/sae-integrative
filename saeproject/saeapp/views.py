import csv

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .donnees import MAISONS, calculer_moyennes, convertir_date, filtrer_mesures
from .forms import CapteurForm
from .models import Capteur, MesureMaison1, MesureMaison2


def preparer_graphique(mesures):
    couleurs = [
        "#005bbb",
        "#d33f49",
        "#228b22",
        "#e67e22",
        "#7b2cbf",
        "#008b8b",
        "#c2185b",
        "#6b4f2c",
    ]
    groupes = {}
    datasets = []

    for mesure in reversed(mesures):
        nom = mesure["maison"] + " - " + mesure["nom_affiche"]

        if nom not in groupes:
            groupes[nom] = []

        groupes[nom].append(
            {
                "x": mesure["date"] + " " + mesure["heure"],
                "y": mesure["temperature"],
            }
        )

    numero = 0

    for nom, valeurs in groupes.items():
        couleur = couleurs[numero % len(couleurs)]

        datasets.append(
            {
                "label": nom,
                "data": valeurs,
                "borderColor": couleur,
                "backgroundColor": couleur,
                "tension": 0.2,
            }
        )

        numero += 1

    return {"datasets": datasets}


def index(request):
    mesures = filtrer_mesures(request)
    moyennes = calculer_moyennes(mesures)

    moyenne_globale = None
    if mesures:
        total = sum(mesure["temperature"] for mesure in mesures)
        moyenne_globale = round(total / len(mesures), 1)

    secondes = request.GET.get("refresh", "30")
    if not secondes.isdigit():
        secondes = "30"

    date_debut = convertir_date(request.GET.get("start", ""))
    date_fin = convertir_date(request.GET.get("end", ""))

    contexte = {
        "mesures": mesures,
        "moyennes": moyennes,
        "moyenne_globale": moyenne_globale,
        "maisons": MAISONS,
        "filtre_maison": request.GET.get("house", "").strip(),
        "filtre_capteur": request.GET.get("sensor", "").strip(),
        "filtre_debut": date_debut.isoformat() if date_debut else "",
        "filtre_fin": date_fin.isoformat() if date_fin else "",
        "actualisation_auto": request.GET.get("auto_refresh") == "on",
        "secondes": secondes,
        "nombre_mesures": len(mesures),
        "graphique": preparer_graphique(mesures),
    }

    return render(request, "saeapp/index.html", contexte)


def liste_capteurs(request):
    capteurs = Capteur.objects.all().order_by("nom")
    return render(request, "saeapp/capteurs.html", {"capteurs": capteurs})


def ajouter_capteur(request):
    form = CapteurForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect("capteurs")

    return render(request, "saeapp/capteur_form.html", {"form": form})


def modifier_capteur(request, capteur_id):
    capteur = get_object_or_404(Capteur, id=capteur_id)
    form = CapteurForm(request.POST or None, instance=capteur)
    form.fields["id"].disabled = True

    if form.is_valid():
        form.save()
        return redirect("capteurs")

    return render(request, "saeapp/capteur_form.html", {"form": form})


def supprimer_capteur(request, capteur_id):
    capteur = get_object_or_404(Capteur, id=capteur_id)

    if request.method == "POST":
        MesureMaison1.objects.filter(capteur=capteur).delete()
        MesureMaison2.objects.filter(capteur=capteur).delete()
        capteur.delete()

    return redirect("capteurs")


def exporter_csv(request):
    mesures = filtrer_mesures(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="temperatures.csv"'

    writer = csv.writer(response)
    writer.writerow(
        [
            "maison",
            "capteur",
            "nom",
            "piece",
            "emplacement",
            "date",
            "heure",
            "temperature",
        ]
    )

    for mesure in mesures:
        writer.writerow(
            [
                mesure["maison"],
                mesure["capteur_id"],
                mesure["nom_affiche"],
                mesure["piece"],
                mesure["emplacement"],
                mesure["date"],
                mesure["heure"],
                mesure["temperature"],
            ]
        )

    return response
