#!/usr/bin/env python
"""
Script de test pour vérifier les fonctionnalités des paramètres
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import GeneralParameter, ReferenceValue, RolePermission, SystemLog, User
from django.contrib.auth import get_user_model

def test_general_parameters():
    """Test des paramètres généraux"""
    print("=== Test des paramètres généraux ===")
    
    # Créer un paramètre de test
    param = GeneralParameter.objects.create(
        parameter_key='test_param',
        parameter_type='text',
        value='valeur_test',
        description='Paramètre de test'
    )
    print(f"Paramètre créé: {param}")
    
    # Tester la récupération
    value = GeneralParameter.get_value('test_param', 'default')
    print(f"Valeur récupérée: {value}")
    
    # Tester la modification
    GeneralParameter.set_value('test_param', 'nouvelle_valeur')
    value = GeneralParameter.get_value('test_param')
    print(f"Nouvelle valeur: {value}")
    
    # Nettoyer
    param.delete()
    print("✓ Test des paramètres généraux réussi\n")

def test_reference_values():
    """Test des valeurs de référence"""
    print("=== Test des valeurs de référence ===")
    
    # Créer une valeur de référence
    ref = ReferenceValue.objects.create(
        category='test_category',
        code='TEST001',
        label='Valeur de test',
        description='Description de test'
    )
    print(f"Valeur de référence créée: {ref}")
    
    # Tester la récupération des choix
    choices = ReferenceValue.get_choices_for_category('test_category')
    print(f"Choix pour la catégorie: {list(choices)}")
    
    # Nettoyer
    ref.delete()
    print("✓ Test des valeurs de référence réussi\n")

def test_role_permissions():
    """Test des permissions de rôle"""
    print("=== Test des permissions de rôle ===")
    
    # Créer une permission
    permission = RolePermission.objects.create(
        role='admin',
        permission='user_create',
        is_active=True
    )
    print(f"Permission créée: {permission}")
    
    # Nettoyer
    permission.delete()
    print("✓ Test des permissions de rôle réussi\n")

def test_system_log():
    """Test du journal système"""
    print("=== Test du journal système ===")
    
    # Créer un utilisateur de test
    User = get_user_model()
    try:
        user = User.objects.get(email='test@example.com')
    except User.DoesNotExist:
        user = User.objects.create_user(
            email='test@example.com',
            matricule='TEST001',
            first_name='Test',
            last_name='User',
            telephone='612345678',
            profession='Testeur'
        )
    
    # Tester la création d'un log
    log = SystemLog.log(
        level='INFO',
        category='general',
        message='Test de journal système',
        user=user,
        details={'test': 'data'}
    )
    print(f"Log créé: {log}")
    
    # Nettoyer
    log.delete()
    user.delete()
    print("✓ Test du journal système réussi\n")

def test_parameter_integration():
    """Test de l'intégration des paramètres dans le système"""
    print("=== Test de l'intégration des paramètres ===")
    
    # Créer des paramètres système
    params = [
        ('organization_name', 'Nom de l\'organisation', 'Impact Data'),
        ('email_host', 'Serveur SMTP', 'smtp.example.com'),
        ('session_timeout', 'Délai d\'expiration de session (minutes)', '30'),
        ('enable_notifications', 'Activer les notifications', 'true'),
    ]
    
    for key, description, value in params:
        param, created = GeneralParameter.objects.get_or_create(
            parameter_key=key,
            defaults={
                'parameter_type': 'text',
                'value': value,
                'description': description
            }
        )
        if not created:
            param.value = value
            param.save()
        print(f"Paramètre {key}: {param.get_typed_value()}")
    
    # Tester l'utilisation des paramètres
    org_name = GeneralParameter.get_value('organization_name', 'Organisation par défaut')
    session_timeout = GeneralParameter.get_value('session_timeout', 60)
    notifications_enabled = GeneralParameter.get_value('enable_notifications', False)
    
    print(f"Nom de l'organisation: {org_name}")
    print(f"Délai de session: {session_timeout} minutes")
    print(f"Notifications activées: {notifications_enabled}")
    
    # Nettoyer
    for key, _, _ in params:
        GeneralParameter.objects.filter(parameter_key=key).delete()
    
    print("✓ Test de l'intégration des paramètres réussi\n")

def main():
    """Fonction principale de test"""
    print("Début des tests des fonctionnalités de paramètres...\n")
    
    try:
        test_general_parameters()
        test_reference_values()
        test_role_permissions()
        test_system_log()
        test_parameter_integration()
        
        print("🎉 Tous les tests sont passés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 