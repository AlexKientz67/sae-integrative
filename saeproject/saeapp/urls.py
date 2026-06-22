from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("index", views.index, name="index_legacy"),
    path("capteurs/", views.liste_capteurs, name="capteurs"),
    path("capteurs/ajouter/", views.ajouter_capteur, name="ajouter_capteur"),
    path(
        "capteurs/<str:capteur_id>/modifier/",
        views.modifier_capteur,
        name="modifier_capteur",
    ),
    path(
        "capteurs/<str:capteur_id>/supprimer/",
        views.supprimer_capteur,
        name="supprimer_capteur",
    ),
    path("export.csv", views.exporter_csv, name="export_csv"),
]
