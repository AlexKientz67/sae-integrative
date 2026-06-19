from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index', views.index, name='index_legacy'),
    path('capteurs/renommer', views.rename_sensor, name='rename_sensor'),
    path('export.csv', views.export_csv, name='export_csv'),
]
