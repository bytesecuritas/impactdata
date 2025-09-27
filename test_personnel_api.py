#!/usr/bin/env python3
"""
Test spécifique de l'API personnel
"""

import requests
import json

def test_personnel_api():
    base_url = "http://localhost:8000"
    
    print("🧪 Test spécifique de l'API personnel...")
    
    try:
        response = requests.get(f"{base_url}/core/api/personnel/search/?q=test", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Résultats: {data}")
        else:
            print(f"Erreur: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion: {e}")
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == '__main__':
    test_personnel_api()
