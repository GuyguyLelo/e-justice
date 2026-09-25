#!/usr/bin/env python
"""
Script d'initialisation des données pour e-Detenu
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edetenu.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.comptes.models import Role

User = get_user_model()

def create_superuser():
    """Crée un superutilisateur par défaut"""
    username = 'admin'
    email = 'admin@edetenu.rdc'
    password = 'admin123'
    
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Administrateur',
            last_name='Système',
            role=Role.ADMIN,
            telephone='+243 123 456 789',
            adresse='Kinshasa, RDC'
        )
        print(f"✅ Superutilisateur créé: {username} / {password}")
    else:
        print(f"ℹ️  Superutilisateur existe déjà: {username}")

def create_demo_users():
    """Crée des utilisateurs de démonstration"""
    users_data = [
        {
            'username': 'directeur',
            'email': 'directeur@edetenu.rdc',
            'password': 'directeur123',
            'first_name': 'Jean',
            'last_name': 'Mukamba',
            'role': Role.DIRECTEUR,
            'telephone': '+243 123 456 780',
            'adresse': 'Kinshasa, RDC'
        },
        {
            'username': 'agent1',
            'email': 'agent1@edetenu.rdc',
            'password': 'agent123',
            'first_name': 'Marie',
            'last_name': 'Kabila',
            'role': Role.AGENT,
            'telephone': '+243 123 456 781',
            'adresse': 'Kinshasa, RDC'
        },
        {
            'username': 'medecin1',
            'email': 'medecin1@edetenu.rdc',
            'password': 'medecin123',
            'first_name': 'Dr. Paul',
            'last_name': 'Tshisekedi',
            'role': Role.MEDECIN,
            'telephone': '+243 123 456 782',
            'adresse': 'Kinshasa, RDC'
        }
    ]
    
    for user_data in users_data:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(**user_data)
            print(f"✅ Utilisateur créé: {user_data['username']} / {user_data['password']}")
        else:
            print(f"ℹ️  Utilisateur existe déjà: {user_data['username']}")

def main():
    """Fonction principale"""
    print("🚀 Initialisation des données pour e-Detenu...")
    
    try:
        create_superuser()
        create_demo_users()
        print("\n✅ Initialisation terminée avec succès!")
        print("\n📋 Comptes créés:")
        print("   - admin / admin123 (Administrateur)")
        print("   - directeur / directeur123 (Directeur)")
        print("   - agent1 / agent123 (Agent)")
        print("   - medecin1 / medecin123 (Médecin)")
        print("\n🌐 Accès à l'API:")
        print("   - Documentation: http://localhost:8000/api/docs/")
        print("   - Authentification: http://localhost:8000/api/auth/auth/login/")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()






