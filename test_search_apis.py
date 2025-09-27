#!/usr/bin/env python3
"""
Script de test pour vérifier que les APIs de recherche fonctionnent correctement
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'impactData.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from core.models import Adherent, Organization, Category

User = get_user_model()

def test_search_apis():
    """Test des APIs de recherche"""
    client = Client()
    
    # Créer un utilisateur de test
    user = User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User',
        matricule='TEST001'
    )
    
    # Se connecter
    client.force_login(user)
    
    print("🧪 Test des APIs de recherche...")
    
    # Test 1: API Personnel
    print("\n1. Test API Personnel...")
    response = client.get('/api/personnel/search/?q=test')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Résultats: {len(data.get('results', []))}")
    else:
        print(f"   Erreur: {response.content}")
    
    # Test 2: API Adhérent
    print("\n2. Test API Adhérent...")
    response = client.get('/api/adherent/search/?q=test')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Résultats: {len(data.get('results', []))}")
    else:
        print(f"   Erreur: {response.content}")
    
    # Test 3: API Organisation
    print("\n3. Test API Organisation...")
    response = client.get('/api/organization/search/?q=test')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Résultats: {len(data.get('results', []))}")
    else:
        print(f"   Erreur: {response.content}")
    
    # Test 4: API Catégorie
    print("\n4. Test API Catégorie...")
    response = client.get('/api/category/search/?q=test')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Résultats: {len(data.get('results', []))}")
    else:
        print(f"   Erreur: {response.content}")
    
    print("\n✅ Tests terminés!")
    
    # Nettoyage
    user.delete()

if __name__ == '__main__':
    test_search_apis()
