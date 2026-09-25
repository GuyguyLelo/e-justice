from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from datetime import datetime, timedelta
import json


class IsAdminCentre(permissions.BasePermission):
    """
    Permission personnalisée pour n'autoriser que les admins de centre
    """
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            hasattr(request.user, 'adminprison')
        )

from .models import (
    Camera, ZoneSurveillance, ProfilFacialDetenu, 
    DetectionFaciale, AlerteSurveillance, HistoriqueSurveillance
)
from .serializers import (
    CameraSerializer, ZoneSurveillanceSerializer, ProfilFacialDetenuSerializer,
    DetectionFacialeSerializer, DetectionFacialeCreateSerializer,
    AlerteSurveillanceSerializer, AlerteSurveillanceCreateSerializer,
    AlerteSurveillanceUpdateSerializer, SurveillanceDashboardSerializer
)

# Import conditionnel des services (dépendances externes)
try:
    from .services import detection_service, alert_service
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False


class CameraViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des caméras"""
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAdminCentre]
    
    def get_queryset(self):
        queryset = Camera.objects.select_related('centre')
        
        # Filtrer par centre de l'admin connecté
        if hasattr(self.request.user, 'adminprison'):
            queryset = queryset.filter(centre=self.request.user.adminprison.centre)
        
        # Filtrage par centre (paramètre URL)
        centre_id = self.request.query_params.get('centre')
        if centre_id:
            queryset = queryset.filter(centre_id=centre_id)
        
        # Filtrage par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtrage par type
        type_camera = self.request.query_params.get('type')
        if type_camera:
            queryset = queryset.filter(type_camera=type_camera)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def demarrer_detection(self, request, pk=None):
        """Démarre la détection pour une caméra"""
        if not SERVICES_AVAILABLE:
            return Response(
                {'error': 'Services de reconnaissance faciale non disponibles. Installez les dépendances requises.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        camera = self.get_object()
        
        if camera.statut != 'ACTIVE':
            return Response(
                {'error': 'La caméra doit être active pour démarrer la détection'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stream_url = camera.url_complete or camera.url_flux
            if not stream_url:
                return Response(
                    {'error': 'Aucune URL de flux configurée'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            success = detection_service.video_stream.start_stream(camera.id, stream_url)
            
            if success:
                # Enregistrer dans l'historique
                HistoriqueSurveillance.objects.create(
                    type_evenement='CAMERA_ON',
                    description=f"Démarrage de la détection pour la caméra {camera.nom}",
                    camera=camera,
                    utilisateur=request.user
                )
                
                return Response({'message': 'Détection démarrée avec succès'})
            else:
                return Response(
                    {'error': 'Impossible de démarrer le flux vidéo'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def arreter_detection(self, request, pk=None):
        """Arrête la détection pour une caméra"""
        camera = self.get_object()
        
        try:
            detection_service.video_stream.stop_stream(camera.id)
            
            # Enregistrer dans l'historique
            HistoriqueSurveillance.objects.create(
                type_evenement='CAMERA_OFF',
                description=f"Arrêt de la détection pour la caméra {camera.nom}",
                camera=camera,
                utilisateur=request.user
            )
            
            return Response({'message': 'Détection arrêtée avec succès'})
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def statut_stream(self, request, pk=None):
        """Vérifie le statut du flux d'une caméra"""
        camera = self.get_object()
        
        is_active = detection_service.video_stream.is_stream_active(camera.id)
        
        return Response({
            'camera_id': camera.id,
            'nom': camera.nom,
            'stream_actif': is_active,
            'statut': camera.statut
        })


class ZoneSurveillanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des zones de surveillance"""
    queryset = ZoneSurveillance.objects.all()
    serializer_class = ZoneSurveillanceSerializer
    permission_classes = [IsAdminCentre]
    
    def get_queryset(self):
        queryset = ZoneSurveillance.objects.select_related('camera', 'camera__centre')
        
        # Filtrage par caméra
        camera_id = self.request.query_params.get('camera')
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        
        # Filtrage par centre
        centre_id = self.request.query_params.get('centre')
        if centre_id:
            queryset = queryset.filter(camera__centre_id=centre_id)
        
        return queryset


class ProfilFacialDetenuViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des profils faciaux"""
    queryset = ProfilFacialDetenu.objects.all()
    serializer_class = ProfilFacialDetenuSerializer
    permission_classes = [IsAdminCentre]
    
    def get_queryset(self):
        queryset = ProfilFacialDetenu.objects.select_related('detenu', 'created_by')
        
        # Filtrage par détenu
        detenu_id = self.request.query_params.get('detenu')
        if detenu_id:
            queryset = queryset.filter(detenu_id=detenu_id)
        
        # Filtrage par statut
        actif = self.request.query_params.get('actif')
        if actif is not None:
            queryset = queryset.filter(actif=actif.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        """Crée un profil facial et génère l'encodage"""
        profil = serializer.save(created_by=self.request.user)
        
        # Générer l'encodage facial depuis l'image
        try:
            encoding = detection_service.face_recognition.encode_face_from_image(
                profil.image_reference.path
            )
            
            if encoding is not None:
                profil.encodage_facial = encoding.tolist()
                profil.save()
                
                # Recharger les profils dans le service de reconnaissance
                detection_service.initialize_from_database()
            else:
                # Supprimer le profil si aucun visage n'est détecté
                profil.delete()
                return Response(
                    {'error': 'Aucun visage détecté dans l\'image'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            profil.delete()
            return Response(
                {'error': f'Erreur lors de l\'encodage facial: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            ProfilFacialDetenuSerializer(profil).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def recharger_encodage(self, request, pk=None):
        """Recharge l'encodage facial d'un profil"""
        profil = self.get_object()
        
        try:
            encoding = detection_service.face_recognition.encode_face_from_image(
                profil.image_reference.path
            )
            
            if encoding is not None:
                profil.encodage_facial = encoding.tolist()
                profil.derniere_mise_a_jour = timezone.now()
                profil.save()
                
                # Recharger les profils dans le service
                detection_service.initialize_from_database()
                
                return Response({'message': 'Encodage rechargé avec succès'})
            else:
                return Response(
                    {'error': 'Aucun visage détecté dans l\'image'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DetectionFacialeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des détections faciales"""
    queryset = DetectionFaciale.objects.all()
    permission_classes = [IsAdminCentre]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DetectionFacialeCreateSerializer
        return DetectionFacialeSerializer
    
    def get_queryset(self):
        queryset = DetectionFaciale.objects.select_related(
            'camera', 'camera__centre', 'detenu', 'zone', 'traitee_par'
        )
        
        # Filtrage par caméra
        camera_id = self.request.query_params.get('camera')
        if camera_id:
            queryset = queryset.filter(camera_id=camera_id)
        
        # Filtrage par détenu
        detenu_id = self.request.query_params.get('detenu')
        if detenu_id:
            queryset = queryset.filter(detenu_id=detenu_id)
        
        # Filtrage par statut de traitement
        traitee = self.request.query_params.get('traitee')
        if traitee is not None:
            queryset = queryset.filter(traitee=traitee.lower() == 'true')
        
        # Filtrage par alerte
        est_alerte = self.request.query_params.get('alerte')
        if est_alerte is not None:
            queryset = queryset.filter(est_alerte=est_alerte.lower() == 'true')
        
        # Filtrage par date
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        if date_debut:
            queryset = queryset.filter(timestamp__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(timestamp__lte=date_fin)
        
        return queryset.order_by('-timestamp')
    
    def create(self, request, *args, **kwargs):
        """Crée une détection faciale et génère une alerte si nécessaire"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        detection_data = serializer.validated_data
        detection_data['is_alert'] = detection_service._should_generate_alert(
            detection_data.get('detenu'),
            detection_data.get('zone'),
            detection_data['camera']
        )
        
        # Créer la détection et l'alerte
        detection = alert_service.create_alert_from_detection(detection_data)
        
        if detection:
            return Response(
                DetectionFacialeSerializer(detection).data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': 'Erreur lors de la création de la détection'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def traiter(self, request, pk=None):
        """Marque une détection comme traitée"""
        detection = self.get_object()
        
        detection.traitee = True
        detection.traitee_par = request.user
        detection.date_traitement = timezone.now()
        detection.notes = request.data.get('notes', '')
        detection.save()
        
        return Response({'message': 'Détection traitée avec succès'})
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne les statistiques des détections"""
        now = timezone.now()
        
        # Statistiques générales
        total_detections = DetectionFaciale.objects.count()
        detections_identifiees = DetectionFaciale.objects.filter(detenu__isnull=False).count()
        detections_alertes = DetectionFaciale.objects.filter(est_alerte=True).count()
        
        confiance_moyenne = DetectionFaciale.objects.aggregate(
            avg_confiance=Avg('confiance')
        )['avg_confiance'] or 0
        
        # Dernières périodes
        detections_24h = DetectionFaciale.objects.filter(
            timestamp__gte=now - timedelta(hours=24)
        ).count()
        
        detections_7j = DetectionFaciale.objects.filter(
            timestamp__gte=now - timedelta(days=7)
        ).count()
        
        detections_30j = DetectionFaciale.objects.filter(
            timestamp__gte=now - timedelta(days=30)
        ).count()
        
        return Response({
            'total_detections': total_detections,
            'detections_identifiees': detections_identifiees,
            'detections_non_identifiees': total_detections - detections_identifiees,
            'detections_alertes': detections_alertes,
            'confiance_moyenne': round(confiance_moyenne, 2),
            'detections_24h': detections_24h,
            'detections_7j': detections_7j,
            'detections_30j': detections_30j
        })


class AlerteSurveillanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des alertes de surveillance"""
    queryset = AlerteSurveillance.objects.all()
    permission_classes = [IsAdminCentre]
    
    def get_serializer_class(self):
        if self.action in ['create']:
            return AlerteSurveillanceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AlerteSurveillanceUpdateSerializer
        return AlerteSurveillanceSerializer
    
    def get_queryset(self):
        queryset = AlerteSurveillance.objects.select_related(
            'camera', 'camera__centre', 'detection', 'detenu',
            'assigne_a', 'traitee_par'
        )
        
        # Filtrage par statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtrage par niveau
        niveau = self.request.query_params.get('niveau')
        if niveau:
            queryset = queryset.filter(niveau=niveau)
        
        # Filtrage par type
        type_alerte = self.request.query_params.get('type')
        if type_alerte:
            queryset = queryset.filter(type_alerte=type_alerte)
        
        # Filtrage par utilisateur assigné
        assigne_a = self.request.query_params.get('assigne_a')
        if assigne_a:
            queryset = queryset.filter(assigne_a_id=assigne_a)
        
        return queryset.order_by('-date_creation')
    
    @action(detail=True, methods=['post'])
    def assigner(self, request, pk=None):
        """Assigne une alerte à un utilisateur"""
        alerte = self.get_object()
        
        alerte.assigne_a = request.user
        alerte.statut = 'EN_COURS'
        alerte.save()
        
        return Response({'message': 'Alerte assignée avec succès'})
    
    @action(detail=True, methods=['post'])
    def resoudre(self, request, pk=None):
        """Marque une alerte comme résolue"""
        alerte = self.get_object()
        
        alerte.statut = 'RESOLUE'
        alerte.traitee_par = request.user
        alerte.date_traitement = timezone.now()
        alerte.resolution = request.data.get('resolution', '')
        alerte.save()
        
        return Response({'message': 'Alerte résolue avec succès'})
    
    @action(detail=True, methods=['post'])
    def fausse_alerte(self, request, pk=None):
        """Marque une alerte comme fausse alerte"""
        alerte = self.get_object()
        
        alerte.statut = 'FAUSSE_ALERTE'
        alerte.traitee_par = request.user
        alerte.date_traitement = timezone.now()
        alerte.resolution = request.data.get('resolution', 'Fausse alerte')
        alerte.save()
        
        return Response({'message': 'Alerte marquée comme fausse alerte'})
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne les statistiques des alertes"""
        now = timezone.now()
        
        # Statistiques générales
        total_alertes = AlerteSurveillance.objects.count()
        alertes_ouvertes = AlerteSurveillance.objects.filter(
            statut__in=['OUVERTE', 'EN_COURS']
        ).count()
        alertes_resolues = AlerteSurveillance.objects.filter(
            statut='RESOLUE'
        ).count()
        alertes_critiques = AlerteSurveillance.objects.filter(
            niveau='CRITIQUE',
            statut__in=['OUVERTE', 'EN_COURS']
        ).count()
        
        # Dernières périodes
        alertes_24h = AlerteSurveillance.objects.filter(
            date_creation__gte=now - timedelta(hours=24)
        ).count()
        
        # Temps de résolution moyen
        temps_resolution = AlerteSurveillance.objects.filter(
            statut='RESOLUE',
            date_traitement__isnull=False
        ).aggregate(
            avg_temps=Avg(F('date_traitement') - F('date_creation'))
        )['avg_temps']
        
        return Response({
            'total_alertes': total_alertes,
            'alertes_ouvertes': alertes_ouvertes,
            'alertes_en_cours': AlerteSurveillance.objects.filter(
                statut='EN_COURS'
            ).count(),
            'alertes_resolues': alertes_resolues,
            'alertes_critiques': alertes_critiques,
            'alertes_24h': alertes_24h,
            'temps_resolution_moyen': temps_resolution
        })


class SurveillanceDashboardViewSet(viewsets.ViewSet):
    """ViewSet pour le dashboard de surveillance"""
    permission_classes = [IsAdminCentre]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Retourne les données du dashboard de surveillance"""
        now = timezone.now()
        
        # Statistiques des caméras
        camera_stats = {
            'total_cameras': Camera.objects.count(),
            'cameras_actives': Camera.objects.filter(statut='ACTIVE').count(),
            'cameras_inactives': Camera.objects.filter(statut='INACTIVE').count(),
            'cameras_en_maintenance': Camera.objects.filter(statut='MAINTENANCE').count(),
            'cameras_hors_service': Camera.objects.filter(statut='HORS_SERVICE').count(),
        }
        
        total_cameras = camera_stats['total_cameras']
        if total_cameras > 0:
            camera_stats['taux_activite'] = round(
                (camera_stats['cameras_actives'] / total_cameras) * 100, 2
            )
        else:
            camera_stats['taux_activite'] = 0
        
        # Statistiques des détections
        detection_stats = {
            'total_detections': DetectionFaciale.objects.count(),
            'detections_identifiees': DetectionFaciale.objects.filter(
                detenu__isnull=False
            ).count(),
            'detections_alertes': DetectionFaciale.objects.filter(
                est_alerte=True
            ).count(),
            'detections_24h': DetectionFaciale.objects.filter(
                timestamp__gte=now - timedelta(hours=24)
            ).count(),
            'detections_7j': DetectionFaciale.objects.filter(
                timestamp__gte=now - timedelta(days=7)
            ).count(),
            'detections_30j': DetectionFaciale.objects.filter(
                timestamp__gte=now - timedelta(days=30)
            ).count(),
        }
        
        confiance_moyenne = DetectionFaciale.objects.aggregate(
            avg_confiance=Avg('confiance')
        )['avg_confiance'] or 0
        detection_stats['confiance_moyenne'] = round(confiance_moyenne, 2)
        
        detection_stats['detections_non_identifiees'] = (
            detection_stats['total_detections'] - detection_stats['detections_identifiees']
        )
        
        # Statistiques des alertes
        alerte_stats = {
            'total_alertes': AlerteSurveillance.objects.count(),
            'alertes_ouvertes': AlerteSurveillance.objects.filter(
                statut='OUVERTE'
            ).count(),
            'alertes_en_cours': AlerteSurveillance.objects.filter(
                statut='EN_COURS'
            ).count(),
            'alertes_resolues': AlerteSurveillance.objects.filter(
                statut='RESOLUE'
            ).count(),
            'alertes_critiques': AlerteSurveillance.objects.filter(
                niveau='CRITIQUE',
                statut__in=['OUVERTE', 'EN_COURS']
            ).count(),
            'alertes_24h': AlerteSurveillance.objects.filter(
                date_creation__gte=now - timedelta(hours=24)
            ).count(),
        }
        
        # Données récentes
        recentes_detections = DetectionFaciale.objects.select_related(
            'camera', 'detenu'
        ).order_by('-timestamp')[:10]
        
        alertes_actives = AlerteSurveillance.objects.filter(
            statut__in=['OUVERTE', 'EN_COURS']
        ).select_related('camera', 'detenu').order_by('-date_creation')[:10]
        
        dernieres_alertes = AlerteSurveillance.objects.select_related(
            'camera', 'detenu'
        ).order_by('-date_creation')[:10]
        
        return Response({
            'camera_stats': camera_stats,
            'detection_stats': detection_stats,
            'alerte_stats': alerte_stats,
            'recentes_detections': DetectionFacialeSerializer(
                recentes_detections, many=True
            ).data,
            'alertes_actives': AlerteSurveillanceSerializer(
                alertes_actives, many=True
            ).data,
            'dernieres_alertes': AlerteSurveillanceSerializer(
                dernieres_alertes, many=True
            ).data,
        })
    
    @action(detail=False, methods=['post'])
    def initialiser_systeme(self, request):
        """Initialise le système de surveillance"""
        try:
            detection_service.initialize_from_database()
            return Response({'message': 'Système initialisé avec succès'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
