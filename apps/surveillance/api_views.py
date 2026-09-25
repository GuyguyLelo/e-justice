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
def encoder_visage_detenu(request, detenu_id):
    """Encode le visage d'un détenu depuis sa photo existante"""
    try:
        detenu = Detenu.objects.get(id=detenu_id)
        
        # Vérifier si le détenu a une photo
        if not detenu.photo_face:
            return JsonResponse({
                'error': 'Le détenu n\'a pas de photo de face'
            }, status=400)
        
        # Encoder le visage depuis la photo
        face_recognition_service = FaceRecognitionService()
        encoding = face_recognition_service.encode_face_from_image(detenu.photo_face.path)
        
        if encoding is None:
            return JsonResponse({
                'error': 'Aucun visage détecté dans la photo'
            }, status=400)
        
        # Créer ou mettre à jour le profil facial
        profil, created = ProfilFacialDetenu.objects.update_or_create(
            detenu=detenu,
            defaults={
                'encodage_facial': encoding.tolist(),
                'qualite_image': 'BONNE',
                'actif': True,
                'date_enregistrement': timezone.now(),
                'derniere_mise_a_jour': timezone.now(),
                'created_by': request.user
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Visage encodé avec succès pour {detenu.nom} {detenu.prenom}',
            'profil_id': profil.id,
            'created': created
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
    """Détecte et identifie les visages dans une image uploadée"""
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
        
        # Utiliser le service biométrique pour la détection
        detections = biometric_service.detect_and_identify_faces(image_bytes, camera_id)
        
        return JsonResponse({
            'success': True,
            'detections': detections,
            'total_faces': len(detections)
        })
        
    except Exception as e:
        logger.error(f'Erreur détection visage: {e}')
        return JsonResponse({
            'error': f'Erreur lors de la détection: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def initialiser_systeme(request):
    """Initialise le système de surveillance en encodant tous les détenus avec photos"""
    try:
        detenus_avec_photos = Detenu.objects.exclude(photo_face='')
        total_detenus = detenus_avec_photos.count()
        profils_crees = 0
        erreurs = []
        
        face_recognition_service = FaceRecognitionService()
        
        for detenu in detenus_avec_photos:
            try:
                # Vérifier si un profil existe déjà
                if ProfilFacialDetenu.objects.filter(detenu=detenu).exists():
                    continue
                
                # Encoder le visage
                encoding = face_recognition_service.encode_face_from_image(detenu.photo_face.path)
                
                if encoding is not None:
                    ProfilFacialDetenu.objects.create(
                        detenu=detenu,
                        encodage_facial=encoding.tolist(),
                        qualite_image='BONNE',
                        actif=True,
                        date_enregistrement=timezone.now(),
                        created_by=request.user
                    )
                    profils_crees += 1
                else:
                    erreurs.append(f"Aucun visage détecté pour {detenu.nom} {detenu.prenom}")
                    
            except Exception as e:
                erreurs.append(f"Erreur pour {detenu.nom} {detenu.prenom}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Système initialisé avec succès',
            'total_detenus': total_detenus,
            'profils_crees': profils_crees,
            'erreurs': erreurs
        })
        
    except Exception as e:
        logger.error(f'Erreur initialisation système: {e}')
        return JsonResponse({
            'error': f'Erreur lors de l\'initialisation: {str(e)}'
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
