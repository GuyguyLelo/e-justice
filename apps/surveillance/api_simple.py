from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .biometric_service import biometric_service
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def initialiser_systeme_simple(request):
    """Initialise le système sans authentification pour les tests"""
    try:
        # Charger les données biométriques seulement si la base est vide
        if len(biometric_service.known_face_ids) == 0:
            biometric_service.load_biometric_data()
        
        # Compter les profils créés
        total_detenus = biometric_service.get_statistics()['total_detenus_with_photos']
        profils_encodes = len(biometric_service.known_face_ids)
        
        return JsonResponse({
            'success': True,
            'message': f'Système initialisé avec {profils_encodes} profils encodés',
            'profils_crees': profils_encodes,
            'total_detenus': total_detenus,
            'detenus': biometric_service.known_face_names
        })
        
    except Exception as e:
        logger.error(f'Erreur initialisation: {e}')
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de l\'initialisation: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def detecter_visage_simple(request):
    """Détecte les visages sans authentification pour les tests"""
    try:
        logger.info("=== DÉBUT DÉTECTION VISAGE SIMPLE ===")
        
        data = json.loads(request.body)
        image_data = data.get('image')
        camera_id = data.get('camera_id', 1)
        
        logger.info(f"Image data reçue: {type(image_data)}")
        logger.info(f"Image data length: {len(image_data) if image_data else 0}")
        logger.info(f"Camera ID: {camera_id}")
        
        if not image_data:
            logger.error("Aucune image fournie")
            return JsonResponse({
                'success': False,
                'error': 'Aucune image fournie'
            }, status=400)
        
        # Décoder l'image base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        logger.info(f"Image data après split: {len(image_data)} caractères")
        
        import base64
        import io
        from PIL import Image
        import numpy as np
        import face_recognition
        
        image_bytes = base64.b64decode(image_data)
        logger.info(f"Image bytes décodés: {len(image_bytes)} octets")
        
        image = Image.open(io.BytesIO(image_bytes))
        logger.info(f"Image PIL ouverte: {image.size}, mode: {image.mode}")
        
        image_array = np.array(image)
        logger.info(f"Image array créé: {image_array.shape}")
        
        # Détecter les visages
        face_locations = face_recognition.face_locations(image_array)
        logger.info(f"Visages détectés: {len(face_locations)}")
        
        face_encodings = face_recognition.face_encodings(image_array, face_locations)
        logger.info(f"Encodages créés: {len(face_encodings)}")
        
        detections = []
        face_rectangles = []
        
        # Charger les données biométriques si pas déjà fait
        if len(biometric_service.known_face_encodings) == 0:
            biometric_service.load_biometric_data()
            logger.info("Base biométrique chargée")
        
        logger.info(f"Visages connus: {len(biometric_service.known_face_encodings)}")
        
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
            
            # Créer une image cropped pour ce visage spécifique
            from PIL import Image
            import io
            
            # Convertir l'image en PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Cropper le visage détecté avec une marge
            margin = 20
            face_top = max(0, top - margin)
            face_right = min(pil_image.width, right + margin)
            face_bottom = min(pil_image.height, bottom + margin)
            face_left = max(0, left - margin)
            
            face_image = pil_image.crop((face_left, face_top, face_right, face_bottom))
            
            # Convertir l'image cropped en bytes
            face_buffer = io.BytesIO()
            face_image.save(face_buffer, format='JPEG', quality=90)
            face_bytes = face_buffer.getvalue()
            
            # Enregistrer la détection en base de données avec l'image cropped
            from django.utils import timezone
            from .models import DetectionFaciale, Camera
            
            camera = Camera.objects.filter(id=camera_id).first() if camera_id else None
            
            # Créer l'enregistrement de détection avec l'image individuelle du visage
            detection = DetectionFaciale(
                camera=camera,
                detenu_id=detenu_id if detenu_id else None,
                confiance=confiance,
                coordonnees_visage={'top': top, 'right': right, 'bottom': bottom, 'left': left},
                timestamp=timezone.now(),
                est_alerte=(name == "Inconnu"),
                traitee=False
            )
            detection.enregistrer_image(
                face_bytes,
                f'face_detection_{timezone.now().strftime("%Y%m%d_%H%M%S")}_{len(detections)+1}.jpg',
            )
            
            logger.info(f"Détection visage #{len(detections)+1} enregistrée: ID {detection.id}, Personne: {name}, Caméra: {camera}, Confiance: {confiance:.1f}%")
            
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
                'is_alert': name == "Inconnu",
                'timestamp': detection.timestamp.isoformat(),
                'camera': {
                    'id': camera.id if camera else None,
                    'nom': camera.nom if camera else 'Inconnue'
                }
            })
        
        logger.info(f"Détection terminée: {len(detections)} détections")
        
        return JsonResponse({
            'success': True,
            'detections': detections,
            'total_faces': len(detections),
            'face_rectangles': face_rectangles
        })
        
    except Exception as e:
        logger.error(f'Erreur détection visage: {e}', exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la détection: {str(e)}'
        }, status=500)
