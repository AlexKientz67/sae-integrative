import mysql.connector
from datetime import datetime

db = mysql.connector.connect(
    host="10.252.1.134",
    user="sae",
    password="password",
    database="sae"
)

cursor = db.cursor()

# Cache des capteurs déjà vérifiés
capteurs_connus = []

with open("/opt/python/data.csv", "r") as f:
    lignes = f.readlines()

for ligne in lignes:

    if ligne.strip() == "":
        continue

    try:
        topic, message = ligne.strip().split(";", 1)

        temp = message.split(",temp=")

        infos = {}

        for champ in temp[0].split(","):
            cle, valeur = champ.split("=", 1)
            infos[cle] = valeur

        # Vérifie le capteur seulement la première fois
        if infos["Id"] not in capteurs_connus:

            cursor.execute(
                "SELECT id FROM saeapp_Capteur WHERE id=%s",
                (infos["Id"],)
            )

            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO saeapp_Capteur
                    (id, nom, piece, emplacement)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (
                        infos["Id"],
                        "Capteur_" + infos["Id"],
                        infos["piece"],
                        ""
                    )
                )

            capteurs_connus.append(infos["Id"])

        timestamp = datetime.strptime(
            infos["date"] + " " + infos["time"],
            "%d/%m/%Y %H:%M:%S"
        )

        if topic.endswith("Maison1"):
            table = "saeapp_MesureMaison1"
        else:
            table = "saeapp_MesureMaison2"

        cursor.execute(
            f"""
            INSERT INTO {table}
            (capteur_id, timestamp, temperature)
            VALUES (%s,%s,%s)
            """,
            (
                infos["Id"],
                timestamp,
                float(temp[1])
            )
        )

    except (KeyError, ValueError, IndexError) as e:
        print(f"[ERREUR] Ligne ignorée : {ligne.strip()}")
        print(f"         Cause : {e}")
        continue

db.commit()

cursor.close()
db.close()

# Vide le fichier CSV
open("/opt/python/data.csv", "w").close()