from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Camera, ZoneSurveillance, ProfilFacialDetenu, 
    DetectionFaciale, AlerteSurveillance, HistoriqueSurveillance
)
from apps.detenus.serializers import DetenuSerializer
from apps.comptes.serializers import UtilisateurSerializer


class CameraSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les caméras"""
    centre_nom = serializers.CharField(source='centre.nom', read_only=True)
    est_en_ligne = serializers.BooleanField(read_only=True)
    url_complete = serializers.CharField(read_only=True)
    
    class Meta:
        model = Camera
        fields = [
            'id', 'nom', 'code', 'centre', 'centre_nom', 'type_camera', 
            'emplacement', 'description', 'adresse_ip', 'port', 'url_flux', 
            'resolution', 'fps', 'statut', 'detection_active', 
            'reconnaissance_faciale_active', 'qualite_detection', 
            'angle_vue', 'portee_max', 'date_installation', 'derniere_maintenance', 
            'created_at', 'updated_at', 'est_en_ligne', 'url_complete'
        ]
        read_only_fields = ['created_at', 'updated_at', 'date_installation']


class ZoneSurveillanceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les zones de surveillance"""
    camera_nom = serializers.CharField(source='camera.nom', read_only=True)
    
    class Meta:
        model = ZoneSurveillance
        fields = [
            'id', 'camera', 'camera_nom', 'nom', 'coordonnees', 'type_zone', 
            'detection_active', 'seuil_alerte', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProfilFacialDetenuSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les profils faciaux des détenus"""
    detenu_info = DetenuSerializer(source='detenu', read_only=True)
    created_by_info = UtilisateurSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = ProfilFacialDetenu
        fields = [
            'id', 'detenu', 'detenu_info', 'encodage_facial', 'image_reference', 
            'qualite_image', 'date_enregistrement', 'derniere_mise_a_jour', 
            'actif', 'created_by', 'created_by_info'
        ]
        read_only_fields = [
            'date_enregistrement', 'derniere_mise_a_jour', 'created_by'
        ]


class DetectionFacialeSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les détections faciales"""
    camera_info = CameraSerializer(source='camera', read_only=True)
    detenu_info = DetenuSerializer(source='detenu', read_only=True)
    zone_info = ZoneSurveillanceSerializer(source='zone', read_only=True)
    traitee_par_info = UtilisateurSerializer(source='traitee_par', read_only=True)
    est_identifie = serializers.BooleanField(read_only=True)
    niveau_confiance = serializers.CharField(read_only=True)
    
    class Meta:
        model = DetectionFaciale
        fields = [
            'id', 'camera', 'camera_info', 'detenu', 'detenu_info', 
            'zone', 'zone_info', 'image_detection', 'confiance', 
            'coordonnees_visage', 'timestamp', 'est_alerte', 'motif_alerte', 
            'traitee', 'traitee_par', 'traitee_par_info', 'date_traitement', 
            'notes', 'created_at', 'est_identifie', 'niveau_confiance'
        ]
        read_only_fields = ['created_at', 'timestamp', 'confiance', 'coordonnees_visage']


class DetectionFacialeCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création de détections faciales"""
    class Meta:
        model = DetectionFaciale
        fields = [
            'camera', 'detenu', 'zone', 'image_detection', 'confiance', 
            'coordonnees_visage', 'timestamp', 'est_alerte', 'motif_alerte'
        ]


class AlerteSurveillanceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les alertes de surveillance"""
    camera_info = CameraSerializer(source='camera', read_only=True)
    detection_info = DetectionFacialeSerializer(source='detection', read_only=True)
    detenu_info = DetenuSerializer(source='detenu', read_only=True)
    assigne_a_info = UtilisateurSerializer(source='assigne_a', read_only=True)
    traitee_par_info = UtilisateurSerializer(source='traitee_par', read_only=True)
    est_ouverte = serializers.BooleanField(read_only=True)
    delai_resolution = serializers.DurationField(read_only=True)
    
    class Meta:
        model = AlerteSurveillance
        fields = [
            'id', 'titre', 'type_alerte', 'niveau', 'description', 
            'camera', 'camera_info', 'detection', 'detection_info', 
            'detenu', 'detenu_info', 'statut', 'assigne_a', 'assigne_a_info', 
            'traitee_par', 'traitee_par_info', 'date_creation', 'date_traitement', 
            'resolution', 'created_at', 'updated_at', 'est_ouverte', 'delai_resolution'
        ]
        read_only_fields = ['created_at', 'updated_at', 'date_creation']


class AlerteSurveillanceCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'alertes"""
    class Meta:
        model = AlerteSurveillance
        fields = [
            'titre', 'type_alerte', 'niveau', 'description', 
            'camera', 'detection', 'detenu'
        ]


class AlerteSurveillanceUpdateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la mise à jour d'alertes"""
    class Meta:
        model = AlerteSurveillance
        fields = [
            'statut', 'assigne_a', 'traitee_par', 'date_traitement', 'resolution'
        ]


class HistoriqueSurveillanceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour l'historique de surveillance"""
    camera_info = CameraSerializer(source='camera', read_only=True)
    detection_info = DetectionFacialeSerializer(source='detection', read_only=True)
    alerte_info = AlerteSurveillanceSerializer(source='alerte', read_only=True)
    utilisateur_info = UtilisateurSerializer(source='utilisateur', read_only=True)
    
    class Meta:
        model = HistoriqueSurveillance
        fields = [
            'id', 'type_evenement', 'description', 'camera', 'camera_info', 
            'detection', 'detection_info', 'alerte', 'alerte_info', 
            'utilisateur', 'utilisateur_info', 'donnees_supplementaires', 
            'timestamp', 'adresse_ip', 'user_agent'
        ]
        read_only_fields = ['timestamp']


class CameraStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des caméras"""
    total_cameras = serializers.IntegerField()
    cameras_actives = serializers.IntegerField()
    cameras_inactives = serializers.IntegerField()
    cameras_en_maintenance = serializers.IntegerField()
    cameras_hors_service = serializers.IntegerField()
    taux_activite = serializers.FloatField()


class DetectionStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des détections"""
    total_detections = serializers.IntegerField()
    detections_identifiees = serializers.IntegerField()
    detections_non_identifiees = serializers.IntegerField()
    detections_alertes = serializers.IntegerField()
    confiance_moyenne = serializers.FloatField()
    detections_24h = serializers.IntegerField()
    detections_7j = serializers.IntegerField()
    detections_30j = serializers.IntegerField()


class AlerteStatsSerializer(serializers.Serializer):
    """Sérialiseur pour les statistiques des alertes"""
    total_alertes = serializers.IntegerField()
    alertes_ouvertes = serializers.IntegerField()
    alertes_en_cours = serializers.IntegerField()
    alertes_resolues = serializers.IntegerField()
    alertes_critiques = serializers.IntegerField()
    alertes_24h = serializers.IntegerField()
    temps_resolution_moyen = serializers.DurationField()


class SurveillanceDashboardSerializer(serializers.Serializer):
    """Sérialiseur pour le dashboard de surveillance"""
    camera_stats = CameraStatsSerializer()
    detection_stats = DetectionStatsSerializer()
    alerte_stats = AlerteStatsSerializer()
    recentes_detections = DetectionFacialeSerializer(many=True)
    alertes_actives = AlerteSurveillanceSerializer(many=True)
    dernieres_alertes = AlerteSurveillanceSerializer(many=True)
