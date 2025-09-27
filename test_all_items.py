#!/usr/bin/env python3
"""
Test des APIs avec paramètre vide pour vérifier qu'elles retournent tous les éléments
"""

import requests
import json

def test_apis_empty():
    base_url = "http://localhost:8000"
    
    print("🧪 Test des APIs avec paramètre vide...")
    
    apis = [
        "/core/api/personnel/search/",
        "/core/api/adherent/search/",
        "/core/api/organization/search/",
        "/core/api/category/search/"
    ]
    
    for api in apis:
        print(f"\n🔍 Test de {api} (sans paramètre q)")
        try:
            response = requests.get(f"{base_url}{api}", timeout=5)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Résultats: {len(data.get('results', []))}")
                if data.get('results'):
                    print(f"   Premier résultat: {data['results'][0]}")
            else:
                print(f"   Erreur: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"   Erreur de connexion: {e}")
        except Exception as e:
            print(f"   Erreur: {e}")

if __name__ == '__main__':
    test_apis_empty()
