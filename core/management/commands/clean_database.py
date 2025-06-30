from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.db import transaction
from core.models import Badge, Adherent, Organization, User, Interaction, UserObjective, SupervisorStats


class Command(BaseCommand):
    help = 'Nettoie complètement la base de données (doublons, données orphelines, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans effectuer la suppression',
        )
        parser.add_argument(
            '--badges-only',
            action='store_true',
            help='Nettoie seulement les badges',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        badges_only = options['badges_only']
        
        self.stdout.write(
            self.style.SUCCESS('🧹 Début du nettoyage de la base de données...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 Mode dry-run: Aucune suppression ne sera effectuée')
            )
        
        total_deleted = 0
        
        # 1. Nettoyer les doublons de badges
        total_deleted += self.clean_badge_duplicates(dry_run)
        
        if not badges_only:
            # 2. Nettoyer les données orphelines
            total_deleted += self.clean_orphaned_data(dry_run)
            
            # 3. Nettoyer les interactions expirées
            total_deleted += self.clean_expired_interactions(dry_run)
            
            # 4. Nettoyer les objectifs obsolètes
            total_deleted += self.clean_obsolete_objectives(dry_run)
            
            # 5. Nettoyer les statistiques obsolètes
            total_deleted += self.clean_obsolete_stats(dry_run)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 Mode dry-run: {total_deleted} élément(s) seraient supprimés')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Nettoyage terminé! {total_deleted} élément(s) supprimé(s).')
            )

    def clean_badge_duplicates(self, dry_run):
        """Nettoie les doublons de badges"""
        self.stdout.write('\n📋 Nettoyage des doublons de badges...')
        
        dupes = (
            Badge.objects.values('badge_number')
            .annotate(nb=Count('id'))
            .filter(nb__gt=1)
        )
        
        deleted_count = 0
        
        for d in dupes:
            badge_number = d['badge_number']
            badges = Badge.objects.filter(badge_number=badge_number).order_by('-issued_date', '-id')
            to_keep = badges.first()
            to_delete = badges.exclude(id=to_keep.id)
            
            self.stdout.write(f'   Badge {badge_number}: garde #{to_keep.id}, supprime {to_delete.count()} doublon(s)')
            
            if not dry_run:
                deleted_count += to_delete.count()
                to_delete.delete()
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {deleted_count} doublon(s) de badge supprimé(s)')
            )
        else:
            self.stdout.write('   ✅ Aucun doublon de badge trouvé')
        
        return deleted_count

    def clean_orphaned_data(self, dry_run):
        """Nettoie les données orphelines"""
        self.stdout.write('\n🔗 Nettoyage des données orphelines...')
        
        deleted_count = 0
        
        # Badges sans adhérent
        orphaned_badges = Badge.objects.filter(adherent__isnull=True)
        if orphaned_badges.exists():
            self.stdout.write(f'   Badges sans adhérent: {orphaned_badges.count()}')
            if not dry_run:
                deleted_count += orphaned_badges.count()
                orphaned_badges.delete()
        
        # Adhérents sans organisation
        orphaned_adherents = Adherent.objects.filter(organisation__isnull=True)
        if orphaned_adherents.exists():
            self.stdout.write(f'   Adhérents sans organisation: {orphaned_adherents.count()}')
            if not dry_run:
                deleted_count += orphaned_adherents.count()
                orphaned_adherents.delete()
        
        # Interactions sans personnel ou adhérent
        orphaned_interactions = Interaction.objects.filter(
            Q(personnel__isnull=True) | Q(adherent__isnull=True)
        )
        if orphaned_interactions.exists():
            self.stdout.write(f'   Interactions orphelines: {orphaned_interactions.count()}')
            if not dry_run:
                deleted_count += orphaned_interactions.count()
                orphaned_interactions.delete()
        
        # Objectifs sans utilisateur
        orphaned_objectives = UserObjective.objects.filter(user__isnull=True)
        if orphaned_objectives.exists():
            self.stdout.write(f'   Objectifs sans utilisateur: {orphaned_objectives.count()}')
            if not dry_run:
                deleted_count += orphaned_objectives.count()
                orphaned_objectives.delete()
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'   ✅ {deleted_count} donnée(s) orpheline(s) supprimée(s)')
            )
        else:
            self.stdout.write('   ✅ Aucune donnée orpheline trouvée')
        
        return deleted_count

    def clean_expired_interactions(self, dry_run):
        """Nettoie les interactions expirées depuis plus de 30 jours"""
        self.stdout.write('\n⏰ Nettoyage des interactions expirées...')
        
        from django.utils import timezone
        from datetime import timedelta
        
        expired_date = timezone.now() - timedelta(days=30)
        expired_interactions = Interaction.objects.filter(
            due_date__lt=expired_date,
            status__in=['completed', 'cancelled']
        )
        
        deleted_count = expired_interactions.count()
        
        if deleted_count > 0:
            self.stdout.write(f'   Interactions expirées: {deleted_count}')
            if not dry_run:
                expired_interactions.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ {deleted_count} interaction(s) expirée(s) supprimée(s)')
                )
        else:
            self.stdout.write('   ✅ Aucune interaction expirée trouvée')
        
        return deleted_count

    def clean_obsolete_objectives(self, dry_run):
        """Nettoie les objectifs obsolètes (échoués depuis plus de 90 jours)"""
        self.stdout.write('\n🎯 Nettoyage des objectifs obsolètes...')
        
        from django.utils import timezone
        from datetime import timedelta
        
        obsolete_date = timezone.now() - timedelta(days=90)
        obsolete_objectives = UserObjective.objects.filter(
            status='failed',
            deadline__lt=obsolete_date
        )
        
        deleted_count = obsolete_objectives.count()
        
        if deleted_count > 0:
            self.stdout.write(f'   Objectifs obsolètes: {deleted_count}')
            if not dry_run:
                obsolete_objectives.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ {deleted_count} objectif(s) obsolète(s) supprimé(s)')
                )
        else:
            self.stdout.write('   ✅ Aucun objectif obsolète trouvé')
        
        return deleted_count

    def clean_obsolete_stats(self, dry_run):
        """Nettoie les statistiques obsolètes (plus de 6 mois)"""
        self.stdout.write('\n📊 Nettoyage des statistiques obsolètes...')
        
        from django.utils import timezone
        from datetime import timedelta
        
        obsolete_date = timezone.now() - timedelta(days=180)
        obsolete_stats = SupervisorStats.objects.filter(
            last_updated__lt=obsolete_date
        )
        
        deleted_count = obsolete_stats.count()
        
        if deleted_count > 0:
            self.stdout.write(f'   Statistiques obsolètes: {deleted_count}')
            if not dry_run:
                obsolete_stats.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ {deleted_count} statistique(s) obsolète(s) supprimée(s)')
                )
        else:
            self.stdout.write('   ✅ Aucune statistique obsolète trouvée')
        
        return deleted_count 