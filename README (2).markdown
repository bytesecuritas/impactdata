# Configuration d'un VPS OVH pour l'Hébergement d'un Site Django avec PuTTY (Windows CMD)

## Introduction

Ce README explique comment configurer un VPS OVH pour héberger un site Django en utilisant PuTTY sous Windows (via CMD) pour la connexion SSH. Chaque commande est accompagnée d'une explication de son importance pour garantir une configuration claire et sécurisée. Ce guide suppose l'utilisation d'Ubuntu 22.04 LTS sur le VPS. Une annexe sur les bases des commandes Linux (Ubuntu) est incluse à la fin pour les débutants.

**Avertissement :** Suivez les bonnes pratiques de sécurité. Consultez la documentation officielle d'OVH pour les dernières informations, car les interfaces ou commandes peuvent évoluer.

## Prérequis

- Un compte OVH actif.
- PuTTY installé sur Windows (téléchargeable depuis https://www.putty.org/).
- Connaissances de base en ligne de commande Linux et CMD Windows.
- Un projet Django prêt à déployer (avec dépôt Git recommandé).
- Un nom de domaine (optionnel pour la production).
- Outils locaux : PuTTY, Git for Windows.

## Étape 1 : Acquisition du VPS sur OVH

1. Connectez-vous à votre compte OVH via le portail client.
2. Accédez à la section "Public Cloud" ou "VPS" et sélectionnez un plan (ex. : VPS Starter).
3. Choisissez Ubuntu 22.04 LTS comme distribution.
4. Configurez une clé SSH (recommandé) ou utilisez un mot de passe. Pour générer une clé SSH sous Windows :
   - Téléchargez PuTTYgen (inclus avec PuTTY).
   - Générez une paire de clés, sauvegardez la clé publique et ajoutez-la dans l'interface OVH.
   - Sauvegardez la clé privée (.ppk) pour PuTTY.
5. Validez la commande. OVH envoie les détails (IP, utilisateur root, mot de passe si pas de clé SSH) par email.

**Importance :** Cette étape provisionne le VPS et établit les paramètres d'accès initiaux. Une clé SSH améliore la sécurité par rapport à un mot de passe.

## Étape 2 : Connexion au VPS avec PuTTY

1. Ouvrez PuTTY sur Windows.
2. Dans le champ "Host Name (or IP address)", entrez l'IP du VPS fournie par OVH.
3. Dans "Connection > SSH > Auth", chargez votre clé privée (.ppk) si configurée.
4. Cliquez sur "Open" pour lancer la connexion.
5. Si vous utilisez un mot de passe, entrez `root` comme utilisateur et le mot de passe OVH.
6. Changez le mot de passe root :
   ```
   passwd
   ```
   **Importance :** Change le mot de passe par défaut pour sécuriser l'accès root, réduisant les risques d'attaques par force brute.
7. Créez un utilisateur non-root :
   ```
   adduser nomutilisateur
   ```
   **Importance :** Crée un utilisateur avec des privilèges limités pour les opérations quotidiennes, réduisant les risques d'erreurs critiques.
   ```
   usermod -aG sudo nomutilisateur
   ```
   **Importance :** Ajoute l'utilisateur au groupe sudo, permettant d'exécuter des commandes administratives tout en limitant l'accès root direct.
8. Fermez PuTTY, puis reconnectez-vous avec l'utilisateur non-root (`nomutilisateur@IP_DU_VPS`).

**Astuce Windows CMD :** Pour lancer PuTTY via CMD :
   ```
   putty -ssh nomutilisateur@IP_DU_VPS -i chemin\vers\votre_cle.ppk
   ```
   **Importance :** Automatise la connexion SSH avec la clé privée, simplifiant l'accès sécurisé depuis CMD.

## Étape 3 : Mise à Jour et Sécurisation du Système

1. Mettez à jour le système :
   ```
   sudo apt update && sudo apt upgrade -y
   ```
   **Importance :** `apt update` actualise la liste des paquets disponibles, et `apt upgrade` installe les dernières versions, corrigeant les vulnérabilités et améliorant la stabilité.
2. Installez les outils essentiels :
   ```
   sudo apt install -y git curl wget unzip
   ```
   **Importance :** Installe Git (pour cloner le projet), curl/wget (pour télécharger des fichiers), et unzip (pour gérer les archives), outils essentiels pour le déploiement.
3. Configurez un pare-feu avec UFW :
   ```
   sudo apt install ufw
   ```
   **Importance :** Installe UFW, un outil simple pour gérer les règles de pare-feu, renforçant la sécurité.
   ```
   sudo ufw allow OpenSSH
   ```
   **Importance :** Autorise les connexions SSH pour maintenir l'accès au VPS.
   ```
   sudo ufw allow 80/tcp
   ```
   **Importance :** Ouvre le port 80 pour le trafic HTTP, nécessaire pour accéder au site avant la configuration SSL.
   ```
   sudo ufw allow 443/tcp
   ```
   **Importance :** Ouvre le port 443 pour HTTPS, essentiel pour un site sécurisé.
   ```
   sudo ufw enable
   ```
   **Importance :** Active le pare-feu, appliquant les règles pour protéger le serveur contre les accès non autorisés.
4. (Optionnel) Installez Fail2Ban :
   ```
   sudo apt install fail2ban
   ```
   **Importance :** Protège contre les attaques par force brute en bloquant automatiquement les adresses IP suspectes.

## Étape 4 : Installation de Python et Dépendances Django

1. Installez Python 3 et les outils associés :
   ```
   sudo apt install -y python3 python3-pip python3-venv
   ```
   **Importance :** Installe Python 3 (requis pour Django), pip (gestionnaire de paquets Python), et venv (pour créer des environnements isolés).
2. Créez un répertoire pour votre projet et un environnement virtuel :
   ```
   mkdir /var/www/monprojet
   ```
   **Importance :** Crée un répertoire structuré pour organiser le projet Django.
   ```
   cd /var/www/monprojet
   ```
   **Importance :** Se déplace dans le répertoire du projet pour les commandes suivantes.
   ```
   python3 -m venv venv
   ```
   **Importance :** Crée un environnement virtuel pour isoler les dépendances du projet, évitant les conflits avec le système.
   ```
   source venv/bin/activate
   ```
   **Importance :** Active l'environnement virtuel, permettant l'utilisation des paquets installés localement.
3. Installez Django et Gunicorn :
   ```
   pip install django gunicorn psycopg2-binary
   ```
   **Importance :** Installe Django (framework web), Gunicorn (serveur WSGI pour exécuter l'application), et psycopg2-binary (adaptateur pour PostgreSQL).

## Étape 5 : Déploiement du Projet Django

1. Depuis votre machine Windows, poussez votre projet Django vers un dépôt Git (ex. : GitHub).
2. Sur le VPS via PuTTY, clonez le dépôt :
   ```
   git clone https://github.com/votreutilisateur/votredjango.git /var/www/monprojet
   ```
   **Importance :** Télécharge le code source du projet depuis Git, permettant un déploiement facile et des mises à jour via Git.
3. Configurez `settings.py` pour la production :
   ```
   nano /var/www/monprojet/monprojet/settings.py
   ```
   **Importance :** Ouvre l'éditeur nano pour modifier le fichier de configuration Django.
   Modifiez :
   ```
   DEBUG = False
   ALLOWED_HOSTS = ['votre-domaine.com', 'IP_DU_VPS']
   ```
   **Importance :** Désactive le mode débogage (sécurité) et spécifie les hôtes autorisés pour accepter les requêtes.
4. Collectez les fichiers statiques :
   ```
   python manage.py collectstatic
   ```
   **Importance :** Rassemble les fichiers statiques (CSS, JS, images) dans un dossier accessible par le serveur web.
5. (Si base de données) Installez PostgreSQL :
   ```
   sudo apt install postgresql postgresql-contrib
   ```
   **Importance :** Installe PostgreSQL, une base de données robuste pour les applications Django.
   ```
   sudo -u postgres psql
   CREATE DATABASE madb;
   CREATE USER monuser WITH PASSWORD 'motdepasse';
   GRANT ALL PRIVILEGES ON DATABASE madb TO monuser;
   \q
   ```
   **Importance :** Configure une base de données, un utilisateur, et des permissions pour connecter Django à PostgreSQL. `\q` quitte l'interface psql.
   Mettez à jour `settings.py` avec les informations de la base de données.

## Étape 6 : Configuration de Gunicorn

1. Créez un fichier de service systemd pour Gunicorn :
   ```
   sudo nano /etc/systemd/system/gunicorn.service
   ```
   **Importance :** Crée un fichier de service pour exécuter Gunicorn comme un daemon système, assurant un démarrage automatique.
   Ajoutez :
   ```
   [Unit]
   Description=gunicorn daemon
   After=network.target

   [Service]
   User=nomutilisateur
   Group=www-data
   WorkingDirectory=/var/www/monprojet
   Environment="PATH=/var/www/monprojet/venv/bin"
   ExecStart=/var/www/monprojet/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/monprojet/monprojet.sock monprojet.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```
   **Importance :** Configure Gunicorn pour s'exécuter avec l'utilisateur non-root, utiliser l'environnement virtuel, et lier à un socket Unix pour communiquer avec Nginx.
2. Activez et démarrez Gunicorn :
   ```
   sudo systemctl daemon-reload
   ```
   **Importance :** Recharge les configurations systemd pour prendre en compte le nouveau fichier de service.
   ```
   sudo systemctl start gunicorn
   ```
   **Importance :** Démarre le service Gunicorn immédiatement.
   ```
   sudo systemctl enable gunicorn
   ```
   **Importance :** Configure Gunicorn pour démarrer automatiquement au redémarrage du VPS.

## Étape 7 : Configuration de Nginx

1. Installez Nginx :
   ```
   sudo apt install nginx
   ```
   **Importance :** Installe Nginx, un serveur web performant pour servir les requêtes HTTP/HTTPS et les fichiers statiques.
2. Créez un fichier de configuration Nginx :
   ```
   sudo nano /etc/nginx/sites-available/monprojet
   ```
   **Importance :** Crée un fichier de configuration spécifique pour le site Django.
   Ajoutez :
   ```
   server {
       listen 80;
       server_name votre-domaine.com;

       location = /favicon.ico { access_log off; log_not_found off; }
       location /static/ {
           root /var/www/monprojet;
       }

       location / {
           proxy_set_header Host $http_host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_pass http://unix:/var/www/monprojet/monprojet.sock;
       }
   }
   ```
   **Importance :** Configure Nginx pour écouter sur le port 80, servir les fichiers statiques, et transmettre les requêtes dynamiques à Gunicorn via un socket Unix.
3. Activez le site et redémarrez Nginx :
   ```
   sudo ln -s /etc/nginx/sites-available/monprojet /etc/nginx/sites-enabled
   ```
   **Importance :** Crée un lien symbolique pour activer la configuration du site.
   ```
   sudo nginx -t
   ```
   **Importance :** Vérifie la syntaxe de la configuration Nginx pour éviter les erreurs.
   ```
   sudo systemctl restart nginx
   ```
   **Importance :** Redémarre Nginx pour appliquer la nouvelle configuration.

## Étape 8 : Configuration du Domaine et SSL

1. Dans l'interface OVH, configurez un enregistrement DNS A pour pointer `votre-domaine.com` vers l'IP du VPS.
   **Importance :** Associe le domaine à l'IP du VPS pour rendre le site accessible via le nom de domaine.
2. Installez Certbot pour SSL (Let's Encrypt) :
   ```
   sudo apt install certbot python3-certbot-nginx
   ```
   **Importance :** Installe Certbot et son plugin Nginx pour configurer automatiquement un certificat SSL.
   ```
   sudo certbot --nginx -d votre-domaine.com
   ```
   **Importance :** Configure HTTPS en obtenant et installant un certificat SSL, sécurisant les connexions au site.

## Étape 9 : Tests et Maintenance

1. Testez l'accès au site via `http://IP_DU_VPS` ou `https://votre-domaine.com`.
   **Importance :** Vérifie que le site est accessible et fonctionne correctement.
2. Vérifiez les logs si nécessaire :
   ```
   sudo journalctl -u gunicorn
   ```
   **Importance :** Affiche les logs de Gunicorn pour diagnostiquer les erreurs d'application.
   ```
   sudo tail -f /var/log/nginx/error.log
   ```
   **Importance :** Surveille les logs d'erreurs Nginx en temps réel pour identifier les problèmes de serveur web.
3. Mettez à jour régulièrement le système :
   ```
   sudo apt update && sudo apt upgrade -y
   ```
   **Importance :** Maintient le système à jour avec les derniers correctifs de sécurité et améliorations.

## Annexe : Bases des Commandes Linux (Ubuntu)

Cette annexe présente les commandes Linux de base utilisées dans ce guide, utiles pour les débutants travaillant sur Ubuntu via PuTTY.

### Navigation et Gestion de Fichiers

- `ls` : Liste les fichiers et dossiers dans le répertoire actuel.
  **Exemple :** `ls -l` affiche les détails (permissions, taille, date).
  **Importance :** Permet de vérifier le contenu d’un répertoire.
- `cd chemin` : Change de répertoire.
  **Exemple :** `cd /var/www/monprojet` navigue vers le dossier du projet.
  **Importance :** Essentiel pour se déplacer dans l’arborescence.
- `pwd` : Affiche le chemin du répertoire actuel.
  **Importance :** Confirme votre position dans le système de fichiers.
- `mkdir nomdossier` : Crée un nouveau dossier.
  **Exemple :** `mkdir /var/www/monprojet`.
  **Importance :** Organise les fichiers du projet.
- `nano chemin/fichier` : Ouvre l’éditeur de texte nano pour modifier un fichier.
  **Exemple :** `nano /etc/nginx/sites-available/monprojet`.
  **Importance :** Permet d’éditer des fichiers de configuration (Ctrl+O pour sauvegarder, Ctrl+X pour quitter).

### Gestion des Paquets

- `sudo apt update` : Met à jour la liste des paquets disponibles.
  **Importance :** Assure que vous installez les dernières versions des logiciels.
- `sudo apt upgrade -y` : Met à jour les paquets installés.
  **Importance :** Corrige les vulnérabilités et améliore la stabilité.
- `sudo apt install paquet` : Installe un paquet spécifique.
  **Exemple :** `sudo apt install nginx`.
  **Importance :** Ajoute les logiciels nécessaires au système.

### Gestion des Permissions et Utilisateurs

- `sudo commande` : Exécute une commande avec des privilèges administratifs.
  **Exemple :** `sudo apt install ufw`.
  **Importance :** Nécessaire pour les tâches nécessitant des droits root.
- `adduser nomutilisateur` : Crée un nouvel utilisateur.
  **Importance :** Améliore la sécurité en évitant l’utilisation de root.
- `usermod -aG groupe utilisateur` : Ajoute un utilisateur à un groupe.
  **Exemple :** `usermod -aG sudo nomutilisateur`.
  **Importance :** Accorde des privilèges spécifiques, comme sudo.

### Gestion des Services

- `sudo systemctl start service` : Démarre un service.
  **Exemple :** `sudo systemctl start gunicorn`.
  **Importance :** Active un service immédiatement.
- `sudo systemctl enable service` : Configure un service pour démarrer au boot.
  **Exemple :** `sudo systemctl enable nginx`.
  **Importance :** Assure la disponibilité continue des services.
- `sudo systemctl restart service` : Redémarre un service.
  **Exemple :** `sudo systemctl restart nginx`.
  **Importance :** Applique les modifications de configuration.
- `sudo systemctl daemon-reload` : Recharge les configurations systemd.
  **Importance :** Prend en compte les nouveaux fichiers de service.

### Gestion des Logs

- `sudo journalctl -u service` : Affiche les logs d’un service.
  **Exemple :** `sudo journalctl -u gunicorn`.
  **Importance :** Aide à diagnostiquer les erreurs d’un service.
- `sudo tail -f /chemin/vers/fichier.log` : Affiche les dernières lignes d’un fichier de log en temps réel.
  **Exemple :** `sudo tail -f /var/log/nginx/error.log`.
  **Importance :** Permet de surveiller les erreurs en direct.

### Commandes Git

- `git clone url` : Télécharge un dépôt Git.
  **Exemple :** `git clone https://github.com/votreutilisateur/votredjango.git`.
  **Importance :** Récupère le code source pour le déploiement.

### Commandes Python/Django

- `python3 -m venv nom` : Crée un environnement virtuel Python.
  **Exemple :** `python3 -m venv venv`.
  **Importance :** Isole les dépendances du projet.
- `source chemin/bin/activate` : Active un environnement virtuel.
  **Exemple :** `source venv/bin/activate`.
  **Importance :** Utilise les paquets installés dans l’environnement virtuel.
- `pip install paquet` : Installe un paquet Python.
  **Exemple :** `pip install django`.
  **Importance :** Ajoute les dépendances nécessaires au projet.
- `python manage.py collectstatic` : Collecte les fichiers statiques Django.
  **Importance :** Prépare les fichiers pour le serveur web.

### Commandes PostgreSQL

- `sudo -u postgres psql` : Ouvre l’interface PostgreSQL.
  **Importance :** Permet de configurer la base de données.
- `CREATE DATABASE nom;` : Crée une base de données.
  **Importance :** Fournit un espace pour stocker les données de l’application.
- `CREATE USER nom WITH PASSWORD 'motdepasse';` : Crée un utilisateur de base de données.
  **Importance :** Sécurise l’accès à la base de données.
- `GRANT ALL PRIVILEGES ON DATABASE nom TO utilisateur;` : Accorde des permissions.
  **Importance :** Permet à l’utilisateur de gérer la base de données.
- `\q` : Quitte l’interface psql.
  **Importance :** Ferme la session PostgreSQL.

**Astuce :** Pour plus d’informations sur une commande, utilisez `man commande` (ex. : `man ls`) ou `commande --help`.

## Ressources

- Documentation OVH : https://docs.ovh.com/fr/vps/
- PuTTY : https://www.putty.org/
- Guide Django : Consultez des tutoriels sur des sites comme Hostinger ou DigitalOcean pour des détails supplémentaires.

Ce README, adapté pour PuTTY sous Windows, inclut l'importance de chaque commande et une annexe pour les débutants en Linux (Ubuntu). Testez chaque étape dans un environnement de développement avant la production.