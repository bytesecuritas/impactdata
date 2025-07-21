# Impact Data - Système de Gestion des Adhérents

## 📋 Description
Système de gestion des adhérents, organisations et interactions avec gestion des rôles et objectifs. Application Django complète avec système de badges, QR codes, et gestion des permissions dynamiques.

## 🚀 Installation Complète

### Prérequis Système

#### Windows
```bash
# Installer Python 3.8+ depuis python.org
# Installer Git depuis git-scm.com
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

#### macOS
```bash
# Installer Homebrew si pas déjà fait
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer Python et Git
brew install python git
```

### 1. Clonage du Projet

```bash
# Cloner le repository
git clone <URL_DU_REPO>
cd impactData

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 2. Installation des Dépendances

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Pour la production avec MySQL (décommenter dans requirements.txt)
# pip install mysqlclient==2.2.7
```

### 3. Configuration de l'Environnement

#### Créer le fichier .env
```bash
# Copier le fichier d'exemple
cp email_config_example.txt .env
```

#### Configurer les variables d'environnement dans .env
```bash
# Clé secrète Django (générer une nouvelle clé)
SECRET_KEY=votre_cle_secrete_tres_longue_et_complexe

# Configuration Email (obligatoire pour les notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_SSL=True
EMAIL_HOST_USER=votre_email@gmail.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_application
DEFAULT_FROM_EMAIL=votre_email@gmail.com

# Configuration MySQL (optionnel - pour la production)
# DB_NAME=impact_data
# DB_USER=root
# DB_PASSWORD=votre_mot_de_passe
# DB_HOST=localhost
# DB_PORT=3306
```

#### Générer une clé secrète Django
```bash
# Dans l'environnement Python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Configuration de la Base de Données

#### Option A : SQLite (Développement)
```bash
# Aucune configuration supplémentaire nécessaire
# La base SQLite sera créée automatiquement
```

#### Option B : MySQL (Production)
```bash
# 1. Installer MySQL
# Windows : Télécharger depuis mysql.com
# Linux : sudo apt install mysql-server
# macOS : brew install mysql

# 2. Créer la base de données
mysql -u root -p
CREATE DATABASE impact_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'impact_user'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON impact_data.* TO 'impact_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 3. Modifier settings.py pour utiliser MySQL
# Décommenter la section DATABASES MySQL et commenter SQLite
```

### 5. Initialisation de la Base de Données

```bash
# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur administrateur
python manage.py createsuperuser
# Suivre les instructions pour créer le premier administrateur
```

### 6. Initialisation des Données de Référence

#### Initialiser les valeurs de référence (obligatoire)
```bash
# Cette commande crée toutes les valeurs de référence nécessaires
python manage.py initialize_reference_values
```

**Valeurs initialisées :**
- Statuts d'interaction (En cours, Terminé, Annulé)
- Statuts de badge (Actif, Expiré, Révoqué)
- Statuts d'objectif (En attente, En cours, Terminé, Échoué)
- Rôles utilisateur (Administrateur, Superviseur, Agent)
- Types d'adhérent (Personne Physique, Personne Morale)
- Types de profession (Médecin, Infirmier, Enseignant, etc.)
- Types de téléphone et d'urgence
- Types d'informations médicales et de formation
- Types de distinction et de langue
- Types d'activité
- Catégories d'organisation

#### Initialiser les permissions par défaut (obligatoire)
```bash
# Cette commande configure les permissions pour tous les rôles
python manage.py initialize_permissions
```

**Permissions configurées :**
- **Administrateur** : Accès complet à toutes les fonctionnalités
- **Superviseur** : Gestion des agents et des données
- **Agent** : Saisie et consultation des données

### 7. Test de l'Installation

#### Tester l'envoi d'emails
```bash
# Tester la configuration email
python manage.py test_email
```

#### Tester la génération de badges
```bash
# Tester la génération de badges et QR codes
python manage.py test_badge_generation
```

### 8. Lancement de l'Application

#### Mode Développement
```bash
# Lancer le serveur de développement
python manage.py runserver

# L'application sera accessible sur http://127.0.0.1:8000
```

#### Mode Production
```bash
# Collecter les fichiers statiques
python manage.py collectstatic

# Lancer avec Gunicorn
gunicorn impactData.wsgi:application --bind 0.0.0.0:8000
```

### 9. Configuration Post-Installation

#### Créer les premiers utilisateurs
1. Se connecter avec le superutilisateur créé
2. Aller dans l'interface d'administration
3. Créer des utilisateurs avec différents rôles :
   - **Administrateur** : Accès complet
   - **Superviseur** : Gestion des agents
   - **Agent** : Saisie des données

#### Configurer les paramètres généraux
1. Aller dans **Paramètres > Paramètres Généraux**
2. Configurer les informations de l'organisation
3. Ajuster les paramètres de sécurité
4. Configurer les paramètres d'interface

### 10. Commandes de Maintenance

#### Nettoyage de la base de données
```bash
# Nettoyer les doublons de badges
python manage.py clean_badge_duplicates

# Nettoyer les doublons d'adhérents
python manage.py fix_adherent_duplicates

# Nettoyer complètement la base de données
python manage.py clean_database
```

#### Mise à jour des données
```bash
# Mettre à jour les objectifs
python manage.py update_objectives

# Mettre à jour les informations de badges
python manage.py update_badge_info

# Mettre à jour les badges existants
python manage.py update_existing_adherents_badge_info
```

#### Réparation des problèmes
```bash
# Corriger les problèmes de badges
python manage.py fix_badge_issues

# Lister les adhérents avec badges
python manage.py list_adherents_badge
```

## 🔧 Configuration Avancée

### Configuration Email Gmail
1. Activer l'authentification à 2 facteurs sur votre compte Gmail
2. Générer un mot de passe d'application :
   - Aller dans **Paramètres Google > Sécurité**
   - **Connexion à Google > Mots de passe d'application**
   - Générer un mot de passe pour "Impact Data"
3. Utiliser ce mot de passe dans `EMAIL_HOST_PASSWORD`

### Configuration MySQL pour Production
1. Modifier `settings.py` :
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', cast=int),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'use_unicode': True,
        },
    }
}
```

2. Installer le client MySQL :
```bash
pip install mysqlclient==2.2.7
```

### Configuration de Sécurité Production
1. Modifier `settings.py` :
```python
DEBUG = False
ALLOWED_HOSTS = ['votre-domaine.com', 'www.votre-domaine.com']
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

2. Configurer HTTPS avec un certificat SSL

## 📁 Structure du Projet

```
impactData/
├── core/                          # Application principale
│   ├── management/commands/       # Commandes personnalisées
│   ├── migrations/               # Migrations de base de données
│   ├── static/                   # Fichiers statiques
│   ├── templates/                # Templates HTML
│   ├── models.py                 # Modèles de données
│   ├── views.py                  # Vues de l'application
│   └── forms.py                  # Formulaires
├── impactData/                   # Configuration du projet
│   ├── settings.py              # Paramètres Django
│   ├── urls.py                  # URLs principales
│   └── wsgi.py                  # Configuration WSGI
├── media/                        # Fichiers uploadés
├── requirements.txt              # Dépendances Python
├── manage.py                     # Script de gestion Django
└── .env                          # Variables d'environnement
```

## 🚨 Dépannage

### Erreurs Courantes

#### Erreur de migration
```bash
# Réinitialiser les migrations si nécessaire
python manage.py migrate --fake-initial
```

#### Erreur de permissions
```bash
# Réinitialiser les permissions
python manage.py initialize_permissions --force
```

#### Erreur d'email
```bash
# Vérifier la configuration dans .env
# Tester avec la commande
python manage.py test_email
```

#### Erreur de base de données
```bash
# Vérifier la connexion MySQL
mysql -u impact_user -p impact_data

# Vérifier les paramètres dans .env
```

## 📞 Support

Pour toute question ou problème :
1. Vérifier les logs Django
2. Consulter la documentation Django
3. Contacter l'équipe de développement

## 🔄 Mise à Jour

```bash
# Mettre à jour le code
git pull origin main

# Mettre à jour les dépendances
pip install -r requirements.txt

# Appliquer les nouvelles migrations
python manage.py migrate

# Redémarrer l'application
```

---

**Impact Data** - Système de gestion des adhérents et organisations

