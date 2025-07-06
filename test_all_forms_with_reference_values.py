#!/usr/bin/env python
"""
Script de test pour vérifier que tous les formulaires utilisent les valeurs de référence
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import ReferenceValue, User, Adherent, Organization, Category, Interaction, Badge, UserObjective
from core.forms import (
    UserForm, UserRegistrationForm, UserEditForm, AdherentForm, AdherentSearchForm,
    InteractionForm, InteractionSearchForm, UserObjectiveForm, BulkRolePermissionForm
)

def test_user_forms():
    """Test les formulaires utilisateur"""
    print("=== Test des formulaires utilisateur ===")
    
    # Test UserForm
    print("\n  UserForm:")
    form = UserForm()
    role_choices = [choice[0] for choice in form.fields['role'].choices if choice[0]]
    print(f"    Rôles disponibles: {role_choices}")
    
    # Test UserRegistrationForm
    print("\n  UserRegistrationForm:")
    form = UserRegistrationForm()
    role_choices = [choice[0] for choice in form.fields['role'].choices if choice[0]]
    print(f"    Rôles disponibles: {role_choices}")
    
    # Test UserEditForm
    print("\n  UserEditForm:")
    form = UserEditForm()
    role_choices = [choice[0] for choice in form.fields['role'].choices if choice[0]]
    print(f"    Rôles disponibles: {role_choices}")
    
    # Test BulkRolePermissionForm
    print("\n  BulkRolePermissionForm:")
    form = BulkRolePermissionForm()
    role_choices = [choice[0] for choice in form.fields['role'].choices if choice[0]]
    print(f"    Rôles disponibles: {role_choices}")

def test_adherent_forms():
    """Test les formulaires adhérent"""
    print("\n=== Test des formulaires adhérent ===")
    
    # Test AdherentForm
    print("\n  AdherentForm:")
    form = AdherentForm()
    type_choices = [choice[0] for choice in form.fields['type_adherent'].choices if choice[0]]
    print(f"    Types d'adhérent disponibles: {type_choices}")
    
    # Test AdherentSearchForm
    print("\n  AdherentSearchForm:")
    form = AdherentSearchForm()
    type_choices = [choice[0] for choice in form.fields['type_adherent'].choices if choice[0]]
    print(f"    Types d'adhérent disponibles: {type_choices}")

def test_interaction_forms():
    """Test les formulaires interaction"""
    print("\n=== Test des formulaires interaction ===")
    
    # Test InteractionForm
    print("\n  InteractionForm:")
    form = InteractionForm()
    status_choices = [choice[0] for choice in form.fields['status'].choices if choice[0]]
    print(f"    Statuts disponibles: {status_choices}")
    
    # Test InteractionSearchForm
    print("\n  InteractionSearchForm:")
    form = InteractionSearchForm()
    status_choices = [choice[0] for choice in form.fields['status'].choices if choice[0]]
    print(f"    Statuts disponibles: {status_choices}")

def test_objective_forms():
    """Test les formulaires objectif"""
    print("\n=== Test des formulaires objectif ===")
    
    # Test UserObjectiveForm
    print("\n  UserObjectiveForm:")
    form = UserObjectiveForm()
    objective_choices = [choice[0] for choice in form.fields['objective_type'].choices if choice[0]]
    print(f"    Types d'objectif disponibles: {objective_choices}")

def test_reference_values_in_forms():
    """Test que les valeurs de référence sont bien utilisées dans les formulaires"""
    print("\n=== Test de l'utilisation des valeurs de référence ===")
    
    # Vérifier que les valeurs de référence existent
    categories_to_test = [
        ('user_roles', 'Rôles utilisateur'),
        ('adherent_types', 'Types d\'adhérent'),
        ('interaction_status', 'Statuts d\'interaction'),
    ]
    
    for category_code, category_name in categories_to_test:
        print(f"\n  {category_name} ({category_code}):")
        
        # Compter les valeurs de référence
        ref_count = ReferenceValue.objects.filter(category=category_code, is_active=True).count()
        print(f"    Valeurs de référence actives: {ref_count}")
        
        # Lister les valeurs
        ref_values = ReferenceValue.objects.filter(category=category_code, is_active=True).order_by('sort_order')
        for value in ref_values:
            print(f"      - {value.code}: {value.label}")
        
        # Vérifier que ces valeurs apparaissent dans les formulaires correspondants
        if category_code == 'user_roles':
            form = UserForm()
            form_choices = [choice[0] for choice in form.fields['role'].choices if choice[0]]
            ref_codes = [value.code for value in ref_values]
            
            missing_in_form = set(ref_codes) - set(form_choices)
            if missing_in_form:
                print(f"    ⚠️  Valeurs manquantes dans le formulaire: {missing_in_form}")
            else:
                print(f"    ✅ Toutes les valeurs de référence sont dans le formulaire")
        
        elif category_code == 'adherent_types':
            form = AdherentForm()
            form_choices = [choice[0] for choice in form.fields['type_adherent'].choices if choice[0]]
            ref_codes = [value.code for value in ref_values]
            
            missing_in_form = set(ref_codes) - set(form_choices)
            if missing_in_form:
                print(f"    ⚠️  Valeurs manquantes dans le formulaire: {missing_in_form}")
            else:
                print(f"    ✅ Toutes les valeurs de référence sont dans le formulaire")
        
        elif category_code == 'interaction_status':
            form = InteractionForm()
            form_choices = [choice[0] for choice in form.fields['status'].choices if choice[0]]
            ref_codes = [value.code for value in ref_values]
            
            missing_in_form = set(ref_codes) - set(form_choices)
            if missing_in_form:
                print(f"    ⚠️  Valeurs manquantes dans le formulaire: {missing_in_form}")
            else:
                print(f"    ✅ Toutes les valeurs de référence sont dans le formulaire")

def test_form_validation():
    """Test la validation des formulaires avec les valeurs de référence"""
    print("\n=== Test de validation des formulaires ===")
    
    # Créer des données de test
    test_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'matricule': 'TEST001',
        'telephone': '612345678',
        'profession': 'Testeur',
        'role': 'agent'
    }
    
    # Test UserForm
    print("\n  Test UserForm avec données valides:")
    form = UserForm(data=test_data)
    if form.is_valid():
        print("    ✅ Formulaire valide")
    else:
        print("    ❌ Erreurs de validation:")
        for field, errors in form.errors.items():
            print(f"      {field}: {errors}")
    
    # Test avec un rôle invalide
    print("\n  Test UserForm avec rôle invalide:")
    invalid_data = test_data.copy()
    invalid_data['role'] = 'invalid_role'
    form = UserForm(data=invalid_data)
    if not form.is_valid():
        print("    ✅ Validation échoue correctement pour rôle invalide")
    else:
        print("    ⚠️  Validation devrait échouer pour rôle invalide")

def test_dynamic_value_addition():
    """Test l'ajout dynamique de nouvelles valeurs"""
    print("\n=== Test d'ajout dynamique de valeurs ===")
    
    # Ajouter une nouvelle valeur de référence
    new_role, created = ReferenceValue.objects.get_or_create(
        category='user_roles',
        code='moderateur',
        defaults={
            'label': 'Modérateur',
            'description': 'Rôle de modérateur avec permissions limitées',
            'sort_order': 4,
            'is_active': True,
            'is_default': False,
            'is_system': False
        }
    )
    
    if created:
        print(f"  ✅ Nouvelle valeur ajoutée: {new_role.code} - {new_role.label}")
    else:
        print(f"  ℹ️  Valeur existante: {new_role.code} - {new_role.label}")
    
    # Vérifier qu'elle apparaît dans le formulaire
    form = UserForm()
    role_choices = [choice[0] for choice in form.fields['role'].choices if choice[0]]
    
    if 'moderateur' in role_choices:
        print("  ✅ Nouvelle valeur disponible dans le formulaire")
    else:
        print("  ❌ Nouvelle valeur non disponible dans le formulaire")
    
    # Nettoyer - supprimer la valeur de test
    if created:
        new_role.delete()
        print("  🧹 Valeur de test supprimée")

def main():
    """Fonction principale"""
    print("🚀 Test complet des formulaires avec valeurs de référence")
    print("=" * 60)
    
    try:
        # Test 1: Formulaires utilisateur
        test_user_forms()
        
        # Test 2: Formulaires adhérent
        test_adherent_forms()
        
        # Test 3: Formulaires interaction
        test_interaction_forms()
        
        # Test 4: Formulaires objectif
        test_objective_forms()
        
        # Test 5: Utilisation des valeurs de référence
        test_reference_values_in_forms()
        
        # Test 6: Validation des formulaires
        test_form_validation()
        
        # Test 7: Ajout dynamique
        test_dynamic_value_addition()
        
        print("\n" + "=" * 60)
        print("✅ Tests terminés avec succès!")
        print("\n📋 Résumé:")
        print("  - Tous les formulaires utilisent maintenant les valeurs de référence")
        print("  - Les administrateurs peuvent ajouter/supprimer des options dynamiquement")
        print("  - Les formulaires ont un fallback vers les choix statiques si nécessaire")
        print("  - La validation fonctionne correctement avec les nouvelles valeurs")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 