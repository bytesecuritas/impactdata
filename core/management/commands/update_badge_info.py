from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import date, timedelta
from core.models import Adherent

class Command(BaseCommand):
    help = 'Met à jour les informations de badge d\'un adhérent'

    def add_arguments(self, parser):
        parser.add_argument('adherent_id', type=int, help='ID de l\'adhérent')
        parser.add_argument('activity_name', type=str, help='Nom de l\'activité')
        parser.add_argument(
            '--validity-days',
            type=int,
            default=365,
            help='Nombre de jours de validité (défaut: 365)'
        )

    def handle(self, *args, **options):
        adherent_id = options['adherent_id']
        activity_name = options['activity_name']
        validity_days = options['validity_days']

        try:
            adherent = Adherent.objects.get(id=adherent_id)
            
            # Calculer la date de validité
            badge_validity = date.today() + timedelta(days=validity_days)
            
            # Mettre à jour les informations
            adherent.activity_name = activity_name
            adherent.badge_validity = badge_validity
            adherent.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Adhérent {adherent.full_name} mis à jour avec succès!\n'
                    f'   Activité: {activity_name}\n'
                    f'   Validité: {badge_validity}'
                )
            )
            
        except Adherent.DoesNotExist:
            raise CommandError(f'Aucun adhérent trouvé avec l\'ID {adherent_id}')
        except Exception as e:
            raise CommandError(f'Erreur lors de la mise à jour: {str(e)}') 