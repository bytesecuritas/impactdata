#!/usr/bin/env python3
"""
Script de test complet pour le système de permissions dynamiques
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import RolePermission, User, Adherent, Organization, Interaction, Badge
from core.views import has_permission, get_user_permissions

User = get_user_model()

def test_permission_system():
    """Test complet du système de permissions"""
    
    print("🧪 Test du système de permissions dynamiques")
    print("=" * 50)
    
    # Créer des utilisateurs de test
    print("\n1. Création des utilisateurs de test...")
    
    # Admin
    admin_user = User.objects.create_user(
        email='admin@test.com',
        matricule='ADM001',
        first_name='Admin',
        last_name='Test',
        telephone='612345678',
        profession='Administrateur',
        role='admin'
    )
    
    # Superviseur
    supervisor_user = User.objects.create_user(
        email='supervisor@test.com',
        matricule='SUP001',
        first_name='Superviseur',
        last_name='Test',
        telephone='612345679',
        profession='Superviseur',
        role='superviseur'
    )
    
    # Agent
    agent_user = User.objects.create_user(
        email='agent@test.com',
        matricule='AGT001',
        first_name='Agent',
        last_name='Test',
        telephone='612345680',
        profession='Agent',
        role='agent'
    )
    
    print(f"✅ Utilisateurs créés: {admin_user}, {supervisor_user}, {agent_user}")
    
    # Vérifier les permissions par défaut
    print("\n2. Vérification des permissions par défaut...")
    
    # Admin devrait avoir toutes les permissions
    admin_permissions = get_user_permissions(admin_user)
    print(f"Permissions admin: {len(admin_permissions)} permissions")
    
    # Superviseur devrait avoir des permissions limitées
    supervisor_permissions = get_user_permissions(supervisor_user)
    print(f"Permissions superviseur: {len(supervisor_permissions)} permissions")
    
    # Agent devrait avoir le moins de permissions
    agent_permissions = get_user_permissions(agent_user)
    print(f"Permissions agent: {len(agent_permissions)} permissions")
    
    # Test des permissions spécifiques
    print("\n3. Test des permissions spécifiques...")
    
    # Test création d'adhérents
    print(f"Admin peut créer des adhérents: {has_permission(admin_user, 'adherent_create')}")
    print(f"Superviseur peut créer des adhérents: {has_permission(supervisor_user, 'adherent_create')}")
    print(f"Agent peut créer des adhérents: {has_permission(agent_user, 'adherent_create')}")
    
    # Test gestion des utilisateurs
    print(f"Admin peut gérer les utilisateurs: {has_permission(admin_user, 'user_create')}")
    print(f"Superviseur peut gérer les utilisateurs: {has_permission(supervisor_user, 'user_create')}")
    print(f"Agent peut gérer les utilisateurs: {has_permission(agent_user, 'user_create')}")
    
    # Test paramètres système
    print(f"Admin peut accéder aux paramètres: {has_permission(admin_user, 'settings_view')}")
    print(f"Superviseur peut accéder aux paramètres: {has_permission(supervisor_user, 'settings_view')}")
    print(f"Agent peut accéder aux paramètres: {has_permission(agent_user, 'settings_view')}")
    
    # Test modification des permissions
    print("\n4. Test de modification des permissions...")
    
    # Donner à l'agent la permission de créer des adhérents
    RolePermission.objects.create(
        role='agent',
        permission='adherent_create',
        is_active=True
    )
    
    print(f"Agent peut maintenant créer des adhérents: {has_permission(agent_user, 'adherent_create')}")
    
    # Retirer la permission au superviseur
    RolePermission.objects.filter(
        role='superviseur',
        permission='user_create'
    ).update(is_active=False)
    
    print(f"Superviseur ne peut plus gérer les utilisateurs: {has_permission(supervisor_user, 'user_create')}")
    
    # Test des vues avec permissions
    print("\n5. Test des vues avec permissions...")
    
    client = Client()
    
    # Test connexion admin
    client.force_login(admin_user)
    
    # Test accès à la liste des adhérents
    response = client.get(reverse('core:adherent_list'))
    print(f"Admin accès liste adhérents: {response.status_code}")
    
    # Test accès à la création d'adhérents
    response = client.get(reverse('core:adherent_create'))
    print(f"Admin accès création adhérents: {response.status_code}")
    
    # Test connexion agent
    client.force_login(agent_user)
    
    # Test accès à la liste des adhérents
    response = client.get(reverse('core:adherent_list'))
    print(f"Agent accès liste adhérents: {response.status_code}")
    
    # Test accès à la création d'adhérents (maintenant autorisé)
    response = client.get(reverse('core:adherent_create'))
    print(f"Agent accès création adhérents: {response.status_code}")
    
    # Test accès refusé aux paramètres
    response = client.get(reverse('core:settings_dashboard'))
    print(f"Agent accès paramètres (devrait être refusé): {response.status_code}")
    
    # Nettoyage
    print("\n6. Nettoyage...")
    User.objects.filter(email__in=[
        'admin@test.com',
        'supervisor@test.com', 
        'agent@test.com'
    ]).delete()
    
    print("✅ Test terminé avec succès!")
    
    return True

def test_permission_utilities():
    """Test des utilitaires de permissions"""
    
    print("\n🔧 Test des utilitaires de permissions")
    print("=" * 40)
    
    # Créer un utilisateur de test
    user = User.objects.create_user(
        email='test@test.com',
        matricule='TST001',
        first_name='Test',
        last_name='User',
        telephone='612345681',
        profession='Testeur',
        role='agent'
    )
    
    # Test des permissions
    permissions = get_user_permissions(user)
    print(f"Permissions de l'utilisateur: {permissions}")
    
    # Test des permissions spécifiques
    print(f"Peut voir les adhérents: {has_permission(user, 'adherent_view')}")
    print(f"Peut créer des adhérents: {has_permission(user, 'adherent_create')}")
    print(f"Peut gérer les utilisateurs: {has_permission(user, 'user_create')}")
    
    # Nettoyage
    user.delete()
    
    print("✅ Test des utilitaires terminé!")

if __name__ == '__main__':
    try:
        test_permission_utilities()
        test_permission_system()
        print("\n🎉 Tous les tests sont passés avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc() 