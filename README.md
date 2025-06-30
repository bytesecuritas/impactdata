# ImpactData - Système de Gestion des Badges

Système de gestion des membres, organisations et badges avec génération de QR codes et export PDF.

## Fonctionnalités

- **Gestion des Adhérents** : Création, modification et suppression des membres
- **Gestion des Organisations** : Administration des organisations partenaires
- **Gestion des Badges** : Génération automatique de badges avec QR codes
- **Système de Rôles** : Admin, Superviseur, Agent avec permissions différenciées
- **Export PDF** : Téléchargement des badges en format PDF
- **Scan QR Code** : Vérification des badges via QR codes
- **Interface Responsive** : Design moderne et adaptatif

## Technologies Utilisées

- **Backend** : Django 4.2.7
- **Base de données** : PostgreSQL (production) / SQLite (développement)
- **Frontend** : Bootstrap 5, Font Awesome
- **Génération PDF** : ReportLab
- **QR Codes** : qrcode
- **Images** : Pillow

## Installation Locale

### Prérequis

- Python 3.11+
- pip
- virtualenv (recommandé)

### Étapes d'installation

1. **Cloner le repository**
   ```bash
   git clone <repository-url>
   cd impactdata
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos paramètres
   ```

5. **Effectuer les migrations**
   ```bash
   python manage.py migrate
   ```

6. **Créer un superutilisateur**
   ```bash
   python manage.py createsuperuser
   ```

7. **Lancer le serveur de développement**
   ```bash
   python manage.py runserver
   ```

8. **Accéder à l'application**
   - URL : http://127.0.0.1:8000/
   - Admin : http://127.0.0.1:8000/admin/

## Déploiement sur Render

### Configuration Automatique

Le projet est configuré pour un déploiement automatique sur Render avec les fichiers suivants :

- `render.yaml` : Configuration du service et de la base de données
- `build.sh` : Script de build pour Render
- `requirements.txt` : Dépendances Python

### Étapes de déploiement

1. **Connecter votre repository GitHub à Render**
   - Créer un compte sur [Render](https://render.com)
   - Connecter votre repository GitHub

2. **Déployer automatiquement**
   - Render détectera automatiquement le fichier `render.yaml`
   - Le service sera déployé avec une base de données PostgreSQL

3. **Variables d'environnement**
   Les variables suivantes sont automatiquement configurées :
   - `SECRET_KEY` : Généré automatiquement
   - `DEBUG` : Défini à `false` en production
   - `DATABASE_URL` : Connecté à la base PostgreSQL
   - `ALLOWED_HOSTS` : Configuré pour `.onrender.com`

### Configuration Manuelle (Alternative)

Si vous préférez configurer manuellement :

1. **Créer un nouveau Web Service**
   - Environment : Python
   - Build Command : `./build.sh`
   - Start Command : `gunicorn impactData.wsgi:application`

2. **Créer une base de données PostgreSQL**
   - Lier la base de données au service web

3. **Configurer les variables d'environnement**
   ```
   SECRET_KEY=votre-clé-secrète
   DEBUG=false
   DATABASE_URL=postgresql://...
   ALLOWED_HOSTS=.onrender.com
   ```

## Structure du Projet

```
impactdata/
├── core/                    # Application principale
│   ├── models.py           # Modèles de données
│   ├── views.py            # Vues et logique métier
│   ├── urls.py             # Configuration des URLs
│   ├── templates/          # Templates HTML
│   ├── static/             # Fichiers statiques (CSS, JS, images)
│   └── management/         # Commandes de gestion
├── impactData/             # Configuration Django
│   ├── settings.py         # Paramètres du projet
│   ├── urls.py             # URLs principales
│   └── wsgi.py             # Configuration WSGI
├── media/                  # Fichiers uploadés
├── staticfiles/            # Fichiers statiques collectés
├── requirements.txt        # Dépendances Python
├── build.sh               # Script de build pour Render
├── render.yaml            # Configuration Render
└── manage.py              # Script de gestion Django
```

## Rôles et Permissions

### Admin
- Accès complet à toutes les fonctionnalités
- Gestion des utilisateurs et organisations
- Configuration système

### Superviseur
- Gestion des adhérents et badges
- Génération et révoquation de badges
- Accès aux rapports

### Agent
- Consultation des adhérents
- Génération de badges
- Accès limité aux fonctionnalités

## Commandes de Gestion

```bash
# Nettoyer les doublons de badges
python manage.py clean_badge_duplicates

# Nettoyer la base de données
python manage.py clean_database

# Corriger les doublons d'adhérents
python manage.py fix_adherent_duplicates

# Lister les adhérents avec badges
python manage.py list_adherents_badge

# Tester la génération de badges
python manage.py test_badge_generation

# Collecter les fichiers statiques
python manage.py collectstatic

# Collecter les fichiers statiques (commande personnalisée)
python manage.py collect_static
```

## Support et Maintenance

Pour toute question ou problème :
1. Vérifier les logs dans le dashboard Render
2. Consulter la documentation Django
3. Contacter l'équipe de développement

## Licence

Ce projet est propriétaire et confidentiel.

