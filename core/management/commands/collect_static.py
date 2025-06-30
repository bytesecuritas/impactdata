from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import shutil

class Command(BaseCommand):
    help = 'Collect static files and organize them for deployment'

    def handle(self, *args, **options):
        self.stdout.write('Collecting static files...')
        
        # Créer le répertoire staticfiles s'il n'existe pas
        static_root = settings.STATIC_ROOT
        if not os.path.exists(static_root):
            os.makedirs(static_root)
        
        # Copier les fichiers statiques de l'application core
        core_static_dir = os.path.join(settings.BASE_DIR, 'core', 'static')
        if os.path.exists(core_static_dir):
            for root, dirs, files in os.walk(core_static_dir):
                for file in files:
                    # Calculer le chemin relatif
                    rel_path = os.path.relpath(root, core_static_dir)
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(static_root, rel_path, file)
                    
                    # Créer le répertoire de destination s'il n'existe pas
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    
                    # Copier le fichier
                    shutil.copy2(src_file, dst_file)
                    self.stdout.write(f'Copied: {src_file} -> {dst_file}')
        
        self.stdout.write(self.style.SUCCESS('Static files collected successfully!')) 