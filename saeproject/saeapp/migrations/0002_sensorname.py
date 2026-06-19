from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("saeapp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SensorName",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("house_id", models.CharField(max_length=8)),
                ("capteur_Id", models.CharField(max_length=32)),
                ("display_name", models.CharField(max_length=80)),
            ],
        ),
        migrations.AddConstraint(
            model_name="sensorname",
            constraint=models.UniqueConstraint(
                fields=("house_id", "capteur_Id"),
                name="unique_sensor_name_by_house",
            ),
        ),
    ]
