#!/usr/bin/env python
"""
Script de test pour vérifier les valeurs de référence
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import ReferenceValue, User, SystemLog

def test_reference_values():
    """Test des valeurs de référence"""
    print("=== Test des valeurs de référence ===")
    
    # Créer un utilisateur de test si nécessaire
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'matricule': 'TEST001',
            'first_name': 'Test',
            'last_name': 'User',
            'telephone': '612345678',
            'profession': 'Testeur',
            'role': 'admin'
        }
    )
    
    if created:
        print(f"Utilisateur de test créé: {user}")
    
    # Créer une valeur de référence de test
    reference, created = ReferenceValue.objects.get_or_create(
        category='interaction_status',
        code='test_status',
        defaults={
            'label': 'Statut de test',
            'description': 'Statut pour les tests',
            'sort_order': 1,
            'is_active': True,
            'created_by': user
        }
    )
    
    if created:
        print(f"Valeur de référence créée: {reference}")
    else:
        print(f"Valeur de référence existante: {reference}")
    
    # Tester le journal système
    try:
        log_entry = SystemLog.log(
            'INFO', 
            'system_config', 
            'Test de journal système',
            user=user,
            user_agent='Test Script'
        )
        print(f"Journal système créé: {log_entry}")
    except Exception as e:
        print(f"Erreur lors de la création du journal: {e}")
    
    # Lister toutes les valeurs de référence
    print("\n=== Valeurs de référence existantes ===")
    for ref in ReferenceValue.objects.all():
        print(f"- {ref.category}: {ref.code} - {ref.label}")
    
    print("\n=== Test terminé avec succès ===")

if __name__ == '__main__':
    test_reference_values() 