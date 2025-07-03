#!/usr/bin/env python
"""
Script de test pour vérifier le fonctionnement des objectifs
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import User, UserObjective, Organization, Adherent, Interaction
from django.utils import timezone
from datetime import date, timedelta

def test_objective_system():
    """Test du système d'objectifs"""
    print("🧪 Test du système d'objectifs")
    print("=" * 50)
    
    # Créer un agent de test
    agent, created = User.objects.get_or_create(
        email='agent_test@example.com',
        defaults={
            'matricule': 'AGT001',
            'first_name': 'Agent',
            'last_name': 'Test',
            'profession': 'Testeur',
            'telephone': '123456789',
            'role': 'agent'
        }
    )
    
    if created:
        print(f"✅ Agent créé : {agent.get_full_name()}")
    else:
        print(f"ℹ️  Agent existant : {agent.get_full_name()}")
    
    # Créer quelques organisations existantes
    org1, created = Organization.objects.get_or_create(
        identifiant=1001,
        defaults={
            'name': 'Organisation Test 1',
            'address': 'Adresse 1',
            'phone': '123456789',
            'category_id': 1,  # Assurez-vous qu'une catégorie existe
            'created_by': agent
        }
    )
    
    org2, created = Organization.objects.get_or_create(
        identifiant=1002,
        defaults={
            'name': 'Organisation Test 2',
            'address': 'Adresse 2',
            'phone': '987654321',
            'category_id': 1,
            'created_by': agent
        }
    )
    
    print(f"📊 Organisations existantes : {Organization.objects.filter(created_by=agent).count()}")
    
    # Créer un objectif
    objective = UserObjective.objects.create(
        user=agent,
        objective_type='organizations',
        target_value=3,  # Créer 3 organisations en plus
        deadline=date.today() + timedelta(days=30),
        description='Test objectif organisations',
        assigned_by=agent  # Pour simplifier
    )
    
    print(f"🎯 Objectif créé :")
    print(f"   - Valeur de base : {objective.base_value}")
    print(f"   - Incrément cible : {objective.target_increment}")
    print(f"   - Valeur cible totale : {objective.target_value}")
    print(f"   - Valeur actuelle : {objective.current_value}")
    print(f"   - Progression : {objective.progress_percentage:.1f}%")
    
    # Créer une nouvelle organisation
    org3 = Organization.objects.create(
        identifiant=1003,
        name='Organisation Test 3',
        address='Adresse 3',
        phone='555555555',
        category_id=1,
        created_by=agent
    )
    
    print(f"\n📈 Après création d'une organisation :")
    objective.refresh_from_db()
    print(f"   - Valeur actuelle : {objective.current_value}")
    print(f"   - Progression : {objective.progress_percentage:.1f}%")
    print(f"   - Statut : {objective.get_status_display()}")
    
    # Créer une autre organisation
    org4 = Organization.objects.create(
        identifiant=1004,
        name='Organisation Test 4',
        address='Adresse 4',
        phone='666666666',
        category_id=1,
        created_by=agent
    )
    
    print(f"\n📈 Après création d'une deuxième organisation :")
    objective.refresh_from_db()
    print(f"   - Valeur actuelle : {objective.current_value}")
    print(f"   - Progression : {objective.progress_percentage:.1f}%")
    print(f"   - Statut : {objective.get_status_display()}")
    
    # Créer une troisième organisation (objectif atteint)
    org5 = Organization.objects.create(
        identifiant=1005,
        name='Organisation Test 5',
        address='Adresse 5',
        phone='777777777',
        category_id=1,
        created_by=agent
    )
    
    print(f"\n📈 Après création d'une troisième organisation :")
    objective.refresh_from_db()
    print(f"   - Valeur actuelle : {objective.current_value}")
    print(f"   - Progression : {objective.progress_percentage:.1f}%")
    print(f"   - Statut : {objective.get_status_display()}")
    
    print(f"\n✅ Test terminé !")
    print(f"📊 Total organisations : {Organization.objects.filter(created_by=agent).count()}")

if __name__ == '__main__':
    test_objective_system() 