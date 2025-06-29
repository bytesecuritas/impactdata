# Impact Data - Système de Gestion des Adhérents

## Description
Système de gestion des adhérents, organisations et interactions avec gestion des rôles et objectifs.

## Fonctionnalités

### Rôles et Permissions

#### Administrateurs
- Accès complet à toutes les fonctionnalités
- Peut créer et gérer tous les types d'utilisateurs (admin, superviseur, agent)
- Peut assigner des superviseurs aux agents
- Accès aux statistiques globales

#### Superviseurs
- Accès à toutes les fonctionnalités des agents
- Peut créer uniquement des agents qui lui sont assignés
- Peut voir les statistiques de ses agents assignés
- Peut assigner des objectifs aux agents
- Gestion des objectifs (création, modification, suppression)

#### Agents
- Accès aux catégories, organisations, adhérents, interactions
- Peut voir et modifier son propre profil
- Pas d'accès à la gestion des utilisateurs
- Accès limité aux données selon ses organisations

### Modules Principaux

#### Gestion des Utilisateurs
- Création, modification, suppression d'utilisateurs
- Gestion des rôles et permissions
- Système de matricules uniques
- Historique des connexions et actions

#### Gestion des Organisations
- Création et gestion des organisations
- Catégorisation des organisations
- Statistiques par organisation
- Gestion des adhérents par organisation

#### Gestion des Adhérents
- Enregistrement des adhérents avec identifiants uniques
- Informations personnelles et médicales
- Photos de profil
- Historique des adhésions

#### Gestion des Interactions
- Suivi des interactions avec les adhérents
- Rapports détaillés
- Statuts des interactions
- Échéances et suivi

#### Système d'Objectifs
- Assignation d'objectifs aux agents par les superviseurs
- Types d'objectifs : organisations, adhérents, interactions
- Suivi de la progression
- Alertes d'échéance

#### Badges et QR Codes
- Génération de badges pour les adhérents
- QR codes pour identification
- Gestion de la validité des badges
- Photos d'activités

### Fonctionnalités Techniques

#### Sécurité
- Authentification personnalisée
- Gestion des sessions
- Journalisation des actions
- Verrouillage de comptes après échecs

#### Interface
- Interface responsive Bootstrap 5
- Tableaux de bord personnalisés par rôle
- Filtres et recherche avancés
- Pagination des résultats

#### Rapports
- Génération de rapports PDF
- Statistiques en temps réel
- Export de données
- Graphiques de progression

## Installation

1. Cloner le repository
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer la base de données
4. Exécuter les migrations : `python manage.py migrate`
5. Créer un superutilisateur : `python manage.py createsuperuser`
6. Lancer le serveur : `python manage.py runserver`

## Structure des Modèles

### User (Utilisateur)
- Rôles : admin, superviseur, agent
- Matricule unique
- Informations personnelles et professionnelles
- Gestion des permissions

### Organization (Organisation)
- Identifiant unique
- Informations de contact et financières
- Catégorisation
- Gestion des adhérents

### Adherent (Adhérent)
- Identifiant basé sur l'organisation
- Informations personnelles complètes
- Données médicales et professionnelles
- Photos et documents

### Interaction
- Suivi des interactions
- Rapports détaillés
- Statuts et échéances
- Assignation au personnel

### UserObjective
- Objectifs assignés aux agents
- Types : organisations, adhérents, interactions
- Suivi de progression
- Échéances et alertes

### SupervisorStats
- Statistiques des agents par superviseur
- Mise à jour automatique
- Historique des performances

## URLs Principales

- `/` - Tableau de bord selon le rôle
- `/users/` - Gestion des utilisateurs
- `/organizations/` - Gestion des organisations
- `/adherents/` - Gestion des adhérents
- `/interactions/` - Gestion des interactions
- `/objectives/` - Gestion des objectifs
- `/badges/` - Gestion des badges

## Développement

### Ajout de nouvelles fonctionnalités
1. Créer les modèles dans `core/models.py`
2. Ajouter les formulaires dans `core/forms.py`
3. Créer les vues dans `core/views.py`
4. Ajouter les URLs dans `core/urls.py`
5. Créer les templates dans `core/templates/`

### Tests
- Tests unitaires pour les modèles
- Tests d'intégration pour les vues
- Tests de sécurité pour les permissions

## Support

Pour toute question ou problème, contacter l'équipe de développement.

