from core.models import Adherent, Badge
from django.core.management.base import BaseCommand
from django.utils import timezone
import qrcode
from io import BytesIO
from django.core.files import File


class Command(BaseCommand):
    help = 'Test de génération de badges pour les adhérents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--adherent-id',
            type=int,
            help='ID de l\'adhérent pour lequel générer un badge'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Générer des badges pour tous les adhérents sans badge'
        )

    def handle(self, *args, **options):
        if options['adherent_id']:
            # Générer un badge pour un adhérent spécifique
            try:
                adherent = Adherent.objects.get(id=options['adherent_id'])
                self.generate_badge_for_adherent(adherent)
            except Adherent.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Adhérent avec ID {options["adherent_id"]} non trouvé')
                )
        elif options['all']:
            # Générer des badges pour tous les adhérents sans badge
            adherents_without_badge = Adherent.objects.filter(badges__isnull=True)
            
            if not adherents_without_badge.exists():
                self.stdout.write(
                    self.style.WARNING('Tous les adhérents ont déjà des badges')
                )
                return
        
            self.stdout.write(
                f'Génération de badges pour {adherents_without_badge.count()} adhérents...'
            )
            
            for adherent in adherents_without_badge:
                self.generate_badge_for_adherent(adherent)
                
            self.stdout.write(
                self.style.SUCCESS('Génération terminée!')
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    'Veuillez spécifier --adherent-id ou --all'
                )
            )

    def generate_badge_for_adherent(self, adherent):
        """Génère un badge pour un adhérent spécifique"""
            try:
            # Vérifier si l'adhérent a déjà un badge actif
                existing_badge = Badge.objects.filter(
                    adherent=adherent, 
                    status='active'
                ).first()
                
                if existing_badge:
                    self.stdout.write(
                        self.style.WARNING(
                        f'L\'adhérent {adherent.full_name} a déjà un badge actif: {existing_badge.badge_number}'
                    )
                )
                return
                
                # Créer le badge
                badge = Badge.objects.create(
                    adherent=adherent,
                activity_name=adherent.activity_name or "Activité non spécifiée",
                badge_validity=adherent.badge_validity or timezone.now().date(),
                notes="Badge généré automatiquement par la commande de test"
                )
                
            # Générer le QR code
            qr_data = f"BADGE:{badge.badge_number}:{adherent.identifiant}"
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            qr_image.save(buffer, format='PNG')
            
            # Sauvegarder le QR code
            badge.qr_code.save(
                f'qr_code_{badge.badge_number}.png',
                File(buffer),
                save=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Badge généré pour {adherent.full_name}: {badge.badge_number}'
                )
            )
            
        except Exception as e:
                self.stdout.write(
                self.style.ERROR(
                    f'❌ Erreur lors de la génération du badge pour {adherent.full_name}: {str(e)}'
            )
        ) 