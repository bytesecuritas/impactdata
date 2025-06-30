from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import Adherent


class Command(BaseCommand):
    help = 'Corrige les doublons d\'identifiants d\'adhérents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait corrigé sans effectuer les changements',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('🔧 Correction des doublons d\'identifiants d\'adhérents...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 Mode dry-run: Aucun changement ne sera effectué')
            )
        
        # Trouver les identifiants en doublon
        dupes = (
            Adherent.objects.values('identifiant')
            .annotate(nb=Count('id'))
            .filter(nb__gt=1)
        )
        
        if not dupes:
            self.stdout.write(
                self.style.SUCCESS('✅ Aucun doublon d\'identifiant trouvé.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'⚠️  {len(dupes)} identifiant(s) avec des doublons trouvé(s).')
        )
        
        total_fixed = 0
        
        for d in dupes:
            identifiant = d['identifiant']
            adherents = Adherent.objects.filter(identifiant=identifiant).order_by('-created_at', '-id')
            to_keep = adherents.first()
            to_fix = adherents.exclude(id=to_keep.id)
            
            self.stdout.write(f'\n📋 Identifiant {identifiant}:')
            self.stdout.write(f'   ✅ Garde: {to_keep.full_name} (créé le {to_keep.created_at.strftime("%d/%m/%Y")})')
            
            for adherent in to_fix:
                self.stdout.write(f'   🔧 Corrige: {adherent.full_name} (créé le {adherent.created_at.strftime("%d/%m/%Y")})')
                
                if not dry_run:
                    # Régénérer l'identifiant pour cet adhérent
                    old_identifiant = adherent.identifiant
                    adherent.generate_identifiant()
                    adherent.save()
                    self.stdout.write(f'      → Nouvel identifiant: {adherent.identifiant}')
                    total_fixed += 1
                else:
                    self.stdout.write(f'      → Serait corrigé (mode dry-run)')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n🔍 Mode dry-run: {total_fixed} adhérent(s) seraient corrigés')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Correction terminée! {total_fixed} adhérent(s) corrigé(s).')
            )
            
            # Vérification finale
            remaining_dupes = (
                Adherent.objects.values('identifiant')
                .annotate(nb=Count('id'))
                .filter(nb__gt=1)
            )
            
            if not remaining_dupes:
                self.stdout.write(
                    self.style.SUCCESS('✅ Aucun doublon restant dans la base de données.')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {len(remaining_dupes)} doublon(s) restant(s) après correction.')
                ) 