from django.core.management.base import BaseCommand
from core.models import UserObjective


class Command(BaseCommand):
    help = 'Met à jour tous les objectifs utilisateurs avec les données actuelles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='ID de l\'utilisateur spécifique pour mettre à jour ses objectifs'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait mis à jour sans effectuer les modifications'
        )

    def handle(self, *args, **options):
        user_id = options.get('user')
        dry_run = options.get('dry_run')

        if dry_run:
            self.stdout.write(self.style.WARNING('Mode DRY RUN - Aucune modification ne sera effectuée'))
            self.stdout.write('')

        if user_id:
            # Mettre à jour les objectifs d'un utilisateur spécifique
            try:
                from core.models import User
                user = User.objects.get(id=user_id)
                self.stdout.write(f'🔄 Mise à jour des objectifs pour {user.get_full_name()}...')
                
                objectives = UserObjective.objects.filter(
                    user=user,
                    status__in=['pending', 'in_progress']
                )
                
                updated_count = 0
                for objective in objectives:
                    old_status = objective.status
                    old_value = objective.current_value
                    
                    if not dry_run:
                        objective.update_progress()
                    
                    new_status = objective.status
                    new_value = objective.current_value
                    
                    if old_status != new_status or old_value != new_value:
                        updated_count += 1
                        self.stdout.write(
                            f'   ✅ {objective.get_objective_type_display()}: '
                            f'{old_value} → {new_value} ({old_status} → {new_status})'
                        )
                
                if updated_count == 0:
                    self.stdout.write('   ℹ️  Aucun objectif mis à jour')
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ {updated_count} objectif(s) mis à jour')
                    )
                    
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Utilisateur avec l\'ID {user_id} non trouvé')
                )
        else:
            # Mettre à jour tous les objectifs
            self.stdout.write('🔄 Mise à jour de tous les objectifs...')
            
            objectives = UserObjective.objects.filter(status__in=['pending', 'in_progress'])
            total_objectives = objectives.count()
            
            if total_objectives == 0:
                self.stdout.write('ℹ️  Aucun objectif actif trouvé')
                return
            
            self.stdout.write(f'📊 {total_objectives} objectif(s) actif(s) trouvé(s)')
            
            updated_count = 0
            for objective in objectives:
                old_status = objective.status
                old_value = objective.current_value
                
                if not dry_run:
                    objective.update_progress()
                
                new_status = objective.status
                new_value = objective.current_value
                
                if old_status != new_status or old_value != new_value:
                    updated_count += 1
                    self.stdout.write(
                        f'   ✅ {objective.user.get_full_name()} - '
                        f'{objective.get_objective_type_display()}: '
                        f'{old_value} → {new_value} ({old_status} → {new_status})'
                    )
            
            if updated_count == 0:
                self.stdout.write('ℹ️  Aucun objectif mis à jour')
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {updated_count} objectif(s) mis à jour sur {total_objectives}')
                )
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Mode DRY RUN terminé - Aucune modification effectuée')) 