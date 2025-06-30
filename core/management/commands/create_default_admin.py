from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée un superutilisateur par défaut pour le déploiement'

    def handle(self, *args, **options):
        # Vérifier si un superutilisateur existe déjà
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('Un superutilisateur existe déjà.')
            )
            return

        # Créer un superutilisateur par défaut
        try:
            admin_user = User.objects.create_superuser(
                email='admin@impactdata.com',
                matricule='ADMIN001',
                first_name='Admin',
                last_name='System',
                telephone='+1234567890',
                profession='Administrateur',
                role='admin'
            )
            
            # Définir un mot de passe simple pour le déploiement
            admin_user.set_password('admin123')
            admin_user.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Superutilisateur créé avec succès!\n'
                    f'Email: admin@impactdata.com\n'
                    f'Mot de passe: admin123\n'
                    f'Matricule: ADMIN001'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la création du superutilisateur: {str(e)}')
            ) 