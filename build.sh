#!/usr/bin/env bash
# exit on error
set -o errexit

# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances système nécessaires
# (Render les installe automatiquement, mais c'est une bonne pratique)

# Installer les dépendances Python
pip install -r requirements.txt

# Collecter les fichiers statiques
python manage.py collectstatic --no-input

# Effectuer les migrations
python manage.py migrate 