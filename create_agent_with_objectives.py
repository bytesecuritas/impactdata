#!/usr/bin/env python3
"""
Script pour créer un agent avec des objectifs et des éléments déjà effectués
Usage: python create_agent_with_objectives.py
"""

import os
import sys
import django
from datetime import datetime, timedelta, date
import random
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import (
    User, Organization, Adherent, Interaction, UserObjective, 
    Category, ReferenceValue
)
from django.utils import timezone
from django.db import transaction

User = get_user_model()

class AgentDataGenerator:
    """Générateur de données pour un agent avec objectifs et éléments"""
    
    def __init__(self):
        self.superviseur = None
        self.agent = None
        self.organizations = []
        self.adherents = []
        self.interactions = []
        self.objectives = []
        
    def ensure_superviseur(self):
        """S'assure qu'il y a un superviseur disponible"""
        try:
            self.superviseur = User.objects.filter(role='superviseur').first()
            if not self.superviseur:
                print("⚠️  Aucun superviseur trouvé. Création d'un superviseur...")
                self.superviseur = User.objects.create_user(
                    email='superviseur@example.com',
                    matricule='SUP001',
                    first_name='Superviseur',
                    last_name='Test',
                    telephone='612345678',
                    profession='Superviseur',
                    role='superviseur',
                    created_by=None
                )
                print(f"✅ Superviseur créé: {self.superviseur.get_full_name()}")
            else:
                print(f"✅ Superviseur existant utilisé: {self.superviseur.get_full_name()}")
        except Exception as e:
            print(f"❌ Erreur lors de la création du superviseur: {e}")
            return False
        return True
    
    def ensure_categories(self):
        """S'assure qu'il y a des catégories d'organisation"""
        try:
            categories = Category.objects.all()
            if not categories.exists():
                print("⚠️  Aucune catégorie trouvée. Création des catégories...")
                categories_data = [
                    ('Entreprise', 'Entreprise privée'),
                    ('Association', 'Association à but non lucratif'),
                    ('ONG', 'Organisation non gouvernementale'),
                    ('Institution', 'Institution publique'),
                ]
                
                for name, description in categories_data:
                    Category.objects.create(name=name, description=description)
                print("✅ Catégories créées")
            else:
                print(f"✅ {categories.count()} catégories disponibles")
        except Exception as e:
            print(f"❌ Erreur lors de la création des catégories: {e}")
            return False
        return True
    
    def ensure_reference_values(self):
        """S'assure qu'il y a des valeurs de référence pour les centres d'intérêt"""
        try:
            centres_interet = ReferenceValue.objects.filter(
                category='centres_d_interet',
                is_active=True
            )
            
            if not centres_interet.exists():
                print("⚠️  Aucun centre d'intérêt trouvé. Création des centres d'intérêt...")
                centres_data = [
                    ('sport', 'Sport', 'Activités sportives', 1),
                    ('culture', 'Culture', 'Activités culturelles', 2),
                    ('education', 'Éducation', 'Formation et éducation', 3),
                    ('sante', 'Santé', 'Secteur de la santé', 4),
                    ('technologie', 'Technologie', 'Technologies et innovation', 5),
                    ('environnement', 'Environnement', 'Protection de l\'environnement', 6),
                ]
                
                for code, label, description, sort_order in centres_data:
                    ReferenceValue.objects.create(
                        category='centres_d_interet',
                        code=code,
                        label=label,
                        description=description,
                        sort_order=sort_order,
                        is_active=True,
                        is_system=False
                    )
                print("✅ Centres d'intérêt créés")
            else:
                print(f"✅ {centres_interet.count()} centres d'intérêt disponibles")
        except Exception as e:
            print(f"❌ Erreur lors de la création des centres d'intérêt: {e}")
            return False
        return True
    
    def create_agent(self):
        """Crée un agent de test"""
        try:
            # Données de l'agent
            agent_data = {
                'email': 'agent.test@example.com',
                'matricule': 'AGT001',
                'first_name': 'Agent',
                'last_name': 'Test',
                'telephone': '623456789',
                'profession': 'Agent de terrain',
                'fonction': 'Collecteur de données',
                'role': 'agent',
                'created_by': self.superviseur,
                'adresse': '123 Avenue Test, Yaoundé',
                'nom_urg1': 'Contact',
                'prenom_urg1': 'Urgence',
                'telephone_urg1': '634567890'
            }
            
            # Vérifier si l'agent existe déjà
            existing_agent = User.objects.filter(
                email=agent_data['email']
            ).first()
            
            if existing_agent:
                print(f"⚠️  Agent existant trouvé: {existing_agent.get_full_name()}")
                self.agent = existing_agent
            else:
                self.agent = User.objects.create_user(**agent_data)
                print(f"✅ Agent créé: {self.agent.get_full_name()}")
                
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création de l'agent: {e}")
            return False
    
    def create_organizations(self, count=5):
        """Crée des organisations pour l'agent"""
        try:
            categories = list(Category.objects.all())
            if not categories:
                print("❌ Aucune catégorie disponible")
                return False
            
            organization_names = [
                "Entreprise Test 1", "Association Test 1", "ONG Test 1",
                "Institution Test 1", "Coopérative Test 1", "Entreprise Test 2",
                "Association Test 2", "ONG Test 2", "Institution Test 2",
                "Coopérative Test 2"
            ]
            
            addresses = [
                "Quartier Bastos, Yaoundé", "Quartier Nlongkak, Yaoundé",
                "Quartier Mvog-Ada, Yaoundé", "Quartier Essos, Yaoundé",
                "Quartier Emana, Yaoundé", "Quartier Nkoldongo, Yaoundé",
                "Quartier Elig-Edzoa, Yaoundé", "Quartier Odza, Yaoundé",
                "Quartier Ekounou, Yaoundé", "Quartier Mbankomo, Yaoundé"
            ]
            
            for i in range(count):
                org_data = {
                    'name': organization_names[i],
                    'address': addresses[i],
                    'category': random.choice(categories),
                    'number_personnel': random.randint(5, 50),
                    'monthly_revenue': Decimal(str(random.randint(100000, 5000000))),
                    'creation_date': date.today() - timedelta(days=random.randint(30, 365)),
                    'phone': f'6{random.randint(10000000, 99999999)}',
                    'whatsapp': f'6{random.randint(10000000, 99999999)}',
                    'infos_annexes': f'Organisation créée pour les tests - {i+1}',
                    'created_by': self.agent,
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 30))
                }
                
                org = Organization(**org_data)
                org.save()
                self.organizations.append(org)
                
            print(f"✅ {count} organisations créées")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création des organisations: {e}")
            return False
    
    def create_adherents(self, count=8):
        """Crée des adhérents pour l'agent"""
        try:
            if not self.organizations:
                print("❌ Aucune organisation disponible pour les adhérents")
                return False
            
            centres_interet = list(ReferenceValue.objects.filter(
                category='centres_d_interet',
                is_active=True
            ))
            
            first_names = ['Jean', 'Marie', 'Paul', 'Anne', 'Pierre', 'Julie', 'Marc', 'Sophie', 'Luc', 'Claire']
            last_names = ['Dupont', 'Martin', 'Durand', 'Moreau', 'Simon', 'Laurent', 'Lefebvre', 'Michel', 'Garcia', 'David']
            communes = ['Yaoundé', 'Douala', 'Bafoussam', 'Bamenda', 'Garoua', 'Maroua', 'Nkongsamba', 'Kumba']
            quartiers = ['Centre', 'Bastos', 'Nlongkak', 'Mvog-Ada', 'Essos', 'Emana', 'Nkoldongo', 'Elig-Edzoa']
            
            for i in range(count):
                # Sélectionner une organisation aléatoire
                org = random.choice(self.organizations)
                
                adherent_data = {
                    'first_name': random.choice(first_names),
                    'last_name': random.choice(last_names),
                    'birth_date': date.today() - timedelta(days=random.randint(6570, 18250)),  # 18-50 ans
                    'type_adherent': random.choice(['physical', 'legal']),
                    'commune': random.choice(communes),
                    'quartier': random.choice(quartiers),
                    'secteur': f'Secteur {random.randint(1, 10)}',
                    'phone1': f'6{random.randint(10000000, 99999999)}',
                    'phone2': f'6{random.randint(10000000, 99999999)}' if random.choice([True, False]) else '',
                    'email': f'adherent{i+1}@example.com',
                    'medical_info': 'Aucune information médicale particulière' if random.choice([True, False]) else '',
                    'formation_pro': f'Formation professionnelle {random.choice(["Informatique", "Commerce", "Santé", "Éducation"])}',
                    'distinction': f'Distinction {random.choice(["Excellence", "Mérite", "Innovation"])}' if random.choice([True, False]) else '',
                    'langues': random.choice(['Français', 'Anglais', 'Français, Anglais', 'Français, Anglais, Espagnol']),
                    'join_date': date.today() - timedelta(days=random.randint(1, 365)),
                    'organisation': org,
                    'activity_name': f'Activité {random.choice(["Commerciale", "Éducative", "Sociale", "Technique"])}',
                    'badge_validity': date.today() + timedelta(days=random.randint(30, 365)),
                    'created_by': self.agent,
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 30))
                }
                
                adherent = Adherent(**adherent_data)
                adherent.save()
                
                # Ajouter des centres d'intérêt aléatoires
                if centres_interet:
                    selected_centres = random.sample(
                        centres_interet, 
                        random.randint(1, min(3, len(centres_interet)))
                    )
                    adherent.centres_interet.set(selected_centres)
                
                self.adherents.append(adherent)
                
            print(f"✅ {count} adhérents créés")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création des adhérents: {e}")
            return False
    
    def create_interactions(self, count=6):
        """Crée des interactions pour l'agent"""
        try:
            if not self.adherents:
                print("❌ Aucun adhérent disponible pour les interactions")
                return False
            
            statuses = ['in_progress', 'completed', 'cancelled']
            reports = [
                "Rapport de visite standard - Suivi des activités",
                "Rapport détaillé - Évaluation des besoins",
                "Rapport de formation - Session d'information",
                "Rapport de suivi - Contrôle qualité",
                "Rapport d'audit - Vérification des procédures",
                "Rapport de sensibilisation - Campagne d'information"
            ]
            
            for i in range(count):
                adherent = random.choice(self.adherents)
                
                interaction_data = {
                    'auteur': self.superviseur,  # L'auteur est généralement le superviseur
                    'personnel': self.agent,     # Le personnel assigné est l'agent
                    'adherent': adherent,
                    'report': random.choice(reports),
                    'due_date': timezone.now() + timedelta(days=random.randint(1, 30)),
                    'status': random.choice(statuses),
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 30))
                }
                
                interaction = Interaction(**interaction_data)
                interaction.save()
                self.interactions.append(interaction)
                
            print(f"✅ {count} interactions créées")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création des interactions: {e}")
            return False
    
    def create_objectives(self):
        """Crée des objectifs pour l'agent avec des éléments déjà effectués"""
        try:
            if not self.agent:
                print("❌ Aucun agent disponible")
                return False
            
            # Calculer les valeurs de base actuelles
            base_organizations = Organization.objects.filter(created_by=self.agent).count()
            base_adherents = Adherent.objects.filter(created_by=self.agent).count()
            base_interactions = Interaction.objects.filter(personnel=self.agent).count()
            
            print(f"📊 Valeurs de base actuelles:")
            print(f"   - Organisations: {base_organizations}")
            print(f"   - Adhérents: {base_adherents}")
            print(f"   - Interactions: {base_interactions}")
            
            # Créer des objectifs réalistes
            objectives_data = [
                {
                    'objective_type': 'organizations',
                    'target_value': base_organizations + 3,  # 3 nouvelles organisations
                    'deadline': date.today() + timedelta(days=30),
                    'description': 'Objectif de créer 3 nouvelles organisations ce mois-ci'
                },
                {
                    'objective_type': 'adherents',
                    'target_value': base_adherents + 5,  # 5 nouveaux adhérents
                    'deadline': date.today() + timedelta(days=45),
                    'description': 'Objectif de recruter 5 nouveaux adhérents'
                },
                {
                    'objective_type': 'interactions',
                    'target_value': base_interactions + 4,  # 4 nouvelles interactions
                    'deadline': date.today() + timedelta(days=20),
                    'description': 'Objectif de réaliser 4 nouvelles interactions'
                }
            ]
            
            for obj_data in objectives_data:
                objective = UserObjective.objects.create(
                    user=self.agent,
                    assigned_by=self.superviseur,
                    base_value=0,  # Sera calculé automatiquement
                    current_value=0,  # Sera calculé automatiquement
                    status='pending',
                    **obj_data
                )
                
                # Mettre à jour la progression
                objective.update_progress()
                self.objectives.append(objective)
                
            print(f"✅ {len(objectives_data)} objectifs créés")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la création des objectifs: {e}")
            return False
    
    def display_summary(self):
        """Affiche un résumé des données créées"""
        print("\n" + "="*60)
        print("📋 RÉSUMÉ DES DONNÉES CRÉÉES")
        print("="*60)
        
        if self.agent:
            print(f"👤 Agent: {self.agent.get_full_name()} ({self.agent.matricule})")
            print(f"   Email: {self.agent.email}")
            print(f"   Téléphone: {self.agent.telephone}")
            print(f"   Superviseur: {self.superviseur.get_full_name() if self.superviseur else 'N/A'}")
        
        print(f"\n🏢 Organisations: {len(self.organizations)}")
        for i, org in enumerate(self.organizations[:3], 1):
            print(f"   {i}. {org.name} ({org.category.name})")
        if len(self.organizations) > 3:
            print(f"   ... et {len(self.organizations) - 3} autres")
        
        print(f"\n👥 Adhérents: {len(self.adherents)}")
        for i, adherent in enumerate(self.adherents[:3], 1):
            print(f"   {i}. {adherent.full_name} ({adherent.organisation.name})")
        if len(self.adherents) > 3:
            print(f"   ... et {len(self.adherents) - 3} autres")
        
        print(f"\n📞 Interactions: {len(self.interactions)}")
        for i, interaction in enumerate(self.interactions[:3], 1):
            print(f"   {i}. {interaction.adherent.full_name} - {interaction.get_status_display()}")
        if len(self.interactions) > 3:
            print(f"   ... et {len(self.interactions) - 3} autres")
        
        print(f"\n🎯 Objectifs: {len(self.objectives)}")
        for i, objective in enumerate(self.objectives, 1):
            print(f"   {i}. {objective.get_objective_type_display()}: {objective.current_value}/{objective.target_increment}")
            print(f"      Statut: {objective.get_status_display()}")
            print(f"      Échéance: {objective.deadline}")
        
        print("\n" + "="*60)
        print("✅ SCRIPT TERMINÉ AVEC SUCCÈS")
        print("="*60)
        print("\n📝 Instructions pour tester:")
        print("1. Connectez-vous en tant que superviseur ou admin")
        print("2. Allez dans Objectifs pour voir les objectifs assignés")
        print("3. Allez dans le dashboard de l'agent pour voir sa progression")
        print("4. Créez de nouveaux éléments pour voir la progression se mettre à jour")

def main():
    """Fonction principale"""
    print("🚀 DÉMARRAGE DU SCRIPT DE CRÉATION D'AGENT AVEC OBJECTIFS")
    print("="*60)
    
    generator = AgentDataGenerator()
    
    try:
        with transaction.atomic():
            # 1. S'assurer qu'il y a un superviseur
            if not generator.ensure_superviseur():
                return
            
            # 2. S'assurer qu'il y a des catégories
            if not generator.ensure_categories():
                return
            
            # 3. S'assurer qu'il y a des valeurs de référence
            if not generator.ensure_reference_values():
                return
            
            # 4. Créer l'agent
            if not generator.create_agent():
                return
            
            # 5. Créer des organisations (éléments déjà effectués)
            if not generator.create_organizations(count=5):
                return
            
            # 6. Créer des adhérents (éléments déjà effectués)
            if not generator.create_adherents(count=8):
                return
            
            # 7. Créer des interactions (éléments déjà effectués)
            if not generator.create_interactions(count=6):
                return
            
            # 8. Créer des objectifs
            if not generator.create_objectives():
                return
            
            # 9. Afficher le résumé
            generator.display_summary()
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
