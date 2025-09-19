from django.core.management.base import BaseCommand
from core.models import User, UserObjective

class Command(BaseCommand):
    help = 'Met à jour les assignments des objectifs existants'

    def handle(self, *args, **options):
        self.stdout.write("=== MISE À JOUR DES ASSIGNMENTS D'OBJECTIFS ===")
        
        # Récupérer tous les objectifs sans assigned_by
        objectives_without_assigned_by = UserObjective.objects.filter(assigned_by__isnull=True)
        self.stdout.write(f"Objectifs sans assigned_by: {objectives_without_assigned_by.count()}")
        
        for objective in objectives_without_assigned_by:
            # Essayer de trouver le superviseur responsable de cet agent
            if objective.user.created_by and objective.user.created_by.role == 'superviseur':
                objective.assigned_by = objective.user.created_by
                objective.save()
                self.stdout.write(f"  → Objectif {objective.id} assigné à {objective.assigned_by.get_full_name()}")
            else:
                self.stdout.write(f"  ⚠️  Objectif {objective.id}: Aucun superviseur trouvé pour {objective.user.get_full_name()}")
        
        # Mettre à jour tous les objectifs
        self.stdout.write("\n=== MISE À JOUR DE LA PROGRESSION ===")
        updated_count = UserObjective.update_all_objectives()
        self.stdout.write(f"Objectifs mis à jour: {updated_count}")
        
        self.stdout.write(self.style.SUCCESS("Mise à jour terminée!"))
