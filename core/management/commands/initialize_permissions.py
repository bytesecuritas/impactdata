from django.core.management.base import BaseCommand
from core.models import RolePermission, User
from django.db import transaction


class Command(BaseCommand):
    help = 'Initialise les permissions par défaut pour tous les rôles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la réinitialisation de toutes les permissions',
        )
        parser.add_argument(
            '--role',
            type=str,
            choices=['admin', 'superviseur', 'agent'],
            help='Initialise les permissions pour un rôle spécifique seulement',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔐 Initialisation des permissions par défaut...')
        )

        # Permissions par défaut pour chaque rôle
        default_permissions = {
            'admin': [
                # Gestion des utilisateurs
                'user_create', 'user_edit', 'user_delete', 'user_view', 'user_activate',
                # Gestion des adhérents
                'adherent_create', 'adherent_edit', 'adherent_delete', 'adherent_view',
                # Gestion des organisations
                'organization_create', 'organization_edit', 'organization_delete', 'organization_view',
                # Gestion des interactions
                'interaction_create', 'interaction_edit', 'interaction_delete', 'interaction_view',
                # Gestion des badges
                'badge_create', 'badge_edit', 'badge_delete', 'badge_view', 'badge_revoke',
                # Gestion des objectifs
                'objective_create', 'objective_edit', 'objective_delete', 'objective_view',
                # Gestion des paramètres
                'settings_view', 'settings_edit', 'settings_roles', 'settings_references',
                # Rapports et statistiques
                'reports_view', 'reports_export', 'stats_view',
                # Administration système
                'system_admin', 'data_backup', 'data_restore',
            ],
            'superviseur': [
                # Gestion des utilisateurs (agents seulement)
                'user_create', 'user_edit', 'user_view',
                # Gestion des adhérents
                'adherent_create', 'adherent_edit', 'adherent_delete', 'adherent_view',
                # Gestion des organisations
                'organization_create', 'organization_edit', 'organization_delete', 'organization_view',
                # Gestion des interactions
                'interaction_create', 'interaction_edit', 'interaction_delete', 'interaction_view',
                # Gestion des badges
                'badge_create', 'badge_edit', 'badge_view', 'badge_revoke',
                # Gestion des objectifs
                'objective_create', 'objective_edit', 'objective_delete', 'objective_view',
                # Paramètres (lecture seulement)
                'settings_view',
                # Rapports et statistiques
                'reports_view', 'stats_view',
            ],
            'agent': [
                # Gestion des adhérents (lecture et création)
                'adherent_create', 'adherent_view',
                # Gestion des organisations (lecture et création)
                'organization_create', 'organization_view',
                # Gestion des interactions (lecture et création)
                'interaction_create', 'interaction_view',
                # Gestion des badges (lecture seulement)
                'badge_view',
                # Objectifs (lecture seulement)
                'objective_view',
            ]
        }

        # Déterminer quels rôles traiter
        roles_to_process = [options['role']] if options['role'] else default_permissions.keys()

        with transaction.atomic():
            total_created = 0
            total_updated = 0

            for role in roles_to_process:
                if role not in default_permissions:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  Rôle "{role}" non reconnu, ignoré.')
                    )
                    continue

                self.stdout.write(f'\n📋 Traitement du rôle: {role}')
                
                # Supprimer les permissions existantes si --force
                if options['force']:
                    deleted_count = RolePermission.objects.filter(role=role).delete()[0]
                    if deleted_count > 0:
                        self.stdout.write(
                            self.style.WARNING(f'   - {deleted_count} permissions existantes supprimées')
                        )

                # Créer les nouvelles permissions
                for permission in default_permissions[role]:
                    permission_obj, created = RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission,
                        defaults={'is_active': True}
                    )
                    
                    if created:
                        total_created += 1
                        self.stdout.write(f'   ✅ Créée: {permission}')
                    else:
                        # Mettre à jour si la permission existait mais était inactive
                        if not permission_obj.is_active:
                            permission_obj.is_active = True
                            permission_obj.save()
                            total_updated += 1
                            self.stdout.write(f'   🔄 Activée: {permission}')
                        else:
                            self.stdout.write(f'   ℹ️  Existe déjà: {permission}')

        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Initialisation terminée!')
        )
        self.stdout.write(f'   - Permissions créées: {total_created}')
        self.stdout.write(f'   - Permissions activées: {total_updated}')
        self.stdout.write(f'   - Total des permissions: {RolePermission.objects.count()}')

        # Vérification des utilisateurs
        self.stdout.write('\n👥 Vérification des utilisateurs:')
        for role in ['admin', 'superviseur', 'agent']:
            count = User.objects.filter(role=role, is_active=True).count()
            self.stdout.write(f'   - {role.capitalize()}: {count} utilisateur(s) actif(s)')

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Les permissions sont maintenant configurées!')
        )
        self.stdout.write(
            '💡 Conseil: Utilisez l\'interface d\'administration pour ajuster les permissions selon vos besoins.'
        ) 