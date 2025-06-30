from django.core.management.base import BaseCommand
from core.models import Adherent
from django.utils import timezone
from django.db import models
from datetime import timedelta

class Command(BaseCommand):
    help = 'Met à jour les adhérents existants avec des informations de badge par défaut'

    def add_arguments(self, parser):
        parser.add_argument(
            '--default-activity',
            type=str,
            default='Membre',
            help='Activité par défaut pour les adhérents sans activité'
        )
        parser.add_argument(
            '--validity-days',
            type=int,
            default=365,
            help='Nombre de jours de validité par défaut'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Afficher ce qui serait fait sans effectuer les modifications'
        )

    def handle(self, *args, **options):
        default_activity = options['default_activity']
        validity_days = options['validity_days']
        dry_run = options['dry_run']
        
        # Trouver les adhérents sans activité ou validité de badge
        adherents_to_update = Adherent.objects.filter(
            models.Q(activity_name__isnull=True) | 
            models.Q(activity_name='') |
            models.Q(badge_validity__isnull=True)
        )
        
        if not adherents_to_update:
            self.stdout.write(
                self.style.SUCCESS('✅ Tous les adhérents ont déjà les informations de badge complètes.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'📋 {adherents_to_update.count()} adhérent(s) à mettre à jour avec:\n'
                f'   Activité par défaut: {default_activity}\n'
                f'   Validité: {validity_days} jours\n'
                f'   Mode: {"Simulation" if dry_run else "Mise à jour réelle"}'
            )
        )
        
        updated_count = 0
        default_validity = timezone.now().date() + timedelta(days=validity_days)
        
        for adherent in adherents_to_update:
            needs_update = False
            updates = []
            
            # Vérifier l'activité
            if not adherent.activity_name:
                needs_update = True
                updates.append(f"activité: '{default_activity}'")
                if not dry_run:
                    adherent.activity_name = default_activity
            
            # Vérifier la validité
            if not adherent.badge_validity:
                needs_update = True
                updates.append(f"validité: {default_validity}")
                if not dry_run:
                    adherent.badge_validity = default_validity
            
            if needs_update:
                if dry_run:
                    self.stdout.write(
                        f'🔄 {adherent.full_name} (ID: {adherent.id}) - {", ".join(updates)}'
                    )
                else:
                    adherent.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {adherent.full_name} mis à jour - {", ".join(updates)}'
                        )
                    )
                updated_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n📊 Simulation terminée:\n'
                    f'   Adhérents qui seraient mis à jour: {updated_count}\n'
                    f'   Pour effectuer les mises à jour, relancez la commande sans --dry-run'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Mise à jour terminée!\n'
                    f'   Adhérents mis à jour: {updated_count}\n'
                    f'   Tous les adhérents ont maintenant les informations de badge complètes.'
                )
            ) 