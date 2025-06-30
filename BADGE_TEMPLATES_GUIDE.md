# Guide des Templates de Badges - Impact Data

## Vue d'ensemble

Le système Impact Data propose 3 designs de badges différents pour répondre à tous les besoins et préférences visuelles.

## Les 3 Templates Disponibles

### 🎨 Template Classique
- **Style :** Professionnel et sobre
- **Couleurs :** Gris et blanc
- **Typographie :** Times New Roman
- **Usage :** Officiel, administratif
- **Caractéristiques :**
  - Design épuré et traditionnel
  - Bordure simple
  - Couleurs neutres
  - Parfait pour un usage professionnel

### 🌟 Template Moderne
- **Style :** Contemporain et dynamique
- **Couleurs :** Dégradé bleu-violet
- **Typographie :** Segoe UI
- **Usage :** Événements, présentations
- **Caractéristiques :**
  - Dégradés colorés
  - Effets de transparence
  - Animations au survol
  - Look moderne et attractif

### 👑 Template Premium
- **Style :** Luxueux et élégant
- **Couleurs :** Doré et beige
- **Typographie :** Georgia
- **Usage :** VIP, événements spéciaux
- **Caractéristiques :**
  - Bordures dorées
  - Étoile décorative
  - Effets de profondeur
  - Aspect premium

## Comment Choisir un Template

### 1. Via l'Interface Web
1. Allez sur la page de détail d'un adhérent
2. Cliquez sur "Générer un badge"
3. Choisissez le template souhaité
4. Cliquez sur "Générer le badge"

### 2. Facteurs de Choix
- **Usage :** Officiel → Classique, Événement → Moderne, VIP → Premium
- **Public :** Personnel → Classique, Clients → Moderne, Partenaires → Premium
- **Budget :** Standard → Classique/Moderne, Premium → Premium
- **Image :** Sérieuse → Classique, Innovante → Moderne, Luxueuse → Premium

## Personnalisation des Templates

### Ajouter un Nouveau Template
1. Créez un nouveau template dans l'admin Django
2. Ajoutez les styles CSS correspondants
3. Testez le template

### Modifier un Template Existant
1. Éditez le template dans l'admin
2. Modifiez les styles CSS
3. Mettez à jour la description

## Commandes de Gestion

### Lister les Templates
```bash
python manage.py shell -c "from core.models import BadgeTemplate; [print(f'{t.name}: {t.description}') for t in BadgeTemplate.objects.all()]"
```

### Créer un Template Personnalisé
```python
from core.models import BadgeTemplate

template = BadgeTemplate.objects.create(
    name="Mon Template",
    template_type="custom",
    description="Description du template",
    is_active=True
)
```

### Désactiver un Template
```python
template = BadgeTemplate.objects.get(name="Template à désactiver")
template.is_active = False
template.save()
```

## Styles CSS Personnalisés

### Structure des Classes
```css
.badge-template-[type] {
    /* Styles principaux */
}

.badge-template-[type] .badge-header {
    /* En-tête */
}

.badge-template-[type] .badge-content {
    /* Contenu */
}

.badge-template-[type] .badge-field {
    /* Champs individuels */
}
```

### Variables CSS Utiles
```css
:root {
    --classic-primary: #6c757d;
    --modern-primary: #667eea;
    --premium-primary: #d4af37;
}
```

## Bonnes Pratiques

### 1. Cohérence Visuelle
- Utilisez le même template pour un même type d'événement
- Maintenez une cohérence dans votre organisation

### 2. Accessibilité
- Assurez-vous que les contrastes sont suffisants
- Testez l'impression en noir et blanc

### 3. Performance
- Optimisez les images
- Utilisez des formats web appropriés

### 4. Responsive Design
- Testez sur différents écrans
- Vérifiez l'affichage mobile

## Dépannage

### Template non affiché
1. Vérifiez que le template est actif
2. Vérifiez les styles CSS
3. Videz le cache du navigateur

### Styles non appliqués
1. Vérifiez le chargement du CSS
2. Vérifiez les classes CSS
3. Inspectez les éléments

### Problème d'impression
1. Testez l'impression
2. Ajustez les styles d'impression
3. Vérifiez la taille du papier

## Support

Pour toute question ou problème :
- Consultez la documentation CSS
- Vérifiez les logs Django
- Contactez l'équipe de développement

## Évolutions Futures

### Templates Prévus
- Template Saisonnier (Noël, été, etc.)
- Template Corporate (avec logo)
- Template Minimaliste
- Template Coloré

### Fonctionnalités
- Éditeur de templates visuel
- Prévisualisation en temps réel
- Export en différents formats
- Intégration avec des outils de design 