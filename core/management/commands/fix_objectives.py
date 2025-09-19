from django.core.management.base import BaseCommand
from core.models import User, UserObjective, Organization, Adherent, Interaction

class Command(BaseCommand):
    help = 'Corrige et met à jour tous les objectifs existants'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES OBJECTIFS ===")
        
        # Mettre à jour tous les objectifs
        objectives = UserObjective.objects.all()
        self.stdout.write(f"Nombre d'objectifs à traiter: {objectives.count()}")
        
        for objective in objectives:
            self.stdout.write(f"\n--- Objectif ID {objective.id} ---")
            self.stdout.write(f"Agent: {objective.user.get_full_name()}")
            self.stdout.write(f"Type: {objective.get_objective_type_display()}")
            self.stdout.write(f"Avant - Base: {objective.base_value}, Cible: {objective.target_value}, Actuel: {objective.current_value}")
            
            # Recalculer la valeur de base si nécessaire
            if objective.objective_type == 'organizations':
                total_orgs = Organization.objects.filter(created_by=objective.user).count()
                if objective.base_value == 0 and total_orgs > 0:
                    # Si l'objectif a été créé après que l'agent ait déjà créé des organisations
                    # on doit ajuster la valeur de base
                    objective.base_value = total_orgs
                    objective.save()
                    self.stdout.write(f"  → Valeur de base corrigée: {objective.base_value}")
            
            # Mettre à jour la progression
            old_current = objective.current_value
            old_status = objective.status
            objective.update_progress()
            
            self.stdout.write(f"Après - Base: {objective.base_value}, Cible: {objective.target_value}, Actuel: {objective.current_value}")
            self.stdout.write(f"Statut: {old_status} → {objective.status}")
            self.stdout.write(f"Progression: {objective.progress_percentage:.1f}%")
            
            if old_current != objective.current_value:
                self.stdout.write("  ✅ Progression mise à jour!")
            else:
                self.stdout.write("  ⚠️  Aucun changement détecté")
        
        self.stdout.write(f"\n=== RÉSUMÉ ===")
        self.stdout.write(f"Objectifs terminés: {UserObjective.objects.filter(status='completed').count()}")
        self.stdout.write(f"Objectifs en cours: {UserObjective.objects.filter(status='in_progress').count()}")
        self.stdout.write(f"Objectifs en attente: {UserObjective.objects.filter(status='pending').count()}")
        self.stdout.write(f"Objectifs échoués: {UserObjective.objects.filter(status='failed').count()}")
        
        self.stdout.write(self.style.SUCCESS("Correction des objectifs terminée!"))
