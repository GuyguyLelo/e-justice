import cv2
import numpy as np
import face_recognition
import threading
import time
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image
import io
import logging
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Service pour la reconnaissance faciale"""
    
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_ids = []
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.process_this_frame = True
        self.detection_threshold = 0.6
        self._lock = threading.Lock()
    
    def load_known_faces(self, profiles_queryset):
        """Charge les profils faciaux connus depuis la base de données"""
        with self._lock:
            self.known_face_encodings = []
            self.known_face_ids = []
            
            for profile in profiles_queryset.select_related('detenu'):
                try:
                    if profile.encodage_facial and profile.actif:
                        encoding = np.array(profile.encodage_facial)
                        self.known_face_encodings.append(encoding)
                        self.known_face_ids.append(profile.detenu.id)
                except Exception as e:
                    logger.error(f"Erreur chargement profil {profile.id}: {e}")
    
    def encode_face_from_image(self, image_path: str) -> Optional[np.ndarray]:
        """Encode un visage depuis une image"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            return None
        except Exception as e:
            logger.error(f"Erreur encodage visage {image_path}: {e}")
            return None
    
    def detect_faces(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], List[np.ndarray]]:
        """Détecte les visages dans une image"""
        try:
            # Redimensionner l'image pour un traitement plus rapide
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            # Remettre à l'échelle les coordonnées
            scaled_locations = []
            for (top, right, bottom, left) in face_locations:
                scaled_locations.append((
                    left * 4, top * 4, right * 4, bottom * 4
                ))
            
            return scaled_locations, face_encodings
        except Exception as e:
            logger.error(f"Erreur détection visages: {e}")
            return [], []
    
    def recognize_faces(self, face_encodings: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Reconnaît les visages détectés"""
        recognized_faces = []
        
        if not self.known_face_encodings:
            return recognized_faces
        
        try:
            for face_encoding in face_encodings:
                # Comparer avec tous les visages connus
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, face_encoding
                )
                
                best_match_index = np.argmin(face_distances)
                confidence = 1 - face_distances[best_match_index]
                
                if confidence >= self.detection_threshold:
                    recognized_faces.append({
                        'detenu_id': self.known_face_ids[best_match_index],
                        'confidence': confidence * 100,
                        'known': True
                    })
                else:
                    recognized_faces.append({
                        'detenu_id': None,
                        'confidence': confidence * 100,
                        'known': False
                    })
        
        except Exception as e:
            logger.error(f"Erreur reconnaissance visages: {e}")
        
        return recognized_faces
    
    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Traite une frame complète"""
        results = {
            'faces': [],
            'timestamp': timezone.now(),
            'success': False
        }
        
        try:
            # Détecter les visages
            face_locations, face_encodings = self.detect_faces(frame)
            
            if not face_locations:
                return results
            
            # Reconnaître les visages
            recognized_faces = self.recognize_faces(face_encodings)
            
            # Combiner les résultats
            for i, (location, face_data) in enumerate(zip(face_locations, recognized_faces)):
                face_info = {
                    'location': location,
                    'detenu_id': face_data['detenu_id'],
                    'confidence': face_data['confidence'],
                    'known': face_data['known']
                }
                results['faces'].append(face_info)
            
            results['success'] = True
            
        except Exception as e:
            logger.error(f"Erreur traitement frame: {e}")
        
        return results


class VideoStreamService:
    """Service pour la gestion des flux vidéo"""
    
    def __init__(self):
        self.active_streams = {}
        self._lock = threading.Lock()
    
    def start_stream(self, camera_id: int, stream_url: str) -> bool:
        """Démarre un flux vidéo"""
        with self._lock:
            if camera_id in self.active_streams:
                return True
            
            try:
                cap = cv2.VideoCapture(stream_url)
                if cap.isOpened():
                    self.active_streams[camera_id] = {
                        'capture': cap,
                        'last_frame': None,
                        'last_update': timezone.now(),
                        'error_count': 0
                    }
                    return True
                else:
                    logger.error(f"Impossible d'ouvrir le flux: {stream_url}")
                    return False
            except Exception as e:
                logger.error(f"Erreur démarrage stream {camera_id}: {e}")
                return False
    
    def stop_stream(self, camera_id: int):
        """Arrête un flux vidéo"""
        with self._lock:
            if camera_id in self.active_streams:
                try:
                    self.active_streams[camera_id]['capture'].release()
                    del self.active_streams[camera_id]
                except Exception as e:
                    logger.error(f"Erreur arrêt stream {camera_id}: {e}")
    
    def get_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Récupère une frame depuis un flux"""
        with self._lock:
            if camera_id not in self.active_streams:
                return None
            
            stream_data = self.active_streams[camera_id]
            cap = stream_data['capture']
            
            try:
                ret, frame = cap.read()
                if ret:
                    stream_data['last_frame'] = frame
                    stream_data['last_update'] = timezone.now()
                    stream_data['error_count'] = 0
                    return frame
                else:
                    stream_data['error_count'] += 1
                    if stream_data['error_count'] > 10:
                        logger.warning(f"Stream {camera_id} semble déconnecté")
                    return None
            except Exception as e:
                logger.error(f"Erreur lecture frame {camera_id}: {e}")
                stream_data['error_count'] += 1
                return None
    
    def is_stream_active(self, camera_id: int) -> bool:
        """Vérifie si un flux est actif"""
        with self._lock:
            if camera_id not in self.active_streams:
                return False
            
            stream_data = self.active_streams[camera_id]
            time_since_update = timezone.now() - stream_data['last_update']
            return time_since_update.total_seconds() < 30


class DetectionService:
    """Service pour la gestion des détections"""
    
    def __init__(self):
        self.face_recognition = FaceRecognitionService()
        self.video_stream = VideoStreamService()
    
    def initialize_from_database(self):
        """Initialise les services depuis la base de données"""
        from .models import Camera, ProfilFacialDetenu
        
        # Charger les profils faciaux
        profiles = ProfilFacialDetenu.objects.filter(actif=True)
        self.face_recognition.load_known_faces(profiles)
        
        # Démarrer les flux vidéo actifs
        active_cameras = Camera.objects.filter(
            statut='ACTIVE',
            detection_active=True
        )
        
        for camera in active_cameras:
            stream_url = camera.url_complete or camera.url_flux
            if stream_url:
                self.video_stream.start_stream(camera.id, stream_url)
    
    def process_camera_detection(self, camera_id: int) -> List[Dict[str, Any]]:
        """Traite les détections pour une caméra spécifique"""
        from .models import Camera, DetectionFaciale, ZoneSurveillance
        
        results = []
        
        try:
            # Récupérer la frame
            frame = self.video_stream.get_frame(camera_id)
            if frame is None:
                return results
            
            # Traiter la frame
            detection_results = self.face_recognition.process_frame(frame)
            
            if not detection_results['success']:
                return results
            
            camera = Camera.objects.get(id=camera_id)
            
            # Traiter chaque visage détecté
            for face_data in detection_results['faces']:
                location = face_data['location']
                confidence = face_data['confidence']
                detenu_id = face_data['detenu_id']
                
                # Vérifier si le visage est dans une zone de surveillance
                zone = self._check_face_in_zones(camera, location)
                
                # Sauvegarder l'image de détection
                image_path = self._save_detection_image(frame, location, camera_id)
                
                # Créer l'enregistrement de détection
                detection_data = {
                    'camera_id': camera_id,
                    'detenu_id': detenu_id,
                    'zone_id': zone.id if zone else None,
                    'image_path': image_path,
                    'confidence': confidence,
                    'location': location,
                    'timestamp': detection_results['timestamp'],
                    'is_alert': self._should_generate_alert(detenu_id, zone, camera)
                }
                
                results.append(detection_data)
        
        except Exception as e:
            logger.error(f"Erreur détection caméra {camera_id}: {e}")
        
        return results
    
    def _check_face_in_zones(self, camera, face_location):
        """Vérifie si un visage est dans une zone de surveillance"""
        try:
            face_center_x = face_location[0] + face_location[2] // 2
            face_center_y = face_location[1] + face_location[3] // 2
            
            for zone in camera.zones.filter(detection_active=True):
                if self._point_in_polygon(
                    (face_center_x, face_center_y), 
                    zone.coordonnees
                ):
                    return zone
        except Exception as e:
            logger.error(f"Erreur vérification zones: {e}")
        
        return None
    
    def _point_in_polygon(self, point, polygon):
        """Vérifie si un point est dans un polygone"""
        x, y = point
        n = len(polygon) // 2
        inside = False
        
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i*2], polygon[i*2+1]
            xj, yj = polygon[j*2], polygon[j*2+1]
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            j = i
        
        return inside
    
    def _save_detection_image(self, frame, location, camera_id):
        """Sauvegarde l'image de détection"""
        try:
            # Extraire la région du visage
            x, y, w, h = location
            face_image = frame[y:h, x:w]
            
            # Convertir en PIL Image
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # Sauvegarder en mémoire
            img_buffer = io.BytesIO()
            filename = f"detection_{camera_id}_{timezone.now().timestamp()}.jpg"
            pil_image.save(img_buffer, format='JPEG', quality=85)
            
            return ContentFile(img_buffer.getvalue(), filename)
        
        except Exception as e:
            logger.error(f"Erreur sauvegarde image: {e}")
            return None
    
    def _should_generate_alert(self, detenu_id, zone, camera):
        """Détermine s'il faut générer une alerte"""
        # Alerte si visage non identifié
        if detenu_id is None:
            return True
        
        # Alerte si détenu dans zone interdite
        if zone and zone.seuil_alerte > 0:
            return True
        
        # Autres règles d'alerte...
        return False


class AlertService:
    """Service pour la gestion des alertes"""
    
    @staticmethod
    def create_alert_from_detection(detection_data):
        """Crée une alerte depuis une détection"""
        from .models import AlerteSurveillance, DetectionFaciale, Detenu
        
        try:
            # Créer la détection
            detection = DetectionFaciale.objects.create(
                camera_id=detection_data['camera_id'],
                detenu_id=detection_data['detenu_id'],
                zone_id=detection_data.get('zone_id'),
                image_detection=detection_data['image_path'],
                confiance=detection_data['confidence'],
                coordonnees_visage=detection_data['location'],
                timestamp=detection_data['timestamp'],
                est_alerte=detection_data['is_alert']
            )
            
            if not detection_data['is_alert']:
                return detection
            
            # Déterminer le type et niveau d'alerte
            alert_type, alert_level = AlertService._determine_alert_type(detection)
            
            # Créer l'alerte
            alerte = AlerteSurveillance.objects.create(
                titre=AlertService._generate_alert_title(detection, alert_type),
                type_alerte=alert_type,
                niveau=alert_level,
                description=AlertService._generate_alert_description(detection, alert_type),
                camera=detection.camera,
                detection=detection,
                detenu=detection.detenu
            )
            
            # Enregistrer dans l'historique
            AlertService._log_alert_event(alerte, detection)
            
            return detection
        
        except Exception as e:
            logger.error(f"Erreur création alerte: {e}")
            return None
    
    @staticmethod
    def _determine_alert_type(detection):
        """Détermine le type et niveau d'alerte"""
        if detection.detenu is None:
            return 'DETECTION_INCONNUE', 'ATTENTION'
        elif detection.zone and detection.zone.type_zone in ['CELLULE', 'INFIRMERIE']:
            return 'DETENU_INTERDIT', 'WARNING'
        else:
            return 'DETECTION_MULTIPLE', 'INFO'
    
    @staticmethod
    def _generate_alert_title(detection, alert_type):
        """Génère le titre de l'alerte"""
        titles = {
            'DETECTION_INCONNUE': 'Visage inconnu détecté',
            'DETENU_INTERDIT': 'Détenu dans zone interdite',
            'DETECTION_MULTIPLE': 'Détection multiple'
        }
        return titles.get(alert_type, 'Alerte surveillance')
    
    @staticmethod
    def _generate_alert_description(detection, alert_type):
        """Génère la description de l'alerte"""
        if detection.detenu:
            detenu_info = f"{detection.detenu.nom} {detection.detenu.prenom}"
        else:
            detenu_info = "Personne non identifiée"
        
        descriptions = {
            'DETECTION_INCONNUE': f"Une personne non identifiée a été détectée par la caméra {detection.camera.nom}",
            'DETENU_INTERDIT': f"Le détenu {detenu_info} a été détecté dans une zone interdite ({detection.zone.nom})",
            'DETECTION_MULTIPLE': f"Détection du détenu {detenu_info} par la caméra {detection.camera.nom}"
        }
        
        return descriptions.get(alert_type, f"Alerte de surveillance: {detenu_info}")
    
    @staticmethod
    def _log_alert_event(alerte, detection):
        """Enregistre l'événement d'alerte dans l'historique"""
        from .models import HistoriqueSurveillance
        
        HistoriqueSurveillance.objects.create(
            type_evenement='ALERTE',
            description=f"Alerte générée: {alerte.titre}",
            camera=detection.camera,
            detection=detection,
            alerte=alerte,
            donnees_supplementaires={
                'alerte_id': alerte.id,
                'detection_id': detection.id,
                'confiance': float(detection.confiance)
            }
        )


# Instance globale des services
detection_service = DetectionService()
alert_service = AlertService()
