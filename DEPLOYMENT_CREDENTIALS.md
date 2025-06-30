# Identifiants de Déploiement

## Superutilisateur par Défaut

Lors du premier déploiement, un superutilisateur est automatiquement créé avec les identifiants suivants :

### Identifiants de Connexion
- **Email** : `admin@impactdata.com`
- **Mot de passe** : `admin123`
- **Matricule** : `ADMIN001`

### Informations du Compte
- **Nom** : Admin System
- **Rôle** : Administrateur
- **Téléphone** : +1234567890
- **Profession** : Administrateur

## Sécurité

⚠️ **IMPORTANT** : Ces identifiants sont pour le déploiement initial uniquement.

### Actions Recommandées après le Premier Déploiement

1. **Se connecter** avec les identifiants par défaut
2. **Changer le mot de passe** immédiatement
3. **Modifier les informations** du compte si nécessaire
4. **Créer d'autres utilisateurs** selon vos besoins

### Changement de Mot de Passe

1. Se connecter à l'application
2. Aller dans "Profil" → "Changer le mot de passe"
3. Entrer l'ancien mot de passe : `admin123`
4. Entrer le nouveau mot de passe sécurisé
5. Confirmer le nouveau mot de passe

## Accès à l'Administration Django

- **URL** : `https://votre-app.onrender.com/admin/`
- **Email** : `admin@impactdata.com`
- **Mot de passe** : `admin123` (ou le nouveau mot de passe)

## Support

En cas de problème d'accès :
1. Vérifier les logs de déploiement sur Render
2. S'assurer que la commande `create_default_admin` s'est exécutée
3. Contacter l'équipe de développement si nécessaire 