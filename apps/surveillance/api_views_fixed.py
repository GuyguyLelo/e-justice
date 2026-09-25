from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.utils import timezone
import json
import base64
import cv2
import face_recognition
import numpy as np
from PIL import Image
import io
from .models import ProfilFacialDetenu, DetectionFaciale, Camera
from apps.detenus.models import Detenu
from .biometric_service import biometric_service
import logging

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def initialiser_systeme(request):
    """Initialise le système en encodant tous les détenus avec photos"""
    try:
        # Charger les données biométriques
        biometric_service.load_biometric_data()
        
        # Compter les profils créés
        total_detenus = Detenu.objects.exclude(photo_face='').count()
        profils_encodes = len(biometric_service.known_face_ids)
        
        return JsonResponse({
            'success': True,
            'message': f'Système initialisé avec {profils_encodes} profils encodés',
            'profils_crees': profils_encodes,
            'total_detenus': total_detenus
        })
        
    except Exception as e:
        logger.error(f'Erreur initialisation: {e}')
        return JsonResponse({
            'error': f'Erreur lors de l\'initialisation: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def encoder_visage_detenu(request, detenu_id):
    """Encode le visage d'un détenu et l'ajoute à la base biométrique"""
    try:
        detenu = Detenu.objects.get(id=detenu_id)
        
        if not detenu.photo_face:
            return JsonResponse({
                'error': 'Le détenu n\'a pas de photo faciale'
            }, status=400)
        
        # Encoder le visage
        encoding = biometric_service.encode_face_from_image(detenu.photo_face.path)
        
        if encoding is None:
            return JsonResponse({
                'error': 'Aucun visage détecté dans la photo'
            }, status=400)
        
        # Ajouter à la base biométrique
        with biometric_service._lock:
            biometric_service.known_face_encodings.append(encoding)
            biometric_service.known_face_ids.append(detenu.id)
            biometric_service.known_face_names.append(f"{detenu.nom} {detenu.prenom}")
        
        return JsonResponse({
            'success': True,
            'message': f'Visage de {detenu.nom} {detenu.prenom} encodé avec succès',
            'detenu_id': detenu.id,
            'nom': f"{detenu.nom} {detenu.prenom}"
        })
        
    except Detenu.DoesNotExist:
        return JsonResponse({
            'error': 'Détenu non trouvé'
        }, status=404)
    except Exception as e:
        logger.error(f'Erreur encodage visage: {e}')
        return JsonResponse({
            'error': f'Erreur lors de l\'encodage: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def detecter_visage_image(request):
    """Détecte et identifie les visages avec retour visuel des rectangles"""
    try:
        data = json.loads(request.body)
        image_data = data.get('image')
        camera_id = data.get('camera_id')
        
        if not image_data:
            return JsonResponse({
                'error': 'Aucune image fournie'
            }, status=400)
        
        # Décoder l'image base64
        image_data = image_data.split(',')[1]  # Enlever le préfixe data:image/jpeg;base64,
        image_bytes = base64.b64decode(image_data)
        
        # Charger l'image pour la détection
        image = Image.open(io.BytesIO(image_bytes))
        image_array = np.array(image)
        
        # Détecter les visages
        face_locations = face_recognition.face_locations(image_array)
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        
        detections = []
        face_rectangles = []  # Pour le retour visuel
        
        # Charger les données biométriques si pas déjà fait
        if len(biometric_service.known_face_encodings) == 0:
            biometric_service.load_biometric_data()
        
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Comparer avec les visages connus
            matches = face_recognition.compare_faces(
                biometric_service.known_face_encodings, 
                face_encoding, 
                tolerance=biometric_service.detection_threshold
            )
            
            name = "Inconnu"
            detenu_id = None
            confiance = 0.0
            
            # Calculer la confiance
            if len(biometric_service.known_face_encodings) > 0:
                face_distances = face_recognition.face_distance(
                    biometric_service.known_face_encodings, 
                    face_encoding
                )
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        detenu_id = biometric_service.known_face_ids[best_match_index]
                        name = biometric_service.known_face_names[best_match_index]
                        confiance = (1 - face_distances[best_match_index]) * 100
            
            # Préparer le rectangle pour le retour visuel
            face_rectangles.append({
                'top': top,
                'right': right,
                'bottom': bottom,
                'left': left,
                'name': name,
                'confidence': round(confiance, 1),
                'is_alert': name == "Inconnu"
            })
            
            # Enregistrer la détection
            camera = Camera.objects.filter(id=camera_id).first() if camera_id else None
            detection = DetectionFaciale.objects.create(
                camera=camera,
                detenu_id=detenu_id if detenu_id else None,
                image_detection=ContentFile(image_bytes, name=f'detection_{timezone.now().strftime("%Y%m%d_%H%M%S")}.jpg'),
                confiance=confiance,
                coordonnees_visage={'top': top, 'right': right, 'bottom': bottom, 'left': left},
                timestamp=timezone.now(),
                est_alerte=(name == "Inconnu"),
                traitee=False
            )
            
            detections.append({
                'detection_id': detection.id,
                'name': name,
                'detenu_id': detenu_id,
                'confidence': round(confiance, 1),
                'location': {
                    'top': top,
                    'right': right,
                    'bottom': bottom,
                    'left': left
                },
                'is_alert': detection.est_alerte
            })
        
        return JsonResponse({
            'success': True,
            'detections': detections,
            'total_faces': len(detections),
            'face_rectangles': face_rectangles  # Pour dessiner les rectangles
        })
        
    except Exception as e:
        logger.error(f'Erreur détection visage: {e}')
        return JsonResponse({
            'error': f'Erreur lors de la détection: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def tester_reconnaissance(request):
    """Teste le système de reconnaissance biométrique"""
    try:
        # Charger les données biométriques
        biometric_service.load_biometric_data()
        
        # Obtenir les statistiques
        stats = biometric_service.get_statistics()
        
        return JsonResponse({
            'success': True,
            'statistiques': {
                'total_profils': stats['total_detenus_with_photos'],
                'visages_charges': stats['total_detenus_with_photos'],
                'total_detections': stats['total_detections'],
                'identified_detections': stats['identified_detections'],
                'unknown_detections': stats['unknown_detections']
            },
            'systeme_pret': stats['total_detenus_with_photos'] > 0,
            'message': f'Système prêt avec {stats["total_detenus_with_photos"]} détenus chargés'
        })
        
    except Exception as e:
        logger.error(f'Erreur test reconnaissance: {e}')
        return JsonResponse({
            'error': f'Erreur lors du test: {str(e)}'
        }, status=500)
