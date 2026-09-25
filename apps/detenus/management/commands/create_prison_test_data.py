from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.detenus.models import CentrePenitencier, AdminPrison, TypeCentre
from datetime import date

class Command(BaseCommand):
    help = 'Créer des données de test pour le système de gestion des prisons'

    def handle(self, *args, **options):
        self.stdout.write('Création des données de test...')
        
        # Créer des centres pénitenciers
        centres_data = [
            {
                'nom': 'Maison d\'Arrêt de Paris',
                'code': 'MAP001',
                'type_centre': TypeCentre.MAISON_D_ARRET,
                'adresse': '123 Rue de la Prison, 75001 Paris',
                'telephone': '01 23 45 67 89',
                'email': 'contact@map.fr',
                'capacite_max': 500,
                'capacite_actuelle': 450,
                'directeur': 'Jean Dupont',
                'date_ouverture': date(1980, 1, 15),
                'statut': True
            },
            {
                'nom': 'Centre de Détention de Lyon',
                'code': 'CDL002',
                'type_centre': TypeCentre.CENTRE_DE_DETENTION,
                'adresse': '456 Avenue de la Liberté, 69000 Lyon',
                'telephone': '04 56 78 90 12',
                'email': 'info@cdl.fr',
                'capacite_max': 800,
                'capacite_actuelle': 720,
                'directeur': 'Marie Martin',
                'date_ouverture': date(1995, 3, 20),
                'statut': True
            },
            {
                'nom': 'Établissement Pénitentiaire de Marseille',
                'code': 'EPM003',
                'type_centre': TypeCentre.ETABLISSEMENT_PENITENTIAIRE,
                'adresse': '789 Boulevard du Port, 13000 Marseille',
                'telephone': '04 91 23 45 67',
                'email': 'contact@epm.fr',
                'capacite_max': 1200,
                'capacite_actuelle': 1100,
                'directeur': 'Pierre Durand',
                'date_ouverture': date(2000, 6, 10),
                'statut': True
            }
        ]
        
        created_centres = []
        for centre_data in centres_data:
            centre, created = CentrePenitencier.objects.get_or_create(
                code=centre_data['code'],
                defaults=centre_data
            )
            if created:
                created_centres.append(centre)
                self.stdout.write(f'✓ Centre créé: {centre.nom}')
            else:
                self.stdout.write(f'- Centre existe déjà: {centre.nom}')
        
        # Créer des utilisateurs et admins de prison
        admins_data = [
            {
                'username': 'admin_paris',
                'email': 'admin.paris@prison.fr',
                'first_name': 'Jean',
                'last_name': 'Dupont',
                'password': 'admin123',
                'centre_code': 'MAP001',
                'matricule_admin': 'ADM001',
                'poste': 'Directeur Adjoint',
                'date_affectation': date(2020, 1, 15),
                'statut': True
            },
            {
                'username': 'admin_lyon',
                'email': 'admin.lyon@prison.fr',
                'first_name': 'Marie',
                'last_name': 'Martin',
                'password': 'admin123',
                'centre_code': 'CDL002',
                'matricule_admin': 'ADM002',
                'poste': 'Responsable Administratif',
                'date_affectation': date(2019, 3, 20),
                'statut': True
            },
            {
                'username': 'admin_marseille',
                'email': 'admin.marseille@prison.fr',
                'first_name': 'Pierre',
                'last_name': 'Durand',
                'password': 'admin123',
                'centre_code': 'EPM003',
                'matricule_admin': 'ADM003',
                'poste': 'Chef de Service',
                'date_affectation': date(2021, 6, 10),
                'statut': True
            }
        ]
        
        for admin_data in admins_data:
            # Créer l'utilisateur
            user, user_created = User.objects.get_or_create(
                username=admin_data['username'],
                defaults={
                    'email': admin_data['email'],
                    'first_name': admin_data['first_name'],
                    'last_name': admin_data['last_name'],
                    'is_staff': True,
                    'is_active': True
                }
            )
            
            if user_created:
                user.set_password(admin_data['password'])
                user.save()
                self.stdout.write(f'✓ Utilisateur créé: {user.username}')
            else:
                self.stdout.write(f'- Utilisateur existe déjà: {user.username}')
            
            # Créer l'admin de prison
            centre = CentrePenitencier.objects.get(code=admin_data['centre_code'])
            admin, admin_created = AdminPrison.objects.get_or_create(
                utilisateur=user,
                defaults={
                    'centre': centre,
                    'matricule_admin': admin_data['matricule_admin'],
                    'poste': admin_data['poste'],
                    'date_affectation': admin_data['date_affectation'],
                    'statut': admin_data['statut']
                }
            )
            
            if admin_created:
                self.stdout.write(f'✓ Admin de prison créé: {admin.utilisateur.get_full_name()} - {centre.nom}')
            else:
                self.stdout.write(f'- Admin de prison existe déjà: {admin.utilisateur.get_full_name()} - {centre.nom}')
        
        self.stdout.write(self.style.SUCCESS('✅ Données de test créées avec succès!'))
        self.stdout.write('\nUtilisateurs de test créés:')
        self.stdout.write('- admin_paris / admin123 (Maison d\'Arrêt de Paris)')
        self.stdout.write('- admin_lyon / admin123 (Centre de Détention de Lyon)')
        self.stdout.write('- admin_marseille / admin123 (Établissement Pénitentiaire de Marseille)')
        self.stdout.write('\nAccès aux pages:')
        self.stdout.write('- Dashboard: http://127.0.0.1:8000/api/detenus/web/dashboard-central/')
        self.stdout.write('- Centres: http://127.0.0.1:8000/api/detenus/web/centres/')
        self.stdout.write('- Admins: http://127.0.0.1:8000/api/detenus/web/admins-prison/')
