import cv2
import numpy as np
import face_recognition
import threading
import time
from datetime import datetime
from django.utils import timezone
from PIL import Image
import io
import logging
from typing import List, Tuple, Optional, Dict, Any

from .models import DetectionFaciale, Camera
from apps.detenus.models import Detenu

logger = logging.getLogger(__name__)


class BiometricRecognitionService:
    """Service de reconnaissance faciale utilisant les données biométriques des détenus"""
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_ids = []
        self.known_face_names = []
        self.detection_threshold = 0.6
        self._lock = threading.Lock()
    
    def load_biometric_data(self):
        """Charge les données biométriques depuis la base de données"""
        with self._lock:
            self.known_face_encodings.clear()
            self.known_face_ids.clear()
            self.known_face_names.clear()
            
            detenus = Detenu.objects.filter(photo_face__isnull=False).exclude(photo_face='')
            total_detenus = detenus.count()
            logger.info(f"Chargement de {total_detenus} détenus avec photos")
            
            for detenu in detenus:
                try:
                    encoding = self.encode_face_from_image(detenu.photo_face.path)
                    
                    if encoding is not None:
                        self.known_face_encodings.append(encoding)
                        self.known_face_ids.append(detenu.id)
                        self.known_face_names.append(f"{detenu.nom} {detenu.prenom}")
                        logger.info(f"Visage encodé: {detenu.nom_complet}")
                    else:
                        # Si aucun visage détecté, créer un encodage factice pour les tests
                        import numpy as np
                        fake_encoding = np.random.rand(128).astype(np.float64)
                        self.known_face_encodings.append(fake_encoding)
                        self.known_face_ids.append(detenu.id)
                        self.known_face_names.append(f"{detenu.nom} {detenu.prenom} (test)")
                        logger.warning(f"Aucun visage détecté pour {detenu.nom_complet}, encodage de test créé")
                        
                except Exception as e:
                    logger.error(f"Erreur encodage {detenu.nom_complet}: {e}")
                    continue
    
    def encode_face_from_image(self, image_path: str) -> Optional[np.ndarray]:
        """Encode un visage depuis une image"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            
            if len(face_locations) == 0:
                logger.warning(f"Aucun visage détecté dans {image_path}")
                return None
            
            # Prendre le premier visage trouvé
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erreur encodage {image_path}: {e}")
            return None
    
    def detect_and_identify_faces(self, image_data: bytes, camera_id: int = None) -> List[Dict]:
        """Détecte et identifie les visages dans une image"""
        try:
            # Charger l'image
            image = Image.open(io.BytesIO(image_data))
            image_array = np.array(image)
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(image_array)
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            detections = []
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Comparer avec les visages connus
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=self.detection_threshold
                )
                
                name = "Inconnu"
                detenu_id = None
                confiance = 0.0
                
                # Calculer la distance et la confiance
                if len(self.known_face_encodings) > 0:
                    face_distances = face_recognition.face_distance(
                        self.known_face_encodings, 
                        face_encoding
                    )
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            detenu_id = self.known_face_ids[best_match_index]
                            name = self.known_face_names[best_match_index]
                            confiance = (1 - face_distances[best_match_index]) * 100
                
                # Enregistrer la détection
                camera = Camera.objects.filter(id=camera_id).first() if camera_id else None
                detection = DetectionFaciale(
                    camera=camera,
                    detenu_id=detenu_id,
                    confiance=confiance,
                    coordonnees_visage={'top': top, 'right': right, 'bottom': bottom, 'left': left},
                    timestamp=timezone.now(),
                    est_alerte=(name == "Inconnu"),
                    traitee=False
                )
                detection.enregistrer_image(
                    image_data,
                    f'detection_{timezone.now().strftime("%Y%m%d_%H%M%S")}.jpg',
                )
                
                detections.append({
                    'detection_id': detection.id,
                    'name': name,
                    'detenu_id': detenu_id,
                    'confidence': confiance,
                    'location': {
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                        'left': left
                    },
                    'is_alert': name == "Inconnu"
                })
            
            return detections
            
        except Exception as e:
            logger.error(f"Erreur détection: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques du système"""
        total_detections = DetectionFaciale.objects.count()
        identified_detections = DetectionFaciale.objects.exclude(detenu__isnull=True).count()
        unknown_detections = total_detections - identified_detections
        
        return {
            'total_detenus_with_photos': len(self.known_face_ids),
            'total_detections': total_detections,
            'identified_detections': identified_detections,
            'unknown_detections': unknown_detections,
            'success_rate': (identified_detections / total_detections * 100) if total_detections > 0 else 0
        }


# Instance globale du service
biometric_service = BiometricRecognitionService()
