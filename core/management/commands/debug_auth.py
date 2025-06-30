from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()

class Command(BaseCommand):
    help = 'Diagnostique les problèmes d\'authentification et crée un utilisateur de test'

    def handle(self, *args, **options):
        self.stdout.write('=== Diagnostic d\'authentification ===')
        
        # 1. Vérifier la base de données
        self.stdout.write('\n1. Vérification de la base de données...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='core_user'")
                if cursor.fetchone():
                    self.stdout.write(self.style.SUCCESS('✓ Table core_user existe'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Table core_user n\'existe pas'))
                    return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur base de données: {str(e)}'))
            return
        
        # 2. Vérifier les utilisateurs existants
        self.stdout.write('\n2. Vérification des utilisateurs...')
        users = User.objects.all()
        self.stdout.write(f'Nombre d\'utilisateurs: {users.count()}')
        
        for user in users:
            self.stdout.write(f'  - {user.email} (rôle: {getattr(user, "role", "N/A")}, actif: {user.is_active})')
        
        # 3. Créer un utilisateur de test si aucun n'existe
        if users.count() == 0:
            self.stdout.write('\n3. Création d\'un utilisateur de test...')
            try:
                test_user = User.objects.create_user(
                    email='admin@impactdata.com',
                    matricule='ADMIN001',
                    first_name='Admin',
                    last_name='Test',
                    telephone='+1234567890',
                    profession='Administrateur',
                    role='admin'
                )
                test_user.set_password('admin123')
                test_user.is_staff = True
                test_user.is_superuser = True
                test_user.save()
                
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Utilisateur de test créé!\n'
                    f'  Email: admin@impactdata.com\n'
                    f'  Mot de passe: admin123\n'
                    f'  Matricule: ADMIN001'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Erreur création utilisateur: {str(e)}'))
        else:
            self.stdout.write('\n3. Utilisateurs existants trouvés, pas de création nécessaire.')
        
        # 4. Tester l'authentification
        self.stdout.write('\n4. Test d\'authentification...')
        try:
            from django.contrib.auth import authenticate
            test_email = 'admin@impactdata.com' if users.count() == 0 else users.first().email
            test_password = 'admin123' if users.count() == 0 else 'admin123'
            
            user = authenticate(username=test_email, password=test_password)
            if user:
                self.stdout.write(self.style.SUCCESS(f'✓ Authentification réussie pour {user.email}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Authentification échouée pour {test_email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erreur test authentification: {str(e)}'))
        
        self.stdout.write('\n=== Diagnostic terminé ===') 