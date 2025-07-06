# Système de Permissions Dynamiques

## Vue d'ensemble

Le système de permissions dynamiques permet aux administrateurs de configurer finement les accès des utilisateurs aux différentes fonctionnalités de l'application. Contrairement au système basé uniquement sur les rôles, ce système permet d'activer ou désactiver des permissions spécifiques pour chaque rôle.

## Architecture

### Modèle de données

Le système utilise le modèle `RolePermission` qui associe :
- Un rôle utilisateur (`admin`, `superviseur`, `agent`)
- Une permission spécifique (ex: `adherent_create`, `user_view`)
- Un statut actif/inactif

### Permissions disponibles

#### Gestion des utilisateurs
- `user_create` : Créer des utilisateurs
- `user_edit` : Modifier des utilisateurs
- `user_delete` : Supprimer des utilisateurs
- `user_view` : Voir les utilisateurs
- `user_activate` : Activer/Désactiver des utilisateurs

#### Gestion des adhérents
- `adherent_create` : Créer des adhérents
- `adherent_edit` : Modifier des adhérents
- `adherent_delete` : Supprimer des adhérents
- `adherent_view` : Voir les adhérents

#### Gestion des organisations
- `organization_create` : Créer des organisations
- `organization_edit` : Modifier des organisations
- `organization_delete` : Supprimer des organisations
- `organization_view` : Voir les organisations

#### Gestion des interactions
- `interaction_create` : Créer des interactions
- `interaction_edit` : Modifier des interactions
- `interaction_delete` : Supprimer des interactions
- `interaction_view` : Voir les interactions

#### Gestion des badges
- `badge_create` : Créer des badges
- `badge_edit` : Modifier des badges
- `badge_delete` : Supprimer des badges
- `badge_view` : Voir les badges
- `badge_revoke` : Révoquer des badges

#### Gestion des objectifs
- `objective_create` : Créer des objectifs
- `objective_edit` : Modifier des objectifs
- `objective_delete` : Supprimer des objectifs
- `objective_view` : Voir les objectifs

#### Gestion des paramètres
- `settings_view` : Voir les paramètres
- `settings_edit` : Modifier les paramètres
- `settings_roles` : Gérer les rôles
- `settings_references` : Gérer les valeurs de référence

#### Rapports et statistiques
- `reports_view` : Voir les rapports
- `reports_export` : Exporter les rapports
- `stats_view` : Voir les statistiques

#### Administration système
- `system_admin` : Administration système
- `data_backup` : Sauvegarde des données
- `data_restore` : Restauration des données

## Utilisation

### Initialisation des permissions

Pour initialiser les permissions par défaut :

```bash
python manage.py initialize_permissions
```

Options disponibles :
- `--force` : Force la réinitialisation de toutes les permissions
- `--role admin` : Initialise seulement les permissions pour le rôle admin

### Vérification des permissions dans le code

#### Dans les vues

```python
from core.views import has_permission, require_permission

# Vérification simple
if has_permission(request.user, 'adherent_create'):
    # L'utilisateur peut créer des adhérents
    pass

# Décorateur pour les vues
@require_permission('adherent_create')
def adherent_create(request):
    # Cette vue nécessite la permission adherent_create
    pass

# Mixin pour les vues basées sur les classes
class AdherentCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'adherent_create'
    # ...
```

#### Dans les templates

```html
{% if user|has_permission:'adherent_create' %}
    <a href="{% url 'core:adherent_create' %}" class="btn btn-primary">
        Créer un adhérent
    </a>
{% endif %}
```

### Gestion des permissions via l'interface

1. **Accès** : Paramètres > Gestion des Rôles et Permissions
2. **Ajout** : Cliquer sur "Nouvelle Permission"
3. **Modification** : Cliquer sur l'icône de modification
4. **Suppression** : Cliquer sur l'icône de suppression
5. **Assignation en masse** : Utiliser "Assignation en masse"

## Configuration par défaut

### Administrateurs
- Toutes les permissions sont activées
- Accès complet à toutes les fonctionnalités

### Superviseurs
- Gestion des utilisateurs (agents seulement)
- Gestion complète des adhérents, organisations, interactions
- Gestion des badges et objectifs
- Accès en lecture aux paramètres
- Accès aux rapports et statistiques

### Agents
- Création et lecture des adhérents
- Création et lecture des organisations
- Création et lecture des interactions
- Lecture des badges et objectifs

## Avantages du système

### Flexibilité
- Permissions granulaires et configurables
- Activation/désactivation en temps réel
- Pas besoin de redéployer l'application

### Sécurité
- Contrôle d'accès précis
- Audit trail des modifications
- Séparation des responsabilités

### Maintenance
- Interface d'administration intuitive
- Assignation en masse pour gagner du temps
- Documentation automatique des permissions

## Cas d'usage

### Exemple 1 : Agent avec permissions étendues
Un agent expérimenté peut recevoir la permission `adherent_edit` pour modifier les informations des adhérents qu'il a créés.

### Exemple 2 : Superviseur avec accès limité
Un superviseur peut avoir la permission `user_view` désactivée pour ne pas voir la liste des utilisateurs.

### Exemple 3 : Permissions temporaires
Une permission peut être temporairement désactivée pour un rôle pendant une maintenance.

## Monitoring et audit

### Journal des modifications
Toutes les modifications de permissions sont enregistrées dans le journal système avec :
- Utilisateur qui a fait la modification
- Permission modifiée
- Ancienne et nouvelle valeur
- Horodatage

### Vérification des permissions
La page de profil utilisateur affiche toutes les permissions actives de l'utilisateur connecté.

## Dépannage

### Problèmes courants

1. **Permission refusée**
   - Vérifier que la permission existe pour le rôle
   - Vérifier que la permission est active
   - Vérifier que l'utilisateur a le bon rôle

2. **Permissions manquantes**
   - Exécuter `python manage.py initialize_permissions`
   - Vérifier la configuration dans l'interface d'administration

3. **Changements non pris en compte**
   - Vérifier que l'utilisateur s'est reconnecté
   - Vider le cache si nécessaire

### Commandes utiles

```bash
# Initialiser les permissions
python manage.py initialize_permissions

# Initialiser pour un rôle spécifique
python manage.py initialize_permissions --role agent

# Forcer la réinitialisation
python manage.py initialize_permissions --force

# Tester le système
python test_permissions_system.py
```

## Évolution du système

### Ajout de nouvelles permissions

1. Ajouter la permission dans `RolePermission.PERMISSION_CHOICES`
2. Mettre à jour la fonction `get_permission_category()`
3. Ajouter la vérification dans les vues concernées
4. Mettre à jour la documentation

### Migration des données

Les migrations automatiques gèrent l'ajout de nouvelles permissions. Les permissions existantes ne sont pas affectées.

## Conclusion

Le système de permissions dynamiques offre une flexibilité maximale pour la gestion des accès tout en maintenant la sécurité et la simplicité d'utilisation. Il permet aux administrateurs d'adapter précisément les permissions selon les besoins de l'organisation. 