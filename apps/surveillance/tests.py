from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from apps.detenus.models import CentrePenitencier, Detenu
from .models import (
    Camera, ZoneSurveillance, ProfilFacialDetenu, 
    DetectionFaciale, AlerteSurveillance
)

Utilisateur = get_user_model()


class CameraModelTest(TestCase):
    """Test du modèle Camera"""
    
    def setUp(self):
        self.centre = CentrePenitencier.objects.create(
            nom="Centre Test",
            code="CT001",
            type_centre="PRISON",
            adresse="Adresse test",
            capacite_max=100,
            date_ouverture=timezone.now().date()
        )
        
        self.camera = Camera.objects.create(
            nom="Camera Test",
            code="CAM001",
            centre=self.centre,
            type_camera="INTERIEURE",
            emplacement="Couloir principal",
            adresse_ip="192.168.1.100",
            port=554,
            statut="ACTIVE"
        )
    
    def test_camera_creation(self):
        """Test la création d'une caméra"""
        self.assertEqual(self.camera.nom, "Camera Test")
        self.assertEqual(self.camera.code, "CAM001")
        self.assertEqual(self.camera.centre, self.centre)
        self.assertEqual(self.camera.statut, "ACTIVE")
    
    def test_camera_str(self):
        """Test la représentation string d'une caméra"""
        expected = "Camera Test - Centre Test"
        self.assertEqual(str(self.camera), expected)
    
    def test_est_en_ligne(self):
        """Test la propriété est_en_ligne"""
        self.assertTrue(self.camera.est_en_ligne)
        
        self.camera.statut = "INACTIVE"
        self.camera.save()
        self.assertFalse(self.camera.est_en_ligne)
    
    def test_url_complete(self):
        """Test la construction de l'URL complète"""
        expected = "rtsp://192.168.1.100:554/stream"
        self.assertEqual(self.camera.url_complete, expected)
        
        # Test avec URL flux direct
        self.camera.adresse_ip = None
        self.camera.url_flux = "http://example.com/stream"
        self.camera.save()
        self.assertEqual(self.camera.url_complete, "http://example.com/stream")


class ZoneSurveillanceModelTest(TestCase):
    """Test du modèle ZoneSurveillance"""
    
    def setUp(self):
        self.centre = CentrePenitencier.objects.create(
            nom="Centre Test",
            code="CT001",
            type_centre="PRISON",
            adresse="Adresse test",
            capacite_max=100,
            date_ouverture=timezone.now().date()
        )
        
        self.camera = Camera.objects.create(
            nom="Camera Test",
            code="CAM001",
            centre=self.centre,
            type_camera="INTERIEURE",
            emplacement="Couloir principal",
            statut="ACTIVE"
        )
        
        self.zone = ZoneSurveillance.objects.create(
            camera=self.camera,
            nom="Zone Test",
            coordonnees=[100, 100, 200, 100, 200, 200, 100, 200],
            type_zone="COULOIR",
            seuil_alerte=2
        )
    
    def test_zone_creation(self):
        """Test la création d'une zone de surveillance"""
        self.assertEqual(self.zone.nom, "Zone Test")
        self.assertEqual(self.zone.camera, self.camera)
        self.assertEqual(self.zone.type_zone, "COULOIR")
        self.assertEqual(self.zone.seuil_alerte, 2)
    
    def test_zone_str(self):
        """Test la représentation string d'une zone"""
        expected = "Zone Test - Camera Test"
        self.assertEqual(str(self.zone), expected)


class ProfilFacialDetenuModelTest(TestCase):
    """Test du modèle ProfilFacialDetenu"""
    
    def setUp(self):
        self.utilisateur = Utilisateur.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.centre = CentrePenitencier.objects.create(
            nom="Centre Test",
            code="CT001",
            type_centre="PRISON",
            adresse="Adresse test",
            capacite_max=100,
            date_ouverture=timezone.now().date()
        )
        
        self.detenu = Detenu.objects.create(
            matricule="D001",
            nom="Doe",
            prenom="John",
            sexe="M",
            date_naissance="1990-01-01",
            lieu_naissance="Kinshasa",
            date_arrestation=timezone.now().date(),
            date_incarceration=timezone.now().date(),
            motif_incarceration="Test",
            tribunal="Tribunal Test",
            cellule="A101",
            centre=self.centre
        )
    
    def test_profil_creation(self):
        """Test la création d'un profil facial"""
        profil = ProfilFacialDetenu.objects.create(
            detenu=self.detenu,
            encodage_facial=[0.1, 0.2, 0.3],
            qualite_image="BONNE",
            created_by=self.utilisateur
        )
        
        self.assertEqual(profil.detenu, self.detenu)
        self.assertEqual(profil.qualite_image, "BONNE")
        self.assertTrue(profil.actif)
    
    def test_profil_str(self):
        """Test la représentation string d'un profil"""
        profil = ProfilFacialDetenu.objects.create(
            detenu=self.detenu,
            encodage_facial=[0.1, 0.2, 0.3],
            created_by=self.utilisateur
        )
        
        expected = "Profil facial - Doe John"
        self.assertEqual(str(profil), expected)


class DetectionFacialeModelTest(TestCase):
    """Test du modèle DetectionFaciale"""
    
    def setUp(self):
        self.utilisateur = Utilisateur.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.centre = CentrePenitencier.objects.create(
            nom="Centre Test",
            code="CT001",
            type_centre="PRISON",
            adresse="Adresse test",
            capacite_max=100,
            date_ouverture=timezone.now().date()
        )
        
        self.camera = Camera.objects.create(
            nom="Camera Test",
            code="CAM001",
            centre=self.centre,
            type_camera="INTERIEURE",
            emplacement="Couloir principal",
            statut="ACTIVE"
        )
        
        self.detenu = Detenu.objects.create(
            matricule="D001",
            nom="Doe",
            prenom="John",
            sexe="M",
            date_naissance="1990-01-01",
            lieu_naissance="Kinshasa",
            date_arrestation=timezone.now().date(),
            date_incarceration=timezone.now().date(),
            motif_incarceration="Test",
            tribunal="Tribunal Test",
            cellule="A101",
            centre=self.centre
        )
        
        self.detection = DetectionFaciale.objects.create(
            camera=self.camera,
            detenu=self.detenu,
            confiance=Decimal('85.50'),
            coordonnees_visage=[100, 100, 200, 200],
            timestamp=timezone.now(),
            est_alerte=False
        )
    
    def test_detection_creation(self):
        """Test la création d'une détection faciale"""
        self.assertEqual(self.detection.camera, self.camera)
        self.assertEqual(self.detection.detenu, self.detenu)
        self.assertEqual(self.detection.confiance, Decimal('85.50'))
        self.assertFalse(self.detection.est_alerte)
    
    def test_est_identifie(self):
        """Test la propriété est_identifie"""
        self.assertTrue(self.detection.est_identifie)
        
        # Test avec détenu None
        self.detection.detenu = None
        self.detection.save()
        self.assertFalse(self.detection.est_identifie)
    
    def test_niveau_confiance(self):
        """Test la propriété niveau_confiance"""
        self.assertEqual(self.detection.niveau_confiance, 'Élevé')
        
        self.detection.confiance = Decimal('70.00')
        self.detection.save()
        self.assertEqual(self.detection.niveau_confiance, 'Moyen')
        
        self.detection.confiance = Decimal('50.00')
        self.detection.save()
        self.assertEqual(self.detection.niveau_confiance, 'Faible')
    
    def test_detection_str(self):
        """Test la représentation string d'une détection"""
        expected = "Detection - Doe John - Camera Test"
        self.assertEqual(str(self.detection), expected)


class AlerteSurveillanceModelTest(TestCase):
    """Test du modèle AlerteSurveillance"""
    
    def setUp(self):
        self.centre = CentrePenitencier.objects.create(
            nom="Centre Test",
            code="CT001",
            type_centre="PRISON",
            adresse="Adresse test",
            capacite_max=100,
            date_ouverture=timezone.now().date()
        )
        
        self.camera = Camera.objects.create(
            nom="Camera Test",
            code="CAM001",
            centre=self.centre,
            type_camera="INTERIEURE",
            emplacement="Couloir principal",
            statut="ACTIVE"
        )
        
        self.detenu = Detenu.objects.create(
            matricule="D001",
            nom="Doe",
            prenom="John",
            sexe="M",
            date_naissance="1990-01-01",
            lieu_naissance="Kinshasa",
            date_arrestation=timezone.now().date(),
            date_incarceration=timezone.now().date(),
            motif_incarceration="Test",
            tribunal="Tribunal Test",
            cellule="A101",
            centre=self.centre
        )
        
        self.alerte = AlerteSurveillance.objects.create(
            titre="Alerte Test",
            type_alerte="DETECTION_INCONNUE",
            niveau="ATTENTION",
            description="Test description",
            camera=self.camera,
            detenu=self.detenu
        )
    
    def test_alerte_creation(self):
        """Test la création d'une alerte"""
        self.assertEqual(self.alerte.titre, "Alerte Test")
        self.assertEqual(self.alerte.type_alerte, "DETECTION_INCONNUE")
        self.assertEqual(self.alerte.niveau, "ATTENTION")
        self.assertEqual(self.alerte.statut, "OUVERTE")
    
    def test_est_ouverte(self):
        """Test la propriété est_ouverte"""
        self.assertTrue(self.alerte.est_ouverte)
        
        self.alerte.statut = "RESOLUE"
        self.alerte.save()
        self.assertFalse(self.alerte.est_ouverte)
    
    def test_alerte_str(self):
        """Test la représentation string d'une alerte"""
        expected = "Alerte Test - Attention"
        self.assertEqual(str(self.alerte), expected)
