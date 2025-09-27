#!/usr/bin/env python3
"""
Test simple des APIs de recherche
"""

import requests
import json

def test_apis():
    base_url = "http://localhost:8000"
    
    apis = [
        "/core/api/personnel/search/",
        "/core/api/adherent/search/",
        "/core/api/organization/search/",
        "/core/api/category/search/"
    ]
    
    print("🧪 Test des APIs de recherche...")
    
    for api in apis:
        print(f"\n🔍 Test de {api}")
        try:
            response = requests.get(f"{base_url}{api}?q=test", timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Résultats: {len(data.get('results', []))}")
            else:
                print(f"   Erreur: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"   Erreur de connexion: {e}")
        except Exception as e:
            print(f"   Erreur: {e}")

if __name__ == '__main__':
    test_apis()
