from django.core.management.base import BaseCommand
from core.models import Adherent
from django.db import models

class Command(BaseCommand):
    help = 'Liste les adhérents avec leurs informations de badge'

    def add_arguments(self, parser):
        parser.add_argument(
            '--missing-info',
            action='store_true',
            help='Afficher seulement les adhérents sans activité ou validité de badge'
        )

    def handle(self, *args, **options):
        adherents = Adherent.objects.all()
        
        if options['missing_info']:
            adherents = adherents.filter(
                models.Q(activity_name__isnull=True) | 
                models.Q(activity_name='') |
                models.Q(badge_validity__isnull=True)
            )
        
        if not adherents:
            self.stdout.write(
                self.style.WARNING('Aucun adhérent trouvé.')
            )
            return
        
        self.stdout.write('\n📋 Liste des adhérents:')
        self.stdout.write('-' * 80)
        self.stdout.write(f"{'ID':<5} {'Nom complet':<30} {'Activité':<20} {'Validité badge':<15}")
        self.stdout.write('-' * 80)
        
        for adherent in adherents:
            activity = adherent.activity_name or "Non renseignée"
            validity = adherent.badge_validity.strftime('%d/%m/%Y') if adherent.badge_validity else "Non renseignée"
            
            # Colorer les lignes selon l'état des informations
            if adherent.activity_name and adherent.badge_validity:
                style = self.style.SUCCESS
            else:
                style = self.style.WARNING
            
            self.stdout.write(
                style(f"{adherent.id:<5} {adherent.full_name:<30} {activity:<20} {validity:<15}")
            )
        
        self.stdout.write('-' * 80)
        
        # Statistiques
        total = Adherent.objects.count()
        complete = Adherent.objects.filter(
            activity_name__isnull=False,
            activity_name__gt='',
            badge_validity__isnull=False
        ).count()
        incomplete = total - complete
        
        self.stdout.write(f'\n📊 Statistiques:')
        self.stdout.write(f'   Total: {total}')
        self.stdout.write(f'   Informations complètes: {complete}')
        self.stdout.write(f'   Informations manquantes: {incomplete}')
        
        if incomplete > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  {incomplete} adhérent(s) ont des informations de badge manquantes.'
                )
            ) 