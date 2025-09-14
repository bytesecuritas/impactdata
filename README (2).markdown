# DEPLOIEMENT_OVH_IMPACTDATA

# 🚀 Déploiement ImpactData sur VPS OVH - Guide Complet

## 📋 Introduction

Ce guide explique comment déployer le projet **ImpactData** (système de gestion des adhérents avec badges et QR codes) sur un VPS OVH en utilisant PuTTY sous Windows. Le projet Django nécessite une configuration spécifique pour gérer 10 000+ adhérents avec génération de badges et système de permissions dynamiques.

**Spécificités ImpactData :**
- Django 5.2.3 avec modèles complexes
- Génération de badges avec QR codes
- Système de permissions dynamiques
- Gestion de fichiers média (images, PDF)
- Base de données MySQL recommandée pour la production
- Configuration email pour les notifications

## 🎯 Prérequis

- Compte OVH actif
- PuTTY installé sur Windows
- Projet ImpactData prêt (dépôt Git)
- Nom de domaine (recommandé)
- Connaissances de base Linux/CMD

## 📊 Configuration VPS Recommandée

### **Spécifications Minimales**

- **CPU** : 4-6 vCores
- **RAM** : 8-16 GB
- **Stockage** : 100-200 GB SSD
- **OS** : Ubuntu 22.04 LTS

### **Spécifications Optimales (10k+ adhérents)**

- **CPU** : 6-12 vCores
- **RAM** : 12-24 GB
- **Stockage** : 200-500 GB SSD NVMe
- **Bande passante** : 8-15 TB/mois

## 🔧 Étape 1 : Acquisition et Configuration VPS OVH

1. **Commande du VPS :**
    - Connectez-vous au portail OVH
    - Choisissez un VPS avec les spécifications ci-dessus
    - Sélectionnez Ubuntu 22.04 LTS
    - Configurez une clé SSH (recommandé)
2. **Génération clé SSH (Windows) :**
    
    ```bash
    # Téléchargez PuTTYgen depuis https://www.putty.org/
    # Générez une paire de clés RSA 2048 bits
    # Sauvegardez la clé privée (.ppk) et ajoutez la clé publique dans OVH
    ```
    

## 🔐 Étape 2 : Connexion et Sécurisation Initiale

1. **Connexion PuTTY :**
    
    ```
    Host: IP_DU_VPS_OVH
    Port: 22
    Connection Type: SSH
    ```
    
2. **Configuration utilisateur :**
    
    ```bash
    # Connexion initiale avec rootpasswd  # Changez le mot de passe root# Création utilisateur non-rootadduser impactdata
    User: impact-data1
    password: Impact-Data12
    usermod -aG sudo impactdata
    # Fermer et reconnecter avec impactdata@IP_DU_VPS
    ```
    
3. **Mise à jour système :**
    
    ```bash
    sudo apt update && sudo apt upgrade -ysudo apt install -y git curl wget unzip htop
    ```
    

## 🛡️ Étape 3 : Sécurisation du Serveur

1. **Configuration pare-feu UFW :**
    
    ```bash
    sudo apt install ufw
    sudo ufw allow OpenSSH
    sudo ufw allow 80/tcp    # HTTPsudo ufw allow 443/tcp   # HTTPSsudo ufw allow 22/tcp    # SSHsudo ufw enable
    ```
    
2. **Installation Fail2Ban :**
    
    ```bash
    sudo apt install fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    ```
    

## 🐍 Étape 4 : Installation Python et Dépendances

1. **Installation Python et outils :**
    
    ```bash
    sudo apt install -y python3 python3-pip python3-venv python3-dev
    sudo apt install -y build-essential libssl-dev libffi-dev
    sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev
    installation des dependances: le serveur n'arrivait pas à charger MySQL 
		solution : sudo apt install -y pkg-config python3-dev default-libmysqlclient-dev build-essential
    ```
    
2. **Installation MySQL :**
    
    ```bash
    sudo apt install -y mysql-server mysql-client libmysqlclient-dev
    sudo mysql_secure_installation
    ```
    
3. **Configuration MySQL pour ImpactData :**
    
    ```bash
    sudo mysql -u root -p
    ```
    
    ```sql
    CREATE DATABASE impactdata CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    CREATE USER 'impact_user12'@'localhost' IDENTIFIED BY 'Impact@Data12';
    GRANT ALL PRIVILEGES ON impactdata.* TO 'impact_user12'@'localhost';
    FLUSH PRIVILEGES;
    EXIT;
    ```
    

## 📁 Étape 5 : Déploiement du Projet ImpactData

1. **Création structure projet :**
    
    ```bash
    sudo mkdir -p /var/www/impactdata
    sudo chown impactdata:impactdata /var/www/impactdata
    cd /var/www/impactdata
    ```
    
2. **Clonage du projet :**
    
    ```bash
    git clone https://github.com/votre-repo/impactdata.git .
    ```
    
3. **Configuration environnement virtuel :**
    
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    ```
    
4. **Installation dépendances ImpactData :**
    
    ```bash
    pip install -r requirements.txt
    # Si erreur MySQL, installer :pip install mysqlclient==2.2.7
    ```
    

## ⚙️ Étape 6 : Configuration Django Production

1. **Création fichier .env :**
    
    ```bash
    nano .env
    ```
    
    ```
    # Configuration ImpactData Production
    SECRET_KEY=votre_cle_secrete_tres_longue_et_complexe
    DEBUG=False
    
    # Base de données MySQL
    DB_NAME=impactdata
    DB_USER=impactdata_user
    DB_PASSWORD=VOTRE_MOT_DE_PASSE_FORT
    DB_HOST=localhost
    DB_PORT=3306
    
    # Configuration Email (obligatoire pour ImpactData)
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_USE_SSL=True
    EMAIL_HOST_USER=votre_email@gmail.com
    EMAIL_HOST_PASSWORD=votre_mot_de_passe_application
    DEFAULT_FROM_EMAIL=votre_email@gmail.com
    
    # Domaine
    ALLOWED_HOSTS=votre-domaine.com,IP_DU_VPS
    ```
    
2. **Modification settings.py :**
    
    ```bash
    nano impactData/settings.py
    ```
    
    ```python
    # Décommenter la section MySQL et commenter SQLiteDATABASES = {
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
    # Configuration productionDEBUG = FalseALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
    # SécuritéSESSION_COOKIE_SECURE = TrueCSRF_COOKIE_SECURE = TrueSECURE_BROWSER_XSS_FILTER = TrueSECURE_CONTENT_TYPE_NOSNIFF = True
    ```
    
3. **Initialisation base de données :**
    
    ```bash
    python manage.py migrate
    python manage.py collectstatic --noinput
    ```
    
4. **Initialisation données ImpactData :**
    
    ```bash
    # Valeurs de référence (obligatoire)python manage.py initialize_reference_values
    # Permissions par défaut (obligatoire)python manage.py initialize_permissions
    # Création superutilisateurpython manage.py createsuperuser
    Compte super user impact data:
      email:tarikgroupe224@gmail.com
      password: Impact@dataAdmin15
    ```
    
5. **Tests de validation ImpactData :**
    
    ```bash
    # Test configuration emailpython manage.py test_email
    # Test génération de badges et QR codespython manage.py test_badge_generation
    ```
    

## 🔧 Étape 7 : Configuration Gunicorn

1. **Création service systemd :**
    
    ```bash
    sudo nano /etc/systemd/system/impactdata.service
    ```
    
    ```
    [Unit]Description=ImpactData Gunicorn daemonAfter=network.target[Service]User=impactdataGroup=www-dataWorkingDirectory=/var/www/impactdataEnvironment="PATH=/var/www/impactdata/venv/bin"ExecStart=/var/www/impactdata/venv/bin/gunicorn --access-logfile - --workers 4 --bind unix:/var/www/impactdata/impactdata.sock impactData.wsgi:applicationExecReload=/bin/kill -s HUP $MAINPIDRestart=on-failure[Install]WantedBy=multi-user.target
    ```
    
2. **Activation service :**
    
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start impactdata
    sudo systemctl enable impactdata
    sudo systemctl status impactdata
    ```
    

## 🌐 Étape 8 : Configuration Nginx

1. **Installation Nginx :**
    
    ```bash
    sudo apt install nginx
    ```
    
2. **Configuration site ImpactData :**
    
    ```bash
    sudo nano /etc/nginx/sites-available/impactdata
    ```
    
    ```
    server {
        listen 80;
        server_name votre-domaine.com IP_DU_VPS;
    
        client_max_body_size 50M;  # Pour upload d'images badges
    
        # Fichiers statiques
        location /static/ {
            alias /var/www/impactdata/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    
        # Fichiers média (badges, images)
        location /media/ {
            alias /var/www/impactdata/media/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    
        # Application Django
        location / {
            proxy_set_header Host $http_host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_pass http://unix:/var/www/impactdata/impactdata.sock;
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
        }
    }
    ```
    
3. **Activation site :**
    
    ```bash
    sudo ln -s /etc/nginx/sites-available/impactdata /etc/nginx/sites-enabled/
    sudo rm /etc/nginx/sites-enabled/default
    sudo nginx -tsudo systemctl restart nginx
    sudo systemctl enable nginx
    ```
    

## 🔒 Étape 9 : Configuration SSL et Domaine

1. **Configuration DNS OVH :**
    - Ajoutez un enregistrement A : `votre-domaine.com` → `IP_DU_VPS`
2. **Installation Certbot :**
    
    ```bash
    sudo apt install certbot python3-certbot-nginx
    sudo certbot --nginx -d votre-domaine.com
    ```
    
3. **Test SSL :**
    
    ```bash
    sudo certbot renew --dry-run
    ```
    

## 📊 Étape 10 : Optimisations ImpactData

1. **Configuration Redis (optionnel) :**
    
    ```bash
    sudo apt install redis-server
    pip install redis django-redis
    ```
    
2. **Configuration cache dans settings.py :**
    
    ```python
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    ```
    
3. **Optimisation MySQL :**
    
    ```bash
    sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
    ```
    
    ```
    [mysqld]innodb_buffer_pool_size = 2Ginnodb_log_file_size = 256Mmax_connections = 200query_cache_size = 64M
    ```
    

## 🔍 Étape 11 : Tests et Validation

1. **Test accès site :**
    
    ```bash
    curl -I http://votre-domaine.com
    curl -I https://votre-domaine.com
    ```
    
2. **Test génération badges :**
    
    ```bash
    cd /var/www/impactdata
    source venv/bin/activate
    python manage.py test_badge_generation
    ```
    
3. **Test email :**
    
    ```bash
    python manage.py test_email
    ```
    
4. **Vérification logs :**
    
    ```bash
    sudo journalctl -u impactdata -fsudo tail -f /var/log/nginx/error.log
    ```
    

## 🛠️ Étape 12 : Maintenance et Monitoring

1. **Script de sauvegarde :**
    
    ```bash
    sudo nano /usr/local/bin/backup-impactdata.sh
    ```
    
    ```bash
    #!/bin/bashDATE=$(date +%Y%m%d_%H%M%S)BACKUP_DIR="/var/backups/impactdata"mkdir -p $BACKUP_DIR# Sauvegarde base de donnéesmysqldump -u impactdata_user -p impactdata > $BACKUP_DIR/db_$DATE.sql
    # Sauvegarde fichiers médiatar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/impactdata/media/
    # Nettoyage anciennes sauvegardes (7 jours)find $BACKUP_DIR -name "*.sql" -mtime +7 -deletefind $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
    ```
    
2. **Cron pour sauvegardes :**
    
    ```bash
    sudo crontab -e# Ajouter : 0 2 * * * /usr/local/bin/backup-impactdata.sh
    ```
    
3. **Monitoring ressources :**
    
    ```bash
    sudo apt install htop iotop
    # Surveiller CPU, RAM, disque
    ```
    

## 🔧 Commandes de Maintenance ImpactData

### **Nettoyage de la base de données :**

```bash
cd /var/www/impactdata
source venv/bin/activate
# Nettoyer les doublons de badgespython manage.py clean_badge_duplicates
# Nettoyer les doublons d'adhérentspython manage.py fix_adherent_duplicates
# Nettoyer complètement la base de donnéespython manage.py clean_database
```

### **Mise à jour des données :**

```bash
# Mettre à jour les objectifspython manage.py update_objectives
# Mettre à jour les informations de badgespython manage.py update_badge_info
# Mettre à jour les badges existantspython manage.py update_existing_adherents_badge_info
```

### **Réparation des problèmes :**

```bash
# Corriger les problèmes de badgespython manage.py fix_badge_issues
# Lister les adhérents avec badgespython manage.py list_adherents_badge
```

### **Tests de validation :**

```bash
# Test configuration emailpython manage.py test_email
# Test génération de badgespython manage.py test_badge_generation
```

## 🚨 Dépannage ImpactData

### **Problèmes courants :**

1. **Erreur génération badges :**
    
    ```bash
    sudo apt install wkhtmltopdf
    pip install --upgrade pillow qrcode reportlab
    ```
    
2. **Erreur permissions fichiers :**
    
    ```bash
    sudo chown -R impactdata:www-data /var/www/impactdata
    sudo chmod -R 755 /var/www/impactdata
    ```
    
3. **Erreur base de données :**
    
    ```bash
    python manage.py migrate --fake-initialpython manage.py initialize_reference_values --force
    ```
    
4. **Erreur email :**
    
    ```bash
    # Vérifier configuration .envpython manage.py test_email
    ```
    
5. **Erreur de migration :**
    
    ```bash
    # Réinitialiser les migrations si nécessairepython manage.py migrate --fake-initial
    ```
    
6. **Erreur de permissions :**
    
    ```bash
    # Réinitialiser les permissionspython manage.py initialize_permissions --force
    ```
    
7. **Erreur de base de données :**
    
    ```bash
    # Vérifier la connexion MySQLmysql -u impactdata_user -p impactdata
    # Vérifier les paramètres dans .env
    ```
    

## 📈 Optimisations Performance

### **Pour 10 000+ adhérents :**

1. **Configuration Gunicorn :**
    
    ```bash
    # Augmenter workers selon CPU--workers 8 --worker-class gevent --worker-connections 1000
    ```
    
2. **Configuration Nginx :**
    
    ```
    # Ajouter dans server block
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    client_max_body_size 100M;
    ```
    
3. **Base de données :**
    
    ```sql
    # Index sur colonnes fréquemment utilisées
    CREATE INDEX idx_adherent_identifiant ON core_adherent(identifiant);
    CREATE INDEX idx_adherent_organisation ON core_adherent(organisation_id);
    ```
    

## 🔄 Mise à jour ImpactData

```bash
cd /var/www/impactdata
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinputsudo systemctl restart impactdata
```

## 📋 Configuration Post-Installation

### **Créer les premiers utilisateurs :**

1. Se connecter avec le superutilisateur créé
2. Aller dans l’interface d’administration
3. Créer des utilisateurs avec différents rôles :
    - **Administrateur** : Accès complet
    - **Superviseur** : Gestion des agents
    - **Agent** : Saisie des données

### **Configurer les paramètres généraux :**

1. Aller dans **Paramètres > Paramètres Généraux**
2. Configurer les informations de l’organisation
3. Ajuster les paramètres de sécurité
4. Configurer les paramètres d’interface

### **Valeurs de référence initialisées :**

- Statuts d’interaction (En cours, Terminé, Annulé)
- Statuts de badge (Actif, Expiré, Révoqué)
- Statuts d’objectif (En attente, En cours, Terminé, Échoué)
- Rôles utilisateur (Administrateur, Superviseur, Agent)
- Types d’adhérent (Personne Physique, Personne Morale)
- Types de profession (Médecin, Infirmier, Enseignant, etc.)
- Types de téléphone et d’urgence
- Types d’informations médicales et de formation
- Types de distinction et de langue
- Types d’activité
- Catégories d’organisation

### **Permissions configurées :**

- **Administrateur** : Accès complet à toutes les fonctionnalités
- **Superviseur** : Gestion des agents et des données
- **Agent** : Saisie et consultation des données

## 📞 Support et Ressources

- **Documentation ImpactData** : README.md du projet
- **Logs application** : `sudo journalctl -u impactdata`
- **Logs Nginx** : `/var/log/nginx/error.log`
- **Logs MySQL** : `/var/log/mysql/error.log`

---

**ImpactData** est maintenant déployé et prêt à gérer vos 10 000+ adhérents avec génération de badges et système de permissions dynamiques ! 🎉