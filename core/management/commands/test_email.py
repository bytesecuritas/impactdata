from django.core.management.base import BaseCommand
from django.conf import settings
from core.services import EmailService


class Command(BaseCommand):
    help = 'Teste la configuration email en envoyant un email de test'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Adresse email de destination pour le test'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(
            self.style.SUCCESS(f'Envoi d\'un email de test à {email}...')
        )
        
        try:
            success = EmailService.send_test_email(email)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Email de test envoyé avec succès à {email}'
                    )
                )
                self.stdout.write(
                    self.style.WARNING(
                        'Vérifiez votre boîte de réception (et vos spams)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Échec de l\'envoi de l\'email de test à {email}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors de l\'envoi : {str(e)}')
            )
            
        # Afficher la configuration actuelle
        self.stdout.write('\n' + '='*50)
        self.stdout.write('CONFIGURATION EMAIL ACTUELLE :')
        self.stdout.write('='*50)
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        if not settings.EMAIL_HOST_USER:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  EMAIL_HOST_USER n\'est pas configuré. '
                    'L\'email sera affiché dans la console en mode développement.'
                )
            ) 