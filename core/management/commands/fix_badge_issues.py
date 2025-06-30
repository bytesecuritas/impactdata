from django.core.management.base import BaseCommand
from django.db.models import Count
from core.models import Badge, Adherent


class Command(BaseCommand):
    help = 'Corrige tous les problèmes de badges (doublons, multiples actifs, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait corrigé sans effectuer les changements',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('🔧 Correction des problèmes de badges...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 Mode dry-run: Aucun changement ne sera effectué')
            )
        
        total_fixed = 0
        
        # 1. Supprimer les doublons de badge_number
        total_fixed += self.fix_badge_number_duplicates(dry_run)
        
        # 2. S'assurer qu'il n'y a qu'un seul badge actif par adhérent
        total_fixed += self.fix_multiple_active_badges(dry_run)
        
        # 3. Nettoyer les badges orphelins
        total_fixed += self.fix_orphaned_badges(dry_run)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 Mode dry-run: {total_fixed} problème(s) seraient corrigés')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Correction terminée! {total_fixed} problème(s) corrigé(s).')
            )

    def fix_badge_number_duplicates(self, dry_run):
        """Supprime les doublons de badge_number"""
        self.stdout.write('\n📋 Correction des doublons de badge_number...')
        
        dupes = (
            Badge.objects.values('badge_number')
            .annotate(nb=Count('id'))
            .filter(nb__gt=1)
        )
        
        fixed_count = 0
        
        for d in dupes:
            badge_number = d['badge_number']
            badges = Badge.objects.filter(badge_number=badge_number).order_by('-issued_date', '-id')
            to_keep = badges.first()
            to_delete = badges.exclude(id=to_keep.id)
            
            self.stdout.write(f'   Badge {badge_number}: garde #{to_keep.id}, supprime {to_delete.count()} doublon(s)')
            
            if not dry_run:
                fixed_count += to_delete.count()
                to_delete.delete()
        
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {fixed_count} doublon(s) de badge_number supprimé(s)')
            )
        else:
            self.stdout.write('   ✅ Aucun doublon de badge_number trouvé')
        
        return fixed_count

    def fix_multiple_active_badges(self, dry_run):
        """S'assure qu'il n'y a qu'un seul badge actif par adhérent"""
        self.stdout.write('\n🔄 Correction des multiples badges actifs par adhérent...')
        
        # Trouver les adhérents avec plusieurs badges actifs
        adherents_with_multiple_active = (
            Badge.objects.filter(status='active')
            .values('adherent__id')
            .annotate(nb=Count('id'))
            .filter(nb__gt=1)
        )
        
        fixed_count = 0
        
        for item in adherents_with_multiple_active:
            adherent_id = item['adherent__id']
            adherent = Adherent.objects.get(id=adherent_id)
            active_badges = Badge.objects.filter(adherent=adherent, status='active').order_by('-issued_date', '-id')
            
            # Garder le plus récent, révoquer les autres
            to_keep = active_badges.first()
            to_revoke = active_badges.exclude(id=to_keep.id)
            
            self.stdout.write(f'   Adhérent {adherent.full_name}: garde #{to_keep.id}, révoque {to_revoke.count()} badge(s)')
            
            if not dry_run:
                for badge in to_revoke:
                    badge.revoke(reason="Correction automatique - multiple badges actifs", revoked_by="Système")
                fixed_count += to_revoke.count()
        
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {fixed_count} badge(s) actif(s) révoqué(s)')
            )
        else:
            self.stdout.write('   ✅ Aucun multiple badge actif trouvé')
        
        return fixed_count

    def fix_orphaned_badges(self, dry_run):
        """Supprime les badges sans adhérent"""
        self.stdout.write('\n🔗 Correction des badges orphelins...')
        
        orphaned_badges = Badge.objects.filter(adherent__isnull=True)
        fixed_count = orphaned_badges.count()
        
        if fixed_count > 0:
            self.stdout.write(f'   Badges sans adhérent: {fixed_count}')
            if not dry_run:
                orphaned_badges.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ {fixed_count} badge(s) orphelin(s) supprimé(s)')
                )
        else:
            self.stdout.write('   ✅ Aucun badge orphelin trouvé')
        
        return fixed_count 