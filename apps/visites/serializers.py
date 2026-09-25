from rest_framework import serializers
from apps.detenus.serializers import DetenuListSerializer
from apps.comptes.serializers import UtilisateurListSerializer
from .models import Visiteur, Visite, ObjetVisite, TypeVisiteur, StatutVisite


class VisiteurSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Visiteur"""
    
    nom_complet = serializers.CharField(source='nom_complet', read_only=True)
    type_visiteur_display = serializers.CharField(source='get_type_visiteur_display', read_only=True)
    
    class Meta:
        model = Visiteur
        fields = [
            'id', 'nom', 'prenom', 'nom_complet', 'type_visiteur', 'type_visiteur_display',
            'piece_identite', 'numero_piece', 'telephone', 'adresse', 'relation_detenu',
            'cabinet_avocat', 'numero_ordre_avocat', 'photo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VisiteurListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des visiteurs"""
    
    nom_complet = serializers.CharField(source='nom_complet', read_only=True)
    type_visiteur_display = serializers.CharField(source='get_type_visiteur_display', read_only=True)
    
    class Meta:
        model = Visiteur
        fields = [
            'id', 'nom_complet', 'type_visiteur', 'type_visiteur_display',
            'telephone', 'relation_detenu', 'photo', 'created_at'
        ]


class ObjetVisiteSerializer(serializers.ModelSerializer):
    """Serializer pour les objets de visite"""
    
    class Meta:
        model = ObjetVisite
        fields = [
            'id', 'nom_objet', 'quantite', 'autorise', 'motif_refus', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class VisiteSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Visite"""
    
    detenu_info = DetenuListSerializer(source='detenu', read_only=True)
    visiteur_info = VisiteurListSerializer(source='visiteur', read_only=True)
    agent_controle_info = UtilisateurListSerializer(source='agent_controle', read_only=True)
    created_by_info = UtilisateurListSerializer(source='created_by', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    objets = ObjetVisiteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Visite
        fields = [
            'id', 'detenu', 'detenu_info', 'visiteur', 'visiteur_info',
            'date_visite', 'duree_minutes', 'statut', 'statut_display',
            'motif_refus', 'objets_apportes', 'objets_autorises', 'objets_refuses',
            'agent_controle', 'agent_controle_info', 'observations',
            'created_by', 'created_by_info', 'objets', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_date_visite(self, value):
        """Validation de la date de visite"""
        from django.utils import timezone
        if value < timezone.now():
            raise serializers.ValidationError("La date de visite ne peut pas être dans le passé.")
        return value
    
    def validate_duree_minutes(self, value):
        """Validation de la durée de visite"""
        if value < 15:
            raise serializers.ValidationError("La durée minimum est de 15 minutes.")
        if value > 180:
            raise serializers.ValidationError("La durée maximum est de 180 minutes.")
        return value


class VisiteListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des visites"""
    
    detenu_nom = serializers.CharField(source='detenu.nom_complet', read_only=True)
    visiteur_nom = serializers.CharField(source='visiteur.nom_complet', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Visite
        fields = [
            'id', 'detenu_nom', 'visiteur_nom', 'date_visite', 'duree_minutes',
            'statut', 'statut_display', 'created_at'
        ]


class VisiteDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une visite"""
    
    detenu_info = DetenuListSerializer(source='detenu', read_only=True)
    visiteur_info = VisiteurListSerializer(source='visiteur', read_only=True)
    agent_controle_info = UtilisateurListSerializer(source='agent_controle', read_only=True)
    created_by_info = UtilisateurListSerializer(source='created_by', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    objets = ObjetVisiteSerializer(many=True, read_only=True)
    
    class Meta:
        model = Visite
        fields = [
            'id', 'detenu', 'detenu_info', 'visiteur', 'visiteur_info',
            'date_visite', 'duree_minutes', 'statut', 'statut_display',
            'motif_refus', 'objets_apportes', 'objets_autorises', 'objets_refuses',
            'agent_controle', 'agent_controle_info', 'observations',
            'created_by', 'created_by_info', 'objets', 'created_at', 'updated_at'
        ]


class VisiteCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une visite"""
    
    objets = ObjetVisiteSerializer(many=True, required=False)
    
    class Meta:
        model = Visite
        fields = [
            'detenu', 'visiteur', 'date_visite', 'duree_minutes',
            'objets_apportes', 'objets', 'observations'
        ]
    
    def create(self, validated_data):
        """Création d'une visite avec objets"""
        objets_data = validated_data.pop('objets', [])
        visite = Visite.objects.create(**validated_data)
        
        for objet_data in objets_data:
            ObjetVisite.objects.create(visite=visite, **objet_data)
        
        return visite


class VisiteUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour une visite"""
    
    class Meta:
        model = Visite
        fields = [
            'statut', 'motif_refus', 'objets_autorises', 'objets_refuses',
            'agent_controle', 'observations'
        ]


class VisiteStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des visites"""
    
    total = serializers.IntegerField()
    programmees = serializers.IntegerField()
    en_cours = serializers.IntegerField()
    terminees = serializers.IntegerField()
    annulees = serializers.IntegerField()
    refusees = serializers.IntegerField()
    par_type_visiteur = serializers.DictField()
    par_jour = serializers.DictField()


class TypeVisiteurSerializer(serializers.Serializer):
    """Serializer pour les types de visiteurs"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_visiteur(cls):
        """Retourne tous les types de visiteurs disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypeVisiteur.choices]


class StatutVisiteSerializer(serializers.Serializer):
    """Serializer pour les statuts des visites"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_statuts_visite(cls):
        """Retourne tous les statuts de visite disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in StatutVisite.choices]





