import mysql.connector
from datetime import datetime

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="nom_de_ta_base"
)

cursor = db.cursor()

with open("/opt/python/nrw/data.csv", "r") as f:
    lignes = f.readlines()

for ligne in lignes:

    if ligne.strip() == "":
        continue

    topic, message = ligne.strip().split(";", 1)

    temp = message.split(",temp=")

    infos = {}

    for champ in temp[0].split(","):
        cle, valeur = champ.split("=")
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

db.commit()

cursor.close()
db.close()

# vide le cache
open("/opt/python/nrw/data.csv", "w").close()