#!/usr/bin/env bash
# exit on error
set -o errexit

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances système nécessaires pour Pillow
# (Render les installe automatiquement)

# Installer les dépendances Python avec des versions compatibles
pip install Django==4.2.23
pip install Pillow==10.4.0
pip install qrcode==7.4.2
pip install reportlab==4.0.7
pip install gunicorn==21.2.0
pip install whitenoise==6.6.0
pip install dj-database-url==2.1.0
pip install psycopg2-binary==2.9.9
pip install python-decouple==3.8
pip install asgiref==3.7.2
pip install sqlparse==0.4.4
pip install tzdata==2023.3

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Effectuer les migrations
python manage.py migrate

# Créer un superutilisateur par défaut (seulement si aucun n'existe)
python manage.py create_default_admin 