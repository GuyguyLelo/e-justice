from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from apps.detenus.models import Detenu
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["PUT", "POST"])
def biometric_update_simple(request, detenu_id):
    """Vue simplifiée pour la mise à jour des données biométriques sans authentification"""
    try:
        detenu = get_object_or_404(Detenu, id=detenu_id)
        logger.info(f"Mise à jour biométrique pour: {detenu.nom_complet}")
        
        # Gérer les fichiers uploadés
        logger.info(f"Fichiers reçus: {list(request.FILES.keys())}")
        logger.info(f"POST data: {list(request.POST.keys())}")
        
        if 'photo_face' in request.FILES:
            detenu.photo_face = request.FILES['photo_face']
            logger.info(f"Photo de face mise à jour: {request.FILES['photo_face']}")
            logger.info(f"Photo face size: {request.FILES['photo_face'].size}")
        else:
            logger.info("Pas de photo_face dans request.FILES")
        
        if 'photo_profil' in request.FILES:
            detenu.photo_profil = request.FILES['photo_profil']
            logger.info(f"Photo de profil mise à jour: {request.FILES['photo_profil']}")
            logger.info(f"Photo profil size: {request.FILES['photo_profil'].size}")
        else:
            logger.info("Pas de photo_profil dans request.FILES")
        
        # Mettre à jour les autres champs
        if 'empreintes_digitales' in request.POST:
            detenu.empreintes_digitales = request.POST['empreintes_digitales']
        
        if 'adn' in request.POST:
            detenu.adn = request.POST['adn']
        
        detenu.save()
        logger.info(f"Détenu {detenu.id} sauvegardé avec succès")
        logger.info(f"Photo face après sauvegarde: {detenu.photo_face}")
        logger.info(f"Photo profil après sauvegarde: {detenu.photo_profil}")
        
        # Encoder automatiquement le visage si photo ajoutée
        if 'photo_face' in request.FILES:
            try:
                from apps.surveillance.biometric_service import biometric_service
                encoding = biometric_service.encode_face_from_image(detenu.photo_face.path)
                
                if encoding is not None:
                    with biometric_service._lock:
                        # Vérifier si le détenu est déjà dans la base
                        if detenu.id in biometric_service.known_face_ids:
                            index = biometric_service.known_face_ids.index(detenu.id)
                            del biometric_service.known_face_encodings[index]
                            del biometric_service.known_face_ids[index]
                            del biometric_service.known_face_names[index]
                        
                        # Ajouter le nouvel encodage
                        biometric_service.known_face_encodings.append(encoding)
                        biometric_service.known_face_ids.append(detenu.id)
                        biometric_service.known_face_names.append(f"{detenu.nom} {detenu.prenom}")
                    
                    logger.info(f"Visage encodé automatiquement pour: {detenu.nom_complet}")
            except Exception as e:
                logger.error(f"Erreur encodage visage: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Données biométriques de {detenu.nom_complet} mises à jour avec succès',
            'detenu_id': detenu.id,
            'nom_complet': detenu.nom_complet
        })
        
    except Exception as e:
        logger.error(f'Erreur mise à jour biométrique: {e}')
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la mise à jour: {str(e)}'
        }, status=500)
