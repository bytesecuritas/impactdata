from django.core.management.base import BaseCommand
from core.models import BadgeTemplate

class Command(BaseCommand):
    help = 'Initialise les templates de badges par défaut'

    def handle(self, *args, **options):
        templates_data = [
            {
                'name': 'Classique',
                'template_type': 'classic',
                'description': 'Design traditionnel avec un style professionnel et sobre. Parfait pour un usage officiel.',
                'is_active': True
            },
            {
                'name': 'Moderne',
                'template_type': 'modern',
                'description': 'Design contemporain avec des dégradés et des effets visuels modernes. Idéal pour un look dynamique.',
                'is_active': True
            },
            {
                'name': 'Premium',
                'template_type': 'premium',
                'description': 'Design luxueux avec des couleurs dorées et des effets premium. Parfait pour les VIP et événements spéciaux.',
                'is_active': True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates_data:
            template, created = BadgeTemplate.objects.get_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Template "{template.name}" créé')
                )
            else:
                # Mettre à jour si le template existe déjà
                for key, value in template_data.items():
                    setattr(template, key, value)
                template.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Template "{template.name}" mis à jour')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Initialisation terminée!\n'
                f'   Templates créés: {created_count}\n'
                f'   Templates mis à jour: {updated_count}\n'
                f'   Total: {BadgeTemplate.objects.count()} templates disponibles'
            )
        ) 