# Fonctionnement de l'application

## 1. Vue d'ensemble

Cette application Django affiche les températures de deux maisons et permet de gérer les capteurs.

Le chemin suivi par une requête est :

```text
Navigateur -> Apache2 -> Gunicorn -> Django -> MySQL
                    |
                    -> fichiers statiques
```

- Apache2 reçoit les requêtes HTTP sur le port 80.
- Apache2 sert directement les fichiers présents dans `staticfiles/`.
- Les autres requêtes sont envoyées à Gunicorn.
- Gunicorn exécute l'application Django.
- Django lit et modifie les données dans MySQL.

## 2. Organisation du projet

```text
saeproject/
├── manage.py
├── saeproject/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── saeapp/
    ├── donnees.py
    ├── forms.py
    ├── models.py
    ├── urls.py
    ├── views.py
    ├── static/saeapp/style.css
    └── templates/saeapp/
        ├── index.html
        ├── capteurs.html
        └── capteur_form.html
```

### Rôle des fichiers

- `models.py` décrit les capteurs et les mesures des deux maisons.
- `forms.py` contient le formulaire Django utilisé pour ajouter et modifier un capteur.
- `donnees.py` charge les mesures, applique les filtres et calcule les moyennes.
- `views.py` contient les pages de l'application et l'export CSV.
- `urls.py` associe chaque adresse à une vue.
- `templates/` contient les pages HTML.
- `static/saeapp/style.css` contient le CSS commun aux pages.

## 3. Base de données

La base MySQL contient trois tables logiques :

```text
capteurs
├── id
├── nom
├── piece
└── emplacement

mesures_maison1              mesures_maison2
├── id                       ├── id
├── capteur_id               ├── capteur_id
├── timestamp                ├── timestamp
└── temperature              └── temperature
```

`capteur_id` relie une mesure au capteur correspondant dans la table `capteurs`.

Attention : sans option `db_table` dans les modèles, Django utilise par défaut les noms `saeapp_capteur`, `saeapp_mesuremaison1` et `saeapp_mesuremaison2`. Si les tables MySQL portent exactement les noms du SQL ci-dessus, les modèles doivent contenir :

```python
class Meta:
    db_table = "capteurs"
```

Le même principe s'applique aux deux tables de mesures.

## 4. Page principale

La page principale est accessible à l'adresse :

```text
http://10.252.1.135/app/
```

La vue `index` appelle `filtrer_mesures()` dans `donnees.py`.

Cette fonction :

1. charge les mesures de la maison 1 et/ou de la maison 2 ;
2. récupère les informations du capteur avec `select_related("capteur")` ;
3. applique les filtres de maison, capteur et dates ;
4. trie toutes les mesures de la plus récente à la plus ancienne ;
5. renvoie toutes les mesures, sans limite de 25 lignes.

La page affiche ensuite :

- le nombre de mesures ;
- la moyenne globale ;
- un graphique avec une couleur par capteur ;
- toutes les mesures dans un tableau ;
- la moyenne de chaque capteur.

L'actualisation automatique recharge la page après le nombre de secondes choisi.

## 5. Explication détaillée de `views.py`

### À quoi sert une vue Django ?

Une vue est une fonction Python qui reçoit une requête HTTP dans la variable `request` et renvoie une réponse HTTP.

Exemple minimal :

```python
def index(request):
    return render(request, "saeapp/index.html")
```

Dans cette application, `views.py` relie les éléments suivants :

```text
URL -> vue Python -> modèle ou fonction de données -> template HTML
```

### Les imports

```python
import csv

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
```

- `csv` sert à fabriquer le fichier CSV.
- `HttpResponse` permet de renvoyer autre chose qu'une page HTML.
- `render` envoie des données à un template HTML.
- `redirect` redirige le navigateur vers une autre page.
- `get_object_or_404` cherche un objet dans la base. Si l'objet n'existe pas, Django renvoie automatiquement une erreur 404.

Les imports propres à l'application sont :

```python
from .donnees import MAISONS, calculer_moyennes, convertir_date, filtrer_mesures
from .forms import CapteurForm
from .models import Capteur, MesureMaison1, MesureMaison2
```

- `donnees.py` s'occupe de la lecture et des calculs sur les températures.
- `CapteurForm` construit le formulaire du CRUD.
- les trois modèles permettent de lire ou modifier les tables MySQL.

### Vue `index`

La vue `index` affiche le tableau de bord.

```python
mesures = filtrer_mesures(request)
moyennes = calculer_moyennes(mesures)
```

La première ligne récupère les mesures qui correspondent aux filtres présents dans l'URL. La deuxième calcule les moyennes à partir de ces mesures filtrées.

La moyenne globale est calculée seulement si la liste contient au moins une mesure :

```python
moyenne_globale = None

if mesures:
    total = sum(mesure["temperature"] for mesure in mesures)
    moyenne_globale = round(total / len(mesures), 1)
```

- `sum()` additionne toutes les températures.
- `len(mesures)` donne le nombre de mesures.
- `round(..., 1)` conserve un chiffre après la virgule.
- si aucune mesure n'existe, la valeur reste `None` et la page affiche `aucune`.

La durée d'actualisation vient d'un paramètre GET :

```python
secondes = request.GET.get("refresh", "30")

if not secondes.isdigit():
    secondes = "30"
```

`request.GET` contient les valeurs présentes après le `?` dans une URL. Par exemple :

```text
/app/?house=1&refresh=10
```

Ici, `house` vaut `1` et `refresh` vaut `10`. Si `refresh` n'est pas un nombre, la vue reprend la valeur par défaut de 30 secondes.

Les valeurs envoyées au template sont rangées dans le dictionnaire `contexte` :

```python
contexte = {
    "mesures": mesures,
    "moyennes": moyennes,
    "moyenne_globale": moyenne_globale,
    "maisons": MAISONS,
    "nombre_mesures": len(mesures),
}
```

Chaque clé devient une variable utilisable dans `index.html`. Par exemple :

```django
{{ nombre_mesures }}
```

La dernière ligne de la vue fabrique la page HTML :

```python
return render(request, "saeapp/index.html", contexte)
```

### Vue `liste_capteurs`

```python
def liste_capteurs(request):
    capteurs = Capteur.objects.all().order_by("nom")
    return render(request, "saeapp/capteurs.html", {"capteurs": capteurs})
```

- `Capteur.objects.all()` récupère tous les capteurs.
- `order_by("nom")` les trie par nom.
- la liste est envoyée au template `capteurs.html`.

Cette vue correspond à la partie « Read » du CRUD.

### Vue `ajouter_capteur`

```python
def ajouter_capteur(request):
    form = CapteurForm(request.POST or None)

    if form.is_valid():
        form.save()
        return redirect("capteurs")

    return render(request, "saeapp/capteur_form.html", {"form": form})
```

Cette vue fonctionne de deux façons :

- avec une requête GET, `request.POST` est vide et Django affiche un formulaire vide ;
- avec une requête POST, le formulaire reçoit les valeurs saisies par l'utilisateur.

`form.is_valid()` vérifie les champs. Si les valeurs sont valides, `form.save()` ajoute le capteur dans la base. `redirect("capteurs")` retourne ensuite à la liste.

Cette vue correspond à la partie « Create » du CRUD.

### Vue `modifier_capteur`

```python
capteur = get_object_or_404(Capteur, id=capteur_id)
form = CapteurForm(request.POST or None, instance=capteur)
form.fields["id"].disabled = True
```

- `capteur_id` vient de l'adresse de la page.
- `get_object_or_404` cherche le capteur correspondant.
- `instance=capteur` indique au formulaire qu'il faut modifier cet objet au lieu d'en créer un nouveau.
- le champ `id` est désactivé car il s'agit de la clé primaire du capteur.

Après validation, `form.save()` exécute la modification puis la vue redirige vers la liste.

Cette vue correspond à la partie « Update » du CRUD.

### Vue `supprimer_capteur`

```python
def supprimer_capteur(request, capteur_id):
    capteur = get_object_or_404(Capteur, id=capteur_id)

    if request.method == "POST":
        MesureMaison1.objects.filter(capteur=capteur).delete()
        MesureMaison2.objects.filter(capteur=capteur).delete()
        capteur.delete()

    return redirect("capteurs")
```

La suppression est exécutée uniquement avec une requête POST. Cela évite qu'un simple clic sur une URL ou qu'un robot supprime une donnée.

Les mesures liées au capteur sont supprimées avant le capteur. Cette étape est nécessaire à cause des clés étrangères de la base.

Cette vue correspond à la partie « Delete » du CRUD.

Attention : cette suppression efface définitivement le capteur et toutes ses mesures dans les deux maisons.

### Vue `exporter_csv`

La vue commence par reprendre les mêmes filtres que la page principale :

```python
mesures = filtrer_mesures(request)
```

Elle prépare ensuite une réponse qui sera téléchargée par le navigateur :

```python
response = HttpResponse(content_type="text/csv; charset=utf-8")
response["Content-Disposition"] = 'attachment; filename="temperatures.csv"'
writer = csv.writer(response)
```

- `content_type` indique qu'il s'agit d'un CSV.
- `Content-Disposition` demande au navigateur de télécharger le résultat.
- `csv.writer` écrit les lignes directement dans la réponse Django.

La première ligne contient les titres des colonnes. Une boucle ajoute ensuite une ligne pour chaque mesure :

```python
for mesure in mesures:
    writer.writerow([
        mesure["maison"],
        mesure["capteur_id"],
        mesure["nom_affiche"],
        mesure["temperature"],
    ])
```

La vue termine avec :

```python
return response
```

Contrairement à `render`, cette réponse ne contient pas une page HTML : elle contient directement le fichier CSV.

### Différence entre GET et POST

| Méthode | Utilisation dans l'application |
|---|---|
| GET | afficher une page et filtrer les mesures |
| POST | ajouter, modifier ou supprimer un capteur |

Les filtres utilisent GET afin de rester visibles dans l'adresse. Les modifications utilisent POST car elles changent la base de données.

## 6. CRUD des capteurs

CRUD signifie créer, lire, modifier et supprimer.

| Action | Adresse | Vue Django |
|---|---|---|
| Liste | `/app/capteurs/` | `liste_capteurs` |
| Ajout | `/app/capteurs/ajouter/` | `ajouter_capteur` |
| Modification | `/app/capteurs/<id>/modifier/` | `modifier_capteur` |
| Suppression | `/app/capteurs/<id>/supprimer/` | `supprimer_capteur` |

Le formulaire est construit par `CapteurForm` à partir du modèle `Capteur`.

Lors de la suppression d'un capteur, l'application supprime d'abord ses mesures dans les deux maisons, puis supprime le capteur.

## 7. Export CSV

L'adresse suivante télécharge les mesures :

```text
/app/export.csv
```

Les filtres présents dans l'adresse sont réutilisés. Le fichier contient la maison, le capteur, son nom, sa pièce, son emplacement, la date, l'heure et la température.

## 8. Fichiers statiques

Le CSS source se trouve ici :

```text
saeapp/static/saeapp/style.css
```

En production, Gunicorn ne sert pas ce fichier. La commande suivante copie tous les fichiers statiques vers `STATIC_ROOT` :

```bash
cd /opt/sae-integrative/saeproject
python3 manage.py collectstatic --noinput
```

Avec cette configuration Django :

```python
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
```

le fichier final est copié ici :

```text
/opt/sae-integrative/saeproject/staticfiles/saeapp/style.css
```

Il doit être accessible avec cette URL :

```text
http://10.252.1.135/static/saeapp/style.css
```

## 9. Configuration Apache2 pour `/static/`

Le 404 sur `/static/saeapp/style.css` signifie généralement qu'Apache2 envoie la requête à Gunicorn au lieu de lire le dossier `staticfiles`.

Exemple de configuration du site Apache2 :

```apache
<VirtualHost *:80>
    ServerName 10.252.1.135

    Alias /static/ /opt/sae-integrative/saeproject/staticfiles/

    <Directory /opt/sae-integrative/saeproject/staticfiles/>
        Require all granted
    </Directory>

    ProxyPreserveHost On
    ProxyPass /static/ !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

`ProxyPass /static/ !` est important : cette ligne empêche Apache2 d'envoyer les fichiers statiques à Gunicorn.

Activer les modules puis recharger Apache2 :

```bash
sudo a2enmod proxy proxy_http
sudo apache2ctl configtest
sudo systemctl reload apache2
```

Vérifier également les droits de lecture :

```bash
sudo chmod -R a+rX /opt/sae-integrative/saeproject/staticfiles
```

## 10. Gunicorn

Gunicorn doit lancer le module WSGI du projet depuis le dossier qui contient `manage.py` :

```bash
cd /opt/sae-integrative/saeproject
gunicorn --bind 127.0.0.1:8000 saeproject.wsgi:application
```

Gunicorn traite uniquement les pages Django. Les fichiers `/static/` restent servis par Apache2.

## 11. Mise à jour de l'application

Après une modification du code :

```bash
cd /opt/sae-integrative/saeproject
python3 manage.py check
python3 manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo apache2ctl configtest
sudo systemctl reload apache2
```

Pour vérifier le CSS :

```bash
curl -I http://10.252.1.135/static/saeapp/style.css
```

Une réponse correcte doit contenir un statut HTTP `200 OK`.

## 12. Points de production à vérifier

Dans `settings.py` :

- ajouter `10.252.1.135` dans `ALLOWED_HOSTS` ;
- utiliser `DEBUG = False` en production ;
- ne pas conserver le mot de passe MySQL et la clé secrète directement dans Git ;
- vérifier que le service Gunicorn redémarre automatiquement après un redémarrage du serveur.
