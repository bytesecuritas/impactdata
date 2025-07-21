# Configuration SMTP Temporairement Désactivée

## Statut Actuel
Le SMTP a été temporairement désactivé pour permettre le lancement du projet en développement.

## Modifications Apportées

### Fichier : `impactData/settings.py`

**Configuration SMTP originale (commentée) :**
```python
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
# EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
# EMAIL_USE_SSL = config('EMAIL_USE_SSL', cast=bool)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
# DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
```

**Configuration temporaire (active) :**
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'noreply@impactdata.local'
```

## Conséquences

### ✅ Avantages
- Le projet peut démarrer sans erreurs SMTP
- Les emails sont affichés dans la console Django
- Pas besoin de configuration SMTP complexe

### ⚠️ Limitations
- Les emails ne sont pas réellement envoyés
- Ils apparaissent seulement dans la console de développement
- Fonctionnalités d'email non disponibles

## Pour Réactiver le SMTP

1. **Décommenter** la configuration SMTP originale dans `settings.py`
2. **Commenter** la configuration temporaire
3. **Configurer** les variables d'environnement dans `.env` :
   ```
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_SSL=True
   EMAIL_HOST_USER=votre_email@gmail.com
   EMAIL_HOST_PASSWORD=votre_mot_de_passe_app
   DEFAULT_FROM_EMAIL=votre_email@gmail.com
   ```

## Test des Emails

Avec la configuration actuelle, les emails apparaîtront dans la console Django lors du lancement du serveur. Exemple :
```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: Test de configuration email - Impact Data Platform
From: noreply@impactdata.local
To: test@example.com
Date: ...

Ceci est un email de test pour vérifier la configuration email.
```

## Date de Modification
- **Date** : $(date)
- **Raison** : Permettre le lancement du projet sans configuration SMTP
- **Statut** : Temporaire 