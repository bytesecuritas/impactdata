#!/usr/bin/env python3
"""
Script de test pour le système de permissions
Ce script teste le système de permissions et initialise les permissions par défaut.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from core.models import User, RolePermission, Adherent, Organization, Interaction
from core.views import has_permission, get_user_permissions, can_access_data

def test_permission_system():
    """Teste le système de permissions"""
    print("=== TEST DU SYSTÈME DE PERMISSIONS ===\n")
    
    # 1. Vérifier que les permissions existent
    print("1. Vérification des permissions existantes...")
    permissions = RolePermission.objects.all()
    print(f"   - {permissions.count()} permissions trouvées")
    
    if permissions.count() == 0:
        print("   ⚠️  Aucune permission trouvée. Initialisation des permissions par défaut...")
        initialize_default_permissions()
        permissions = RolePermission.objects.all()
        print(f"   ✅ {permissions.count()} permissions initialisées")
    
    # 2. Tester avec différents utilisateurs
    print("\n2. Test avec différents utilisateurs...")
    
    # Trouver des utilisateurs de chaque rôle
    admin_users = User.objects.filter(role='admin', is_active=True)[:1]
    superviseur_users = User.objects.filter(role='superviseur', is_active=True)[:1]
    agent_users = User.objects.filter(role='agent', is_active=True)[:1]
    
    test_users = []
    if admin_users:
        test_users.append(('Admin', admin_users[0]))
    if superviseur_users:
        test_users.append(('Superviseur', superviseur_users[0]))
    if agent_users:
        test_users.append(('Agent', agent_users[0]))
    
    if not test_users:
        print("   ⚠️  Aucun utilisateur trouvé pour les tests")
        return
    
    # Tester les permissions pour chaque utilisateur
    for role_name, user in test_users:
        print(f"\n   --- {role_name}: {user.get_full_name()} ---")
        
        # Permissions de base
        permissions_list = get_user_permissions(user)
        print(f"   Permissions actives: {len(permissions_list)}")
        
        # Test de permissions spécifiques
        test_permissions = [
            'adherent_create', 'adherent_view', 'adherent_edit', 'adherent_delete',
            'organization_create', 'organization_view', 'organization_edit', 'organization_delete',
            'interaction_create', 'interaction_view', 'interaction_edit', 'interaction_delete',
            'user_create', 'user_view', 'user_edit', 'user_delete',
            'settings_view', 'settings_edit'
        ]
        
        for perm in test_permissions:
            has_perm = has_permission(user, perm)
            status = "✅" if has_perm else "❌"
            print(f"   {status} {perm}")
    
    # 3. Test d'accès aux données
    print("\n3. Test d'accès aux données...")
    
    if test_users:
        test_user = test_users[0][1]  # Premier utilisateur disponible
        
        # Test d'accès aux adhérents
        can_read_adherents = can_access_data(test_user, 'read', data_category='adherent')
        can_create_adherents = can_access_data(test_user, 'create', data_category='adherent')
        can_update_adherents = can_access_data(test_user, 'update', data_category='adherent')
        can_delete_adherents = can_access_data(test_user, 'delete', data_category='adherent')
        
        print(f"   Utilisateur: {test_user.get_full_name()} ({test_user.role})")
        print(f"   - Lecture adhérents: {'✅' if can_read_adherents else '❌'}")
        print(f"   - Création adhérents: {'✅' if can_create_adherents else '❌'}")
        print(f"   - Modification adhérents: {'✅' if can_update_adherents else '❌'}")
        print(f"   - Suppression adhérents: {'✅' if can_delete_adherents else '❌'}")
    
    print("\n=== FIN DES TESTS ===\n")

def initialize_default_permissions():
    """Initialise les permissions par défaut pour chaque rôle"""
    print("Initialisation des permissions par défaut...")
    
    # Permissions par défaut pour chaque rôle
    default_permissions = {
        'admin': [
            # Gestion des utilisateurs
            'user_create', 'user_edit', 'user_delete', 'user_view', 'user_activate',
            # Gestion des adhérents
            'adherent_create', 'adherent_edit', 'adherent_delete', 'adherent_view',
            # Gestion des organisations
            'organization_create', 'organization_edit', 'organization_delete', 'organization_view',
            # Gestion des interactions
            'interaction_create', 'interaction_edit', 'interaction_delete', 'interaction_view',
            # Gestion des badges
            'badge_create', 'badge_edit', 'badge_delete', 'badge_view', 'badge_revoke',
            # Gestion des objectifs
            'objective_create', 'objective_edit', 'objective_delete', 'objective_view',
            # Gestion des paramètres
            'settings_view', 'settings_edit', 'settings_roles', 'settings_references',
            # Rapports et statistiques
            'reports_view', 'reports_export', 'stats_view',
            # Administration système
            'system_admin', 'data_backup', 'data_restore',
        ],
        'superviseur': [
            # Gestion des utilisateurs (agents seulement)
            'user_create', 'user_edit', 'user_view',
            # Gestion des adhérents
            'adherent_create', 'adherent_edit', 'adherent_delete', 'adherent_view',
            # Gestion des organisations
            'organization_create', 'organization_edit', 'organization_delete', 'organization_view',
            # Gestion des interactions
            'interaction_create', 'interaction_edit', 'interaction_delete', 'interaction_view',
            # Gestion des badges
            'badge_create', 'badge_edit', 'badge_view', 'badge_revoke',
            # Gestion des objectifs
            'objective_create', 'objective_edit', 'objective_delete', 'objective_view',
            # Paramètres (lecture seulement)
            'settings_view',
            # Rapports et statistiques
            'reports_view', 'stats_view',
        ],
        'agent': [
            # Gestion des adhérents (lecture et création)
            'adherent_create', 'adherent_view',
            # Gestion des organisations (lecture et création)
            'organization_create', 'organization_view',
            # Gestion des interactions (lecture et création)
            'interaction_create', 'interaction_view',
            # Gestion des badges (lecture seulement)
            'badge_view',
            # Objectifs (lecture seulement)
            'objective_view',
        ]
    }
    
    # Créer les permissions
    created_count = 0
    for role, permissions in default_permissions.items():
        for permission in permissions:
            permission_obj, created = RolePermission.objects.get_or_create(
                role=role,
                permission=permission,
                defaults={'is_active': True}
            )
            if created:
                created_count += 1
    
    print(f"✅ {created_count} permissions créées")

def test_permission_changes():
    """Teste les changements de permissions en temps réel"""
    print("\n=== TEST DES CHANGEMENTS DE PERMISSIONS ===\n")
    
    # Trouver un agent pour tester
    agent = User.objects.filter(role='agent', is_active=True).first()
    if not agent:
        print("❌ Aucun agent trouvé pour le test")
        return
    
    print(f"Agent de test: {agent.get_full_name()}")
    
    # Vérifier les permissions initiales
    print("\n1. Permissions initiales:")
    initial_permissions = get_user_permissions(agent)
    print(f"   - {len(initial_permissions)} permissions actives")
    
    # Tester la permission de création d'adhérents
    can_create_before = has_permission(agent, 'adherent_create')
    print(f"   - Peut créer des adhérents: {'✅' if can_create_before else '❌'}")
    
    # Ajouter la permission de création d'adhérents
    print("\n2. Ajout de la permission 'adherent_create'...")
    permission, created = RolePermission.objects.get_or_create(
        role='agent',
        permission='adherent_create',
        defaults={'is_active': True}
    )
    
    if created:
        print("   ✅ Permission créée")
    else:
        permission.is_active = True
        permission.save()
        print("   ✅ Permission activée")
    
    # Vérifier que la permission est maintenant active
    can_create_after = has_permission(agent, 'adherent_create')
    print(f"   - Peut maintenant créer des adhérents: {'✅' if can_create_after else '❌'}")
    
    # Désactiver la permission
    print("\n3. Désactivation de la permission 'adherent_create'...")
    permission.is_active = False
    permission.save()
    
    can_create_final = has_permission(agent, 'adherent_create')
    print(f"   - Peut encore créer des adhérents: {'✅' if can_create_final else '❌'}")
    
    print("\n✅ Test des changements de permissions terminé")

def test_form_access():
    """Teste l'accès aux formulaires basé sur les permissions"""
    print("\n=== TEST D'ACCÈS AUX FORMULAIRES ===\n")
    
    # Trouver un utilisateur pour tester
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("❌ Aucun utilisateur trouvé pour le test")
        return
    
    print(f"Utilisateur de test: {user.get_full_name()} ({user.role})")
    
    # Tester les permissions pour les formulaires
    form_permissions = {
        'Formulaire de création d\'adhérent': 'adherent_create',
        'Formulaire de modification d\'adhérent': 'adherent_edit',
        'Formulaire de création d\'organisation': 'organization_create',
        'Formulaire de modification d\'organisation': 'organization_edit',
        'Formulaire de création d\'interaction': 'interaction_create',
        'Formulaire de modification d\'interaction': 'interaction_edit',
    }
    
    for form_name, permission in form_permissions.items():
        has_perm = has_permission(user, permission)
        status = "✅" if has_perm else "❌"
        print(f"   {status} {form_name}: {permission}")

def main():
    """Fonction principale"""
    print("🔐 TEST DU SYSTÈME DE PERMISSIONS DYNAMIQUES")
    print("=" * 50)
    
    try:
        # Test principal
        test_permission_system()
        
        # Test des changements de permissions
        test_permission_changes()
        
        # Test d'accès aux formulaires
        test_form_access()
        
        print("\n🎉 Tous les tests terminés avec succès!")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 