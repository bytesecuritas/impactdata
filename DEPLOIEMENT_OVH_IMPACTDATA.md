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
   ```cmd
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
   # Connexion initiale avec root
   passwd  # Changez le mot de passe root
   
   # Création utilisateur non-root
   adduser impactdata
   usermod -aG sudo impactdata
   
   # Fermer et reconnecter avec impactdata@IP_DU_VPS
   ```

3. **Mise à jour système :**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git curl wget unzip htop
   ```

## 🛡️ Étape 3 : Sécurisation du Serveur

1. **Configuration pare-feu UFW :**
   ```bash
   sudo apt install ufw
   sudo ufw allow OpenSSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw allow 22/tcp    # SSH
   sudo ufw enable
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
   CREATE USER 'impactdata_user'@'localhost' IDENTIFIED BY 'VOTRE_MOT_DE_PASSE_FORT';
   GRANT ALL PRIVILEGES ON impactdata.* TO 'impactdata_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

## 🗄️ Configuration MySQL Avancée pour ImpactData

### **1. Configuration MySQL optimisée pour 10 000+ adhérents :**

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

```ini
[mysqld]
# Configuration de base
default-storage-engine = InnoDB
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Optimisations pour ImpactData
innodb_buffer_pool_size = 2G                    # 50-70% de la RAM disponible
innodb_log_file_size = 256M                     # Taille des logs InnoDB
innodb_log_buffer_size = 64M                    # Buffer des logs
innodb_flush_log_at_trx_commit = 2              # Performance vs sécurité
innodb_file_per_table = 1                       # Un fichier par table

# Connexions et requêtes
max_connections = 200                           # Connexions simultanées
max_connect_errors = 1000000                    # Limite d'erreurs de connexion
query_cache_size = 64M                          # Cache des requêtes
query_cache_type = 1                            # Activer le cache
query_cache_limit = 2M                          # Taille max par requête

# Optimisations pour les badges et images
max_allowed_packet = 64M                        # Taille max des paquets
tmp_table_size = 64M                            # Taille des tables temporaires
max_heap_table_size = 64M                       # Taille des tables MEMORY

# Logs et monitoring
slow_query_log = 1                              # Activer les logs lents
slow_query_log_file = /var/log/mysql/slow.log   # Fichier des logs lents
long_query_time = 2                             # Seuil pour requêtes lentes
log_queries_not_using_indexes = 1               # Log des requêtes sans index

# Sécurité
local_infile = 0                                # Désactiver LOAD DATA LOCAL
```

### **2. Redémarrage et vérification :**
```bash
sudo systemctl restart mysql
sudo systemctl status mysql
```

### **3. Création d'index optimisés pour ImpactData :**

```bash
mysql -u impactdata_user -p impactdata
```

```sql
-- Index pour les recherches fréquentes d'adhérents
CREATE INDEX idx_adherent_identifiant ON core_adherent(identifiant);
CREATE INDEX idx_adherent_organisation ON core_adherent(organisation_id);
CREATE INDEX idx_adherent_phone1 ON core_adherent(phone1);
CREATE INDEX idx_adherent_join_date ON core_adherent(join_date);
CREATE INDEX idx_adherent_badge_validity ON core_adherent(badge_validity);

-- Index pour les organisations
CREATE INDEX idx_organization_identifiant ON core_organization(identifiant);
CREATE INDEX idx_organization_category ON core_organization(category_id);
CREATE INDEX idx_organization_created_by ON core_organization(created_by_id);

-- Index pour les interactions
CREATE INDEX idx_interaction_identifiant ON core_interaction(identifiant);
CREATE INDEX idx_interaction_adherent ON core_interaction(adherent_id);
CREATE INDEX idx_interaction_personnel ON core_interaction(personnel_id);
CREATE INDEX idx_interaction_status ON core_interaction(status);
CREATE INDEX idx_interaction_created_at ON core_interaction(created_at);

-- Index pour les badges
CREATE INDEX idx_badge_number ON core_badge(badge_number);
CREATE INDEX idx_badge_adherent ON core_badge(adherent_id);
CREATE INDEX idx_badge_status ON core_badge(status);
CREATE INDEX idx_badge_issued_date ON core_badge(issued_date);

-- Index pour les utilisateurs
CREATE INDEX idx_user_matricule ON core_user(matricule);
CREATE INDEX idx_user_email ON core_user(email);
CREATE INDEX idx_user_role ON core_user(role);
CREATE INDEX idx_user_is_active ON core_user(is_active);

-- Index pour les objectifs
CREATE INDEX idx_userobjective_user ON core_userobjective(user_id);
CREATE INDEX idx_userobjective_status ON core_userobjective(status);
CREATE INDEX idx_userobjective_deadline ON core_userobjective(deadline);

-- Index composites pour les requêtes complexes
CREATE INDEX idx_adherent_org_join_date ON core_adherent(organisation_id, join_date);
CREATE INDEX idx_interaction_personnel_status ON core_interaction(personnel_id, status);
CREATE INDEX idx_badge_adherent_status ON core_badge(adherent_id, status);
```

### **4. Configuration des utilisateurs MySQL :**

```sql
-- Créer un utilisateur pour les sauvegardes
CREATE USER 'backup_user'@'localhost' IDENTIFIED BY 'BACKUP_PASSWORD';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON impactdata.* TO 'backup_user'@'localhost';

-- Créer un utilisateur pour le monitoring
CREATE USER 'monitor_user'@'localhost' IDENTIFIED BY 'MONITOR_PASSWORD';
GRANT PROCESS, REPLICATION CLIENT ON *.* TO 'monitor_user'@'localhost';
GRANT SELECT ON performance_schema.* TO 'monitor_user'@'localhost';

-- Créer un utilisateur pour les rapports (lecture seule)
CREATE USER 'report_user'@'localhost' IDENTIFIED BY 'REPORT_PASSWORD';
GRANT SELECT ON impactdata.* TO 'report_user'@'localhost';

FLUSH PRIVILEGES;
```

### **5. Configuration des partitions (optionnel pour très grandes tables) :**

```sql
-- Partitionner la table des logs système par mois
ALTER TABLE core_systemlog 
PARTITION BY RANGE (YEAR(timestamp) * 100 + MONTH(timestamp)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    PARTITION p202403 VALUES LESS THAN (202404),
    -- Ajouter d'autres partitions selon les besoins
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

### **6. Script de maintenance MySQL :**

```bash
sudo nano /usr/local/bin/mysql-maintenance.sh
```

```bash
#!/bin/bash
# Script de maintenance MySQL pour ImpactData

DB_NAME="impactdata"
DB_USER="impactdata_user"
DB_PASS="VOTRE_MOT_DE_PASSE_FORT"
LOG_FILE="/var/log/mysql-maintenance.log"

echo "$(date): Début de la maintenance MySQL" >> $LOG_FILE

# Optimisation des tables
mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "OPTIMIZE TABLE core_adherent, core_organization, core_interaction, core_badge, core_user;"

# Analyse des tables pour les statistiques
mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "ANALYZE TABLE core_adherent, core_organization, core_interaction, core_badge, core_user;"

# Nettoyage des logs lents anciens
find /var/log/mysql/ -name "slow.log.*" -mtime +30 -delete

# Vérification de l'intégrité
mysql -u $DB_USER -p$DB_PASS $DB_NAME -e "CHECK TABLE core_adherent, core_organization, core_interaction, core_badge, core_user;"

echo "$(date): Fin de la maintenance MySQL" >> $LOG_FILE
```

```bash
sudo chmod +x /usr/local/bin/mysql-maintenance.sh
```

### **7. Monitoring MySQL :**

```bash
# Installation d'outils de monitoring
sudo apt install mysql-client-core-8.0

# Script de monitoring des performances
sudo nano /usr/local/bin/mysql-monitor.sh
```

```bash
#!/bin/bash
# Monitoring MySQL pour ImpactData

DB_USER="monitor_user"
DB_PASS="MONITOR_PASSWORD"

echo "=== État des connexions ==="
mysql -u $DB_USER -p$DB_PASS -e "SHOW STATUS LIKE 'Threads_connected';"

echo "=== Requêtes lentes ==="
mysql -u $DB_USER -p$DB_PASS -e "SHOW STATUS LIKE 'Slow_queries';"

echo "=== Cache des requêtes ==="
mysql -u $DB_USER -p$DB_PASS -e "SHOW STATUS LIKE 'Qcache%';"

echo "=== Taille des tables ImpactData ==="
mysql -u $DB_USER -p$DB_PASS -e "
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'impactdata'
ORDER BY (data_length + index_length) DESC;
"

echo "=== Index non utilisés ==="
mysql -u $DB_USER -p$DB_PASS -e "
SELECT 
    object_schema,
    object_name,
    index_name
FROM performance_schema.table_io_waits_summary_by_index_usage 
WHERE object_schema = 'impactdata' 
AND count_star = 0
AND index_name IS NOT NULL;
"
```

### **8. Configuration de la sauvegarde MySQL :**

```bash
sudo nano /usr/local/bin/mysql-backup.sh
```

```bash
#!/bin/bash
# Sauvegarde MySQL pour ImpactData

DB_NAME="impactdata"
DB_USER="backup_user"
DB_PASS="BACKUP_PASSWORD"
BACKUP_DIR="/var/backups/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Sauvegarde complète
mysqldump -u $DB_USER -p$DB_PASS \
    --single-transaction \
    --routines \
    --triggers \
    --events \
    --add-drop-database \
    --databases $DB_NAME > $BACKUP_DIR/impactdata_full_$DATE.sql

# Compression
gzip $BACKUP_DIR/impactdata_full_$DATE.sql

# Sauvegarde des tables critiques uniquement
mysqldump -u $DB_USER -p$DB_PASS \
    --single-transaction \
    --tables $DB_NAME core_adherent core_organization core_user \
    > $BACKUP_DIR/impactdata_critical_$DATE.sql

gzip $BACKUP_DIR/impactdata_critical_$DATE.sql

# Nettoyage des anciennes sauvegardes (7 jours)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Sauvegarde terminée: $DATE"
```

### **9. Configuration cron pour la maintenance :**

```bash
sudo crontab -e
```

```bash
# Maintenance MySQL quotidienne à 3h du matin
0 3 * * * /usr/local/bin/mysql-maintenance.sh

# Sauvegarde MySQL toutes les 6 heures
0 */6 * * * /usr/local/bin/mysql-backup.sh

# Monitoring toutes les heures
0 * * * * /usr/local/bin/mysql-monitor.sh >> /var/log/mysql-monitor.log
```

### **10. Vérification de la configuration :**

```bash
# Test de connexion
mysql -u impactdata_user -p impactdata -e "SELECT VERSION();"

# Vérification des variables de configuration
mysql -u impactdata_user -p impactdata -e "SHOW VARIABLES LIKE 'innodb_buffer_pool_size';"

# Test des performances
mysql -u impactdata_user -p impactdata -e "SELECT COUNT(*) FROM core_adherent;"
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
   # Si erreur MySQL, installer :
   pip install mysqlclient==2.2.7
   ```

## ⚙️ Étape 6 : Configuration Django Production

1. **Création fichier .env :**
   ```bash
   nano .env
   ```
   ```env
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
   # Décommenter la section MySQL et commenter SQLite
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
   
   # Configuration production
   DEBUG = False
   ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')
   
   # Sécurité
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   SECURE_BROWSER_XSS_FILTER = True
   SECURE_CONTENT_TYPE_NOSNIFF = True
   ```

3. **Initialisation base de données :**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```

4. **Initialisation données ImpactData :**
   ```bash
   # Valeurs de référence (obligatoire)
   python manage.py initialize_reference_values
   
   # Permissions par défaut (obligatoire)
   python manage.py initialize_permissions
   
   # Création superutilisateur
   python manage.py createsuperuser
   ```

5. **Tests de validation ImpactData :**
   ```bash
   # Test configuration email
   python manage.py test_email
   
   # Test génération de badges et QR codes
   python manage.py test_badge_generation
   ```

## 🔧 Étape 7 : Configuration Gunicorn

1. **Création service systemd :**
   ```bash
   sudo nano /etc/systemd/system/impactdata.service
   ```
   ```ini
   [Unit]
   Description=ImpactData Gunicorn daemon
   After=network.target

   [Service]
   User=impactdata
   Group=www-data
   WorkingDirectory=/var/www/impactdata
   Environment="PATH=/var/www/impactdata/venv/bin"
   ExecStart=/var/www/impactdata/venv/bin/gunicorn --access-logfile - --workers 4 --bind unix:/var/www/impactdata/impactdata.sock impactData.wsgi:application
   ExecReload=/bin/kill -s HUP $MAINPID
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
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
   ```nginx
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
   sudo nginx -t
   sudo systemctl restart nginx
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
   ```ini
   [mysqld]
   innodb_buffer_pool_size = 2G
   innodb_log_file_size = 256M
   max_connections = 200
   query_cache_size = 64M
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
   sudo journalctl -u impactdata -f
   sudo tail -f /var/log/nginx/error.log
   ```

## 🛠️ Étape 12 : Maintenance et Monitoring

1. **Script de sauvegarde :**
   ```bash
   sudo nano /usr/local/bin/backup-impactdata.sh
   ```
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   BACKUP_DIR="/var/backups/impactdata"
   
   mkdir -p $BACKUP_DIR
   
   # Sauvegarde base de données
   mysqldump -u impactdata_user -p impactdata > $BACKUP_DIR/db_$DATE.sql
   
   # Sauvegarde fichiers média
   tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/impactdata/media/
   
   # Nettoyage anciennes sauvegardes (7 jours)
   find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
   find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
   ```

2. **Cron pour sauvegardes :**
   ```bash
   sudo crontab -e
   # Ajouter : 0 2 * * * /usr/local/bin/backup-impactdata.sh
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

# Nettoyer les doublons de badges
python manage.py clean_badge_duplicates

# Nettoyer les doublons d'adhérents
python manage.py fix_adherent_duplicates

# Nettoyer complètement la base de données
python manage.py clean_database
```

### **Mise à jour des données :**
```bash
# Mettre à jour les objectifs
python manage.py update_objectives

# Mettre à jour les informations de badges
python manage.py update_badge_info

# Mettre à jour les badges existants
python manage.py update_existing_adherents_badge_info
```

### **Réparation des problèmes :**
```bash
# Corriger les problèmes de badges
python manage.py fix_badge_issues

# Lister les adhérents avec badges
python manage.py list_adherents_badge
```

### **Tests de validation :**
```bash
# Test configuration email
python manage.py test_email

# Test génération de badges
python manage.py test_badge_generation
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
   python manage.py migrate --fake-initial
   python manage.py initialize_reference_values --force
   ```

4. **Erreur email :**
   ```bash
   # Vérifier configuration .env
   python manage.py test_email
   ```

5. **Erreur de migration :**
   ```bash
   # Réinitialiser les migrations si nécessaire
   python manage.py migrate --fake-initial
   ```

6. **Erreur de permissions :**
   ```bash
   # Réinitialiser les permissions
   python manage.py initialize_permissions --force
   ```

7. **Erreur de base de données :**
   ```bash
   # Vérifier la connexion MySQL
   mysql -u impactdata_user -p impactdata
   
   # Vérifier les paramètres dans .env
   ```

## 📈 Optimisations Performance

### **Pour 10 000+ adhérents :**

1. **Configuration Gunicorn :**
   ```bash
   # Augmenter workers selon CPU
   --workers 8 --worker-class gevent --worker-connections 1000
   ```

2. **Configuration Nginx :**
   ```nginx
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
python manage.py collectstatic --noinput
sudo systemctl restart impactdata
```

## 📋 Configuration Post-Installation

### **Créer les premiers utilisateurs :**
1. Se connecter avec le superutilisateur créé
2. Aller dans l'interface d'administration
3. Créer des utilisateurs avec différents rôles :
   - **Administrateur** : Accès complet
   - **Superviseur** : Gestion des agents
   - **Agent** : Saisie des données

### **Configurer les paramètres généraux :**
1. Aller dans **Paramètres > Paramètres Généraux**
2. Configurer les informations de l'organisation
3. Ajuster les paramètres de sécurité
4. Configurer les paramètres d'interface

### **Valeurs de référence initialisées :**
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
