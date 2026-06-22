from django.test import SimpleTestCase

from .forms import CapteurForm
from .models import Capteur, MesureMaison1, MesureMaison2


class DatabaseSchemaTests(SimpleTestCase):
    def test_table_names(self):
        self.assertEqual(Capteur._meta.db_table, "capteurs")
        self.assertEqual(MesureMaison1._meta.db_table, "mesures_maison1")
        self.assertEqual(MesureMaison2._meta.db_table, "mesures_maison2")

    def test_capteur_form_fields(self):
        self.assertEqual(
            list(CapteurForm().fields),
            ["id", "nom", "piece", "emplacement"],
        )
