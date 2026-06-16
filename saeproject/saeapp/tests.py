from django.urls import reverse

from django.test import TestCase

from .models import TemperatureDataM1, TemperatureDataM2


class TemperatureDashboardTests(TestCase):
    def setUp(self):
        TemperatureDataM1.objects.create(
            capteur_Id="M1-S1",
            piece="Salon",
            date="2026-06-15",
            heure="08:00",
            temp=20.5,
        )
        TemperatureDataM2.objects.create(
            capteur_Id="M2-S1",
            piece="Cuisine",
            date="2026-06-15",
            heure="09:00",
            temp=22.0,
        )

    def test_dashboard_displays_both_houses_by_default(self):
        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maison 1")
        self.assertContains(response, "M1-S1")
        self.assertContains(response, "Maison 2")
        self.assertContains(response, "M2-S1")
        self.assertEqual(response.context["total_count"], 2)

    def test_dashboard_can_filter_house(self):
        response = self.client.get(reverse("index"), {"house": "2"})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "M1-S1")
        self.assertContains(response, "M2-S1")
        self.assertEqual(response.context["total_count"], 1)

    def test_csv_export_includes_house_column(self):
        response = self.client.get(reverse("export_csv"))
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn("maison,capteur,piece,date,heure,temperature", content)
        self.assertIn("Maison 1,M1-S1,Salon,2026-06-15,08:00,20.5", content)
        self.assertIn("Maison 2,M2-S1,Cuisine,2026-06-15,09:00,22.0", content)
