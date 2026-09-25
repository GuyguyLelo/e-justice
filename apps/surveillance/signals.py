from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Camera, DetectionFaciale, AlerteSurveillance, ProfilFacialDetenu
from .services import detection_service
from .biometric_service import biometric_service
from apps.detenus.models import Detenu
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Detenu)
def encode_new_detenu_face(sender, instance, created, **kwargs):
    """Encode automatiquement le visage d'un nouveau détenu"""
    if created and instance.photo_face:
        try:
            # Encoder le visage
            encoding = biometric_service.encode_face_from_image(instance.photo_face.path)
            
            if encoding is not None:
                # Ajouter à la base biométrique
                with biometric_service._lock:
                    biometric_service.known_face_encodings.append(encoding)
                    biometric_service.known_face_ids.append(instance.id)
                    biometric_service.known_face_names.append(f"{instance.nom} {instance.prenom}")
                
                logger.info(f"Visage encodé automatiquement: {instance.nom} {instance.prenom}")
            else:
                logger.warning(f"Aucun visage détecté pour: {instance.nom} {instance.prenom}")
                
        except Exception as e:
            logger.error(f"Erreur encodage automatique {instance.matricule}: {e}")


@receiver(post_save, sender=Detenu)
def update_detenu_face_encoding(sender, instance, **kwargs):
    """Met à jour l'encodage si la photo change"""
    if not kwargs.get('created') and instance.photo_face:
        try:
            # Vérifier si le détenu est déjà dans la base
            if instance.id in biometric_service.known_face_ids:
                # Retirer l'ancien encodage
                index = biometric_service.known_face_ids.index(instance.id)
                del biometric_service.known_face_encodings[index]
                del biometric_service.known_face_ids[index]
                del biometric_service.known_face_names[index]
            
            # Ajouter le nouvel encodage
            encoding = biometric_service.encode_face_from_image(instance.photo_face.path)
            
            if encoding is not None:
                with biometric_service._lock:
                    biometric_service.known_face_encodings.append(encoding)
                    biometric_service.known_face_ids.append(instance.id)
                    biometric_service.known_face_names.append(f"{instance.nom} {instance.prenom}")
                
                logger.info(f"Visage mis à jour: {instance.nom} {instance.prenom}")
                
        except Exception as e:
            logger.error(f"Erreur mise à jour encodage {instance.matricule}: {e}")


@receiver(post_save, sender=Camera)
def camera_saved(sender, instance, created, **kwargs):
    """Signal déclenché lors de la sauvegarde d'une caméra"""
    from .models import HistoriqueSurveillance
    
    if created:
        HistoriqueSurveillance.objects.create(
            type_evenement='CAMERA_ON',
            description=f"Nouvelle caméra ajoutée: {instance.nom}",
            camera=instance,
            donnees_supplementaires={
                'camera_id': instance.id,
                'centre_id': instance.centre.id,
                'type_camera': instance.type_camera
            }
        )
    else:
        HistoriqueSurveillance.objects.create(
            type_evenement='CONFIG_CHANGE',
            description=f"Configuration modifiée pour la caméra: {instance.nom}",
            camera=instance,
            donnees_supplementaires={
                'camera_id': instance.id,
                'statut': instance.statut,
                'detection_active': instance.detection_active
            }
        )


@receiver(post_save, sender=ProfilFacialDetenu)
def profil_facial_saved(sender, instance, created, **kwargs):
    """Signal déclenché lors de la sauvegarde d'un profil facial"""
    from .models import HistoriqueSurveillance
    
    if created:
        HistoriqueSurveillance.objects.create(
            type_evenement='DETECTION',
            description=f"Nouveau profil facial créé pour: {instance.detenu.nom_complet}",
            utilisateur=instance.created_by,
            donnees_supplementaires={
                'detenu_id': instance.detenu.id,
                'profil_id': instance.id,
                'qualite_image': instance.qualite_image
            }
        )
        
        # Recharger les profils faciaux dans le service
        try:
            detection_service.initialize_from_database()
        except Exception as e:
            pass  # Ignorer les erreurs lors du rechargement


@receiver(post_save, sender=DetectionFaciale)
def detection_saved(sender, instance, created, **kwargs):
    """Signal déclenché lors de la sauvegarde d'une détection"""
    from .models import HistoriqueSurveillance
    
    if created:
        detenu_info = "inconnu" if not instance.detenu else instance.detenu.nom_complet
        camera_info = "caméra inconnue" if not instance.camera else instance.camera.nom
        
        HistoriqueSurveillance.objects.create(
            type_evenement='DETECTION',
            description=f"Détection faciale: {detenu_info} - {camera_info}",
            camera=instance.camera,
            detection=instance,
            donnees_supplementaires={
                'detection_id': instance.id,
                'confiance': float(instance.confiance),
                'est_alerte': instance.est_alerte,
                'est_identifie': instance.detenu is not None,
                'detenu_id': instance.detenu.id if instance.detenu else None,
                'detenu_nom': instance.detenu.nom_complet if instance.detenu else None,
                'camera_id': instance.camera.id if instance.camera else None,
                'camera_nom': instance.camera.nom if instance.camera else None
            }
        )


@receiver(post_save, sender=AlerteSurveillance)
def alerte_saved(sender, instance, created, **kwargs):
    """Signal déclenché lors de la sauvegarde d'une alerte"""
    from .models import HistoriqueSurveillance
    
    if created:
        HistoriqueSurveillance.objects.create(
            type_evenement='ALERTE',
            description=f"Alerte générée: {instance.titre}",
            camera=instance.camera,
            alerte=instance,
            detenu=instance.detenu,
            donnees_supplementaires={
                'alerte_id': instance.id,
                'type_alerte': instance.type_alerte,
                'niveau': instance.niveau,
                'statut': instance.statut
            }
        )
    elif instance.statut in ['RESOLUE', 'FAUSSE_ALERTE']:
        HistoriqueSurveillance.objects.create(
            type_evenement='ALERTE',
            description=f"Alerte résolue: {instance.titre}",
            camera=instance.camera,
            alerte=instance,
            detenu=instance.detenu,
            utilisateur=instance.traitee_par,
            donnees_supplementaires={
                'alerte_id': instance.id,
                'ancien_statut': 'OUVERTE',
                'nouveau_statut': instance.statut,
                'resolution': instance.resolution
            }
        )


@receiver(post_delete, sender=Camera)
def camera_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'une caméra"""
    from .models import HistoriqueSurveillance
    
    HistoriqueSurveillance.objects.create(
        type_evenement='CAMERA_OFF',
        description=f"Caméra supprimée: {instance.nom}",
        donnees_supplementaires={
            'camera_id': instance.id,
            'centre_id': instance.centre.id,
            'nom_camera': instance.nom
        }
    )
    
    # Arrêter le flux si actif
    try:
        detection_service.video_stream.stop_stream(instance.id)
    except Exception as e:
        pass  # Ignorer les erreurs


@receiver(post_delete, sender=ProfilFacialDetenu)
def profil_facial_deleted(sender, instance, **kwargs):
    """Signal déclenché lors de la suppression d'un profil facial"""
    from .models import HistoriqueSurveillance
    
    HistoriqueSurveillance.objects.create(
        type_evenement='DETECTION',
        description=f"Profil facial supprimé pour: {instance.detenu.nom_complet}",
        utilisateur=None,  # Peut être fait par le système
        donnees_supplementaires={
            'detenu_id': instance.detenu.id,
            'profil_id': instance.id
        }
    )
    
    # Recharger les profils faciaux dans le service
    try:
        detection_service.initialize_from_database()
    except Exception as e:
        pass  # Ignorer les erreurs lors du rechargement
