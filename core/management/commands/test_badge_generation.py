from django.core.management.base import BaseCommand
from core.models import Adherent, BadgeTemplate, Badge
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Teste la génération de badge avec différents templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--adherent-id',
            type=int,
            help='ID de l\'adhérent pour lequel générer le badge'
        )

    def handle(self, *args, **options):
        adherent_id = options.get('adherent_id')
        
        if not adherent_id:
            # Utiliser le premier adhérent disponible
            adherent = Adherent.objects.first()
            if not adherent:
                self.stdout.write(
                    self.style.ERROR('❌ Aucun adhérent trouvé. Créez d\'abord un adhérent.')
                )
                return
        else:
            try:
                adherent = Adherent.objects.get(id=adherent_id)
            except Adherent.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Adhérent avec l\'ID {adherent_id} non trouvé.')
                )
                return
        
        # Vérifier que l'adhérent a les informations nécessaires
        if not adherent.activity_name or not adherent.badge_validity:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ L\'adhérent {adherent.full_name} n\'a pas les informations de badge complètes.\n'
                    f'   Activité: {adherent.activity_name or "Manquante"}\n'
                    f'   Validité: {adherent.badge_validity or "Manquante"}'
                )
            )
            return
        
        # Récupérer un utilisateur pour émettre le badge
        user = User.objects.first()
        if not user:
            self.stdout.write(
                self.style.ERROR('❌ Aucun utilisateur trouvé. Créez d\'abord un utilisateur.')
            )
            return
        
        # Récupérer les templates disponibles
        templates = BadgeTemplate.objects.filter(is_active=True)
        
        if not templates:
            self.stdout.write(
                self.style.ERROR('❌ Aucun template de badge actif trouvé.')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎯 Test de génération de badge pour {adherent.full_name}\n'
                f'   Activité: {adherent.activity_name}\n'
                f'   Validité: {adherent.badge_validity}\n'
                f'   Templates disponibles: {templates.count()}'
            )
        )
        
        # Générer un badge pour chaque template
        for template in templates:
            try:
                # Vérifier s'il existe déjà un badge actif pour cet adhérent
                existing_badge = Badge.objects.filter(
                    adherent=adherent, 
                    status='active'
                ).first()
                
                if existing_badge:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  Badge actif existant pour {adherent.full_name} (ID: {existing_badge.id})'
                        )
                    )
                    continue
                
                # Créer le badge
                badge = Badge.objects.create(
                    adherent=adherent,
                    issued_by=user,
                    template=template,
                    badge_validity=adherent.badge_validity,
                    activity_name=adherent.activity_name,
                    notes=f"Badge de test généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')} avec le template {template.name}"
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Badge généré avec le template "{template.name}":\n'
                        f'   Numéro: {badge.badge_number}\n'
                        f'   Template: {badge.template.name}\n'
                        f'   Statut: {badge.get_status_display()}'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur lors de la génération du badge avec {template.name}: {str(e)}')
                )
        
        # Afficher les badges générés
        badges = Badge.objects.filter(adherent=adherent).order_by('-issued_date')
        if badges:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📋 Badges générés pour {adherent.full_name}:'
                )
            )
            for badge in badges:
                self.stdout.write(
                    f'   - {badge.badge_number} ({badge.template.name if badge.template else "Sans template"}) - {badge.get_status_display()}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Test terminé! Vous pouvez maintenant:\n'
                f'   1. Voir les badges dans l\'interface web\n'
                f'   2. Tester les différents templates\n'
                f'   3. Télécharger les badges en PDF'
            )
        ) 