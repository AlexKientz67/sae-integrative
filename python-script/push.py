import mysql.connector
from datetime import datetime

db = mysql.connector.connect(
    host="10.252.1.134",
    user="sae",
    password="password",
    database="sae"
)

cursor = db.cursor()

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

        # Vérifie si le capteur existe
        cursor.execute(
            "SELECT id FROM Capteur WHERE id=%s",
            (infos["Id"],)
        )

        if cursor.fetchone() is None:
            cursor.execute(
                """
                INSERT INTO Capteur
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

        timestamp = datetime.strptime(
            infos["date"] + " " + infos["time"],
            "%d/%m/%Y %H:%M:%S"
        )

        if topic.endswith("Maison1"):
            table = "MesureMaison1"
        else:
            table = "MesureMaison2"

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

# vide le cache
open("/opt/python/data.csv", "w").close()