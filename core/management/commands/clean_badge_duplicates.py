from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import Badge


class Command(BaseCommand):
    help = 'Nettoie les doublons de badges en gardant le plus récent pour chaque numéro de badge'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans effectuer la suppression',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Recherche des doublons de badges...')
        )
        
        # Trouver les badge_number en doublon
        dupes = (
            Badge.objects.values('badge_number')
            .annotate(nb=Count('id'))
            .filter(nb__gt=1)
        )
        
        if not dupes:
            self.stdout.write(
                self.style.SUCCESS('✅ Aucun doublon de badge trouvé dans la base de données.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'⚠️  {len(dupes)} numéro(s) de badge avec des doublons trouvé(s).')
        )
        
        total_deleted = 0
        
        for d in dupes:
            badge_number = d['badge_number']
            badges = Badge.objects.filter(badge_number=badge_number).order_by('-issued_date', '-id')
            to_keep = badges.first()
            to_delete = badges.exclude(id=to_keep.id)
            
            self.stdout.write(
                f'📋 Badge {badge_number}:'
            )
            self.stdout.write(
                f'   ✅ Garde: Badge #{to_keep.id} (émis le {to_keep.issued_date.strftime("%d/%m/%Y")})'
            )
            
            for badge in to_delete:
                self.stdout.write(
                    f'   ❌ Supprime: Badge #{badge.id} (émis le {badge.issued_date.strftime("%d/%m/%Y")})'
                )
            
            if not dry_run:
                deleted_count = to_delete.count()
                to_delete.delete()
                total_deleted += deleted_count
                self.stdout.write(
                    self.style.SUCCESS(f'   🗑️  {deleted_count} badge(s) supprimé(s)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   🔍 {to_delete.count()} badge(s) seraient supprimés (mode dry-run)')
                )
            
            self.stdout.write('')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 Mode dry-run: Aucune suppression effectuée.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Nettoyage terminé! {total_deleted} badge(s) supprimé(s).')
            )
            
            # Vérification finale
            remaining_dupes = (
                Badge.objects.values('badge_number')
                .annotate(nb=Count('id'))
                .filter(nb__gt=1)
            )
            
            if not remaining_dupes:
                self.stdout.write(
                    self.style.SUCCESS('✅ Aucun doublon restant dans la base de données.')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {len(remaining_dupes)} doublon(s) restant(s) après nettoyage.')
                ) 