#!/usr/bin/env python
"""
Script de test pour vérifier l'intégration des valeurs de référence dans les formulaires
"""

import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import ReferenceValue, Interaction, User, Adherent, Organization, Category
from core.forms import InteractionForm, InteractionSearchForm
from django.test import RequestFactory

def test_reference_values_initialization():
    """Test l'initialisation des valeurs de référence"""
    print("=== Test d'initialisation des valeurs de référence ===")
    
    # Vérifier que les valeurs de référence existent
    categories = [
        'interaction_status',
        'badge_status', 
        'objective_status',
        'user_roles',
        'adherent_types',
        'profession_types',
        'phone_types',
        'emergency_types',
        'medical_info_types',
        'formation_types',
        'distinction_types',
        'language_types',
        'activity_types',
        'organization_categories'
    ]
    
    for category in categories:
        count = ReferenceValue.objects.filter(category=category, is_active=True).count()
        print(f"  {category}: {count} valeurs actives")
        
        if count == 0:
            print(f"    ⚠️  Aucune valeur pour {category}")
        else:
            values = ReferenceValue.objects.filter(category=category, is_active=True).order_by('sort_order')
            for value in values:
                print(f"    - {value.code}: {value.label}")

def test_interaction_form_with_reference_values():
    """Test le formulaire d'interaction avec les valeurs de référence"""
    print("\n=== Test du formulaire d'interaction ===")
    
    # Créer un utilisateur de test si nécessaire
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={
            'matricule': 'TEST001',
            'first_name': 'Test',
            'last_name': 'User',
            'telephone': '612345678',
            'profession': 'Testeur',
            'role': 'agent'
        }
    )
    
    # Créer une organisation de test si nécessaire
    category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={'description': 'Catégorie de test'}
    )
    
    org, created = Organization.objects.get_or_create(
        identifiant=999,
        defaults={
            'name': 'Test Organization',
            'address': 'Test Address',
            'phone': '612345678',
            'category': category
        }
    )
    
    # Créer un adhérent de test si nécessaire
    adherent, created = Adherent.objects.get_or_create(
        identifiant='999-001',
        defaults={
            'first_name': 'Test',
            'last_name': 'Adherent',
            'phone1': '612345678',
            'commune': 'Test Commune',
            'quartier': 'Test Quartier',
            'secteur': 'Test Secteur',
            'join_date': '2024-01-01',
            'organisation': org,
            'type_adherent': 'physical'
        }
    )
    
    # Tester le formulaire d'interaction
    form = InteractionForm(user=user)
    
    print("  Statuts disponibles dans le formulaire:")
    for choice in form.fields['status'].choices:
        if choice[0]:  # Ignorer l'option vide
            print(f"    - {choice[0]}: {choice[1]}")
    
    # Tester la création d'une interaction
    data = {
        'identifiant': 'INT-001',
        'personnel': user.id,
        'adherent': adherent.id,
        'report': 'Test interaction',
        'due_date': '2024-12-31T23:59',
        'status': 'in_progress'
    }
    
    form = InteractionForm(data=data, user=user)
    if form.is_valid():
        print("  ✅ Formulaire d'interaction valide")
        interaction = form.save()
        print(f"  ✅ Interaction créée: {interaction.identifiant}")
    else:
        print("  ❌ Erreurs dans le formulaire d'interaction:")
        for field, errors in form.errors.items():
            print(f"    {field}: {errors}")

def test_interaction_search_form():
    """Test le formulaire de recherche d'interaction"""
    print("\n=== Test du formulaire de recherche d'interaction ===")
    
    form = InteractionSearchForm()
    
    print("  Statuts disponibles dans le formulaire de recherche:")
    for choice in form.fields['status'].choices:
        if choice[0]:  # Ignorer l'option vide
            print(f"    - {choice[0]}: {choice[1]}")

def test_reference_values_management():
    """Test la gestion des valeurs de référence"""
    print("\n=== Test de gestion des valeurs de référence ===")
    
    # Tester l'ajout d'une nouvelle valeur
    new_status, created = ReferenceValue.objects.get_or_create(
        category='interaction_status',
        code='en_attente',
        defaults={
            'label': 'En attente',
            'description': 'Interaction en attente de traitement',
            'sort_order': 4,
            'is_active': True,
            'is_default': False,
            'is_system': False
        }
    )
    
    if created:
        print(f"  ✅ Nouvelle valeur ajoutée: {new_status.code} - {new_status.label}")
    else:
        print(f"  ℹ️  Valeur existante: {new_status.code} - {new_status.label}")
    
    # Vérifier que la nouvelle valeur apparaît dans le formulaire
    form = InteractionForm()
    status_choices = [choice[0] for choice in form.fields['status'].choices if choice[0]]
    
    if 'en_attente' in status_choices:
        print("  ✅ Nouvelle valeur disponible dans le formulaire")
    else:
        print("  ❌ Nouvelle valeur non disponible dans le formulaire")
    
    # Tester la suppression d'une valeur
    if new_status and not new_status.is_system:
        new_status.is_active = False
        new_status.save()
        print(f"  ✅ Valeur désactivée: {new_status.code}")
        
        # Vérifier qu'elle n'apparaît plus dans le formulaire
        form = InteractionForm()
        status_choices = [choice[0] for choice in form.fields['status'].choices if choice[0]]
        
        if 'en_attente' not in status_choices:
            print("  ✅ Valeur supprimée du formulaire")
        else:
            print("  ❌ Valeur toujours présente dans le formulaire")

def test_all_categories():
    """Test toutes les catégories de valeurs de référence"""
    print("\n=== Test de toutes les catégories ===")
    
    categories = ReferenceValue.CATEGORY_CHOICES
    
    for category_code, category_name in categories:
        print(f"\n  Catégorie: {category_name} ({category_code})")
        
        try:
            choices = ReferenceValue.get_choices_for_category(category_code)
            print(f"    Nombre de valeurs: {len(choices)}")
            
            for code, label in choices:
                print(f"      - {code}: {label}")
                
        except Exception as e:
            print(f"    ❌ Erreur: {e}")

def main():
    """Fonction principale"""
    print("🚀 Test d'intégration des valeurs de référence")
    print("=" * 50)
    
    try:
        # Test 1: Initialisation
        test_reference_values_initialization()
        
        # Test 2: Formulaire d'interaction
        test_interaction_form_with_reference_values()
        
        # Test 3: Formulaire de recherche
        test_interaction_search_form()
        
        # Test 4: Gestion des valeurs
        test_reference_values_management()
        
        # Test 5: Toutes les catégories
        test_all_categories()
        
        print("\n" + "=" * 50)
        print("✅ Tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 