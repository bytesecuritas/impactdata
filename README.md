# Platforme impact Data

##Procéssus d'installation:

#### Cloné le projet:
https://github.com/bytesecuritas/impactdata.git

#### Créer un environnement virtuel:
python -m venv venv

#### Avtiver l'environnement virtuel:
venv\Scripts\activate

#### Se déplacer dans le dossier du proje
cd impacData

#### Installer les dépendances:
pip freeze > requirements.txt

### Crée le fichier .env:
mettez y les informations de connexion à la base de donnée selons les variables 
situez dans le fichier settings.py

#### Effectuez les migrations: (Sans oublier)
python manage.py makemigrations
python manage.py migrate

#### Lancé le serveur:
python manage.py runserver

