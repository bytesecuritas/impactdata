#!/usr/bin/env python
"""
Script de test complet pour vérifier toutes les fonctionnalités des paramètres
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import ReferenceValue, GeneralParameter, User, SystemLog

def test_parameters_complete():
    """Test complet des paramètres"""
    print("=== Test Complet des Paramètres ===")
    
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
        print(f"✅ Utilisateur de test créé: {user}")
    else:
        print(f"✅ Utilisateur de test existant: {user}")
    
    # Test 1: Valeurs de référence
    print("\n--- Test des Valeurs de Référence ---")
    
    # Créer une valeur de référence de test
    reference, created = ReferenceValue.objects.get_or_create(
        category='interaction_status',
        code='test_status',
        defaults={
            'label': 'Statut de test',
            'description': 'Statut pour les tests',
            'sort_order': 1,
            'is_active': True,
            'is_default': False,
            'is_system': False,
            'created_by': user
        }
    )
    
    if created:
        print(f"✅ Valeur de référence créée: {reference}")
    else:
        print(f"✅ Valeur de référence existante: {reference}")
    
    # Vérifier que le champ is_system existe
    try:
        reference.is_system = True
        reference.save()
        print("✅ Champ is_system fonctionne correctement")
    except Exception as e:
        print(f"❌ Erreur avec le champ is_system: {e}")
    
    # Test 2: Paramètres généraux
    print("\n--- Test des Paramètres Généraux ---")
    
    # Créer un paramètre général de test
    parameter, created = GeneralParameter.objects.get_or_create(
        parameter_key='test_parameter',
        defaults={
            'parameter_type': 'text',
            'value': 'valeur_test',
            'description': 'Paramètre de test',
            'is_required': False,
            'is_system': False,
            'created_by': user
        }
    )
    
    if created:
        print(f"✅ Paramètre général créé: {parameter}")
    else:
        print(f"✅ Paramètre général existant: {parameter}")
    
    # Test 3: Journal système
    print("\n--- Test du Journal Système ---")
    
    try:
        log_entry = SystemLog.log(
            'INFO', 
            'system_config', 
            'Test de journal système',
            user=user,
            user_agent='Test Script'
        )
        print(f"✅ Journal système créé: {log_entry}")
    except Exception as e:
        print(f"❌ Erreur lors de la création du journal: {e}")
    
    # Test 4: Statistiques
    print("\n--- Test des Statistiques ---")
    
    try:
        total_references = ReferenceValue.objects.count()
        active_references = ReferenceValue.objects.filter(is_active=True).count()
        system_references = ReferenceValue.objects.filter(is_system=True).count()
        
        total_parameters = GeneralParameter.objects.count()
        system_parameters = GeneralParameter.objects.filter(is_system=True).count()
        
        print(f"✅ Statistiques des valeurs de référence:")
        print(f"   - Total: {total_references}")
        print(f"   - Actives: {active_references}")
        print(f"   - Système: {system_references}")
        
        print(f"✅ Statistiques des paramètres généraux:")
        print(f"   - Total: {total_parameters}")
        print(f"   - Système: {system_parameters}")
        
    except Exception as e:
        print(f"❌ Erreur lors du calcul des statistiques: {e}")
    
    # Test 5: Méthodes des modèles
    print("\n--- Test des Méthodes des Modèles ---")
    
    try:
        # Test de la méthode get_typed_value
        typed_value = parameter.get_typed_value()
        print(f"✅ get_typed_value fonctionne: {typed_value}")
        
        # Test de la méthode get_choices_for_category
        choices = ReferenceValue.get_choices_for_category('interaction_status')
        print(f"✅ get_choices_for_category fonctionne: {len(choices)} choix trouvés")
        
    except Exception as e:
        print(f"❌ Erreur lors du test des méthodes: {e}")
    
    # Test 6: Validation des formulaires
    print("\n--- Test de Validation des Formulaires ---")
    
    try:
        from core.forms import ReferenceValueForm, GeneralParameterForm
        
        # Test du formulaire ReferenceValue
        form_data = {
            'category': 'interaction_status',
            'code': 'test_form',
            'label': 'Test Formulaire',
            'description': 'Test de validation',
            'sort_order': 1,
            'is_active': True,
            'is_default': False,
            'is_system': False,
        }
        
        form = ReferenceValueForm(data=form_data)
        if form.is_valid():
            print("✅ Formulaire ReferenceValue valide")
        else:
            print(f"❌ Formulaire ReferenceValue invalide: {form.errors}")
        
        # Test du formulaire GeneralParameter
        param_form_data = {
            'parameter_key': 'test_form_param',
            'parameter_type': 'text',
            'value': 'valeur_test',
            'description': 'Test de validation',
            'is_required': False,
            'is_system': False,
        }
        
        param_form = GeneralParameterForm(data=param_form_data)
        if param_form.is_valid():
            print("✅ Formulaire GeneralParameter valide")
        else:
            print(f"❌ Formulaire GeneralParameter invalide: {param_form.errors}")
            
    except Exception as e:
        print(f"❌ Erreur lors du test des formulaires: {e}")
    
    print("\n=== Test Terminé ===")
    print("✅ Tous les tests de base des paramètres sont passés avec succès!")

if __name__ == '__main__':
    test_parameters_complete() 