# Guide de Gestion des Badges - Impact Data

## Vue d'ensemble

Ce guide explique comment gérer les badges des adhérents dans le système Impact Data.

## Prérequis pour la génération d'un badge

Avant de pouvoir générer un badge pour un adhérent, vous devez renseigner deux informations obligatoires :

1. **Nom de l'activité** (`activity_name`) : L'activité principale de l'adhérent
2. **Validité du badge** (`badge_validity`) : La date jusqu'à laquelle le badge sera valide

## Commandes de gestion des badges

### 1. Lister tous les adhérents avec leurs informations de badge

```bash
python manage.py list_adherents_badge
```

### 2. Lister seulement les adhérents avec des informations manquantes

```bash
python manage.py list_adherents_badge --missing-info
```

### 3. Mettre à jour les informations de badge d'un adhérent

```bash
python manage.py update_badge_info <adherent_id> "<activity_name>" [--validity-days <jours>]
```

**Exemples :**
```bash
# Mise à jour avec validité par défaut (1 an)
python manage.py update_badge_info 1 "Macanier"

# Mise à jour avec validité personnalisée (6 mois)
python manage.py update_badge_info 1 "Commerçant" --validity-days 180

# Mise à jour avec validité de 2 ans
python manage.py update_badge_info 1 "Artisan" --validity-days 730
```

## Processus de génération d'un badge

### Étape 1 : Vérifier les informations de l'adhérent

1. Allez dans la section "Adhérents" de l'interface web
2. Cliquez sur l'adhérent concerné
3. Vérifiez que les champs "Nom de l'activité" et "Validité du badge" sont renseignés

### Étape 2 : Mettre à jour les informations si nécessaire

Si les informations sont manquantes, vous pouvez :

**Option A : Via l'interface web**
1. Cliquez sur "Modifier" dans la page de détail de l'adhérent
2. Remplissez les champs "Nom de l'activité" et "Validité du badge"
3. Sauvegardez

**Option B : Via la ligne de commande**
```bash
python manage.py update_badge_info <adherent_id> "<activity_name>"
```

### Étape 3 : Générer le badge

1. Retournez à la page de détail de l'adhérent
2. Cliquez sur le bouton "Générer un badge"
3. Le badge sera créé avec un QR code unique

## Gestion des badges existants

### Voir tous les badges
- Allez dans la section "Badges" de l'interface web

### Voir un badge spécifique
- Cliquez sur un badge dans la liste pour voir ses détails

### Télécharger un badge en PDF
- Dans la page de détail d'un badge, cliquez sur "Télécharger PDF"

### Révoquer un badge
- Dans la page de détail d'un badge, cliquez sur "Révoquer"
- Donnez une raison pour la révocation

### Réactiver un badge révoqué
- Dans la page de détail d'un badge révoqué, cliquez sur "Réactiver"

## Dépannage

### Erreur : "Veuillez d'abord renseigner l'activité et la validité du badge"

**Solution :**
1. Vérifiez que l'adhérent a bien un nom d'activité renseigné
2. Vérifiez que l'adhérent a bien une date de validité de badge renseignée
3. Utilisez la commande de mise à jour si nécessaire

### Erreur : "L'adhérent a déjà un badge actif valide"

**Solution :**
1. Vérifiez les badges existants de l'adhérent
2. Si le badge est expiré, vous pouvez en créer un nouveau
3. Si le badge est toujours valide, vous devez d'abord le révoquer

### Erreur lors de la génération du QR code

**Solution :**
1. Vérifiez que le dossier `media/badge_qr_codes/` existe et est accessible en écriture
2. Vérifiez les permissions du dossier media
3. Redémarrez le serveur Django

## Bonnes pratiques

1. **Nom de l'activité** : Utilisez des noms clairs et descriptifs (ex: "Macanier", "Commerçant", "Artisan")
2. **Validité du badge** : Généralement 1 an, mais peut varier selon les besoins
3. **Vérification régulière** : Utilisez la commande `list_adherents_badge` pour vérifier l'état des informations
4. **Sauvegarde** : Sauvegardez régulièrement la base de données

## Support

Pour toute question ou problème, consultez :
- Les logs Django pour les erreurs techniques
- La documentation Django pour les questions générales
- L'équipe de développement pour les problèmes spécifiques 