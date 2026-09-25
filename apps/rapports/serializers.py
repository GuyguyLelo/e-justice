from rest_framework import serializers
from apps.comptes.serializers import UtilisateurListSerializer
from .models import Rapport, ModeleRapport, TableauBord, TypeRapport, StatutRapport


class RapportSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Rapport"""
    
    created_by_info = UtilisateurListSerializer(source='created_by', read_only=True)
    type_rapport_display = serializers.CharField(source='get_type_rapport_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    taille_fichier_mb = serializers.FloatField(source='get_taille_fichier_mb', read_only=True)
    
    class Meta:
        model = Rapport
        fields = [
            'id', 'nom', 'type_rapport', 'type_rapport_display', 'statut',
            'statut_display', 'description', 'date_debut', 'date_fin',
            'parametres', 'fichier', 'taille_fichier', 'taille_fichier_mb',
            'created_by', 'created_by_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RapportListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des rapports"""
    
    type_rapport_display = serializers.CharField(source='get_type_rapport_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    created_by_nom = serializers.CharField(source='created_by.get_full_name', read_only=True)
    taille_fichier_mb = serializers.FloatField(source='get_taille_fichier_mb', read_only=True)
    
    class Meta:
        model = Rapport
        fields = [
            'id', 'nom', 'type_rapport', 'type_rapport_display', 'statut',
            'statut_display', 'date_debut', 'date_fin', 'fichier',
            'taille_fichier_mb', 'created_by_nom', 'created_at'
        ]


class RapportCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un rapport"""
    
    class Meta:
        model = Rapport
        fields = [
            'nom', 'type_rapport', 'description', 'date_debut', 'date_fin', 'parametres'
        ]
    
    def create(self, validated_data):
        """Création d'un rapport"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ModeleRapportSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle ModeleRapport"""
    
    type_rapport_display = serializers.CharField(source='get_type_rapport_display', read_only=True)
    
    class Meta:
        model = ModeleRapport
        fields = [
            'id', 'nom', 'type_rapport', 'type_rapport_display', 'description',
            'template', 'parametres_defaut', 'est_actif', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModeleRapportListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des modèles de rapports"""
    
    type_rapport_display = serializers.CharField(source='get_type_rapport_display', read_only=True)
    
    class Meta:
        model = ModeleRapport
        fields = [
            'id', 'nom', 'type_rapport', 'type_rapport_display', 'description',
            'est_actif', 'created_at'
        ]


class TableauBordSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle TableauBord"""
    
    created_by_info = UtilisateurListSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = TableauBord
        fields = [
            'id', 'nom', 'description', 'configuration', 'est_public',
            'created_by', 'created_by_info', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Création d'un tableau de bord"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TableauBordListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des tableaux de bord"""
    
    created_by_nom = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = TableauBord
        fields = [
            'id', 'nom', 'description', 'est_public', 'created_by_nom', 'created_at'
        ]


class RapportStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des rapports"""
    
    total = serializers.IntegerField()
    en_cours = serializers.IntegerField()
    termines = serializers.IntegerField()
    erreurs = serializers.IntegerField()
    par_type = serializers.DictField()
    taille_totale_mb = serializers.FloatField()


class TypeRapportSerializer(serializers.Serializer):
    """Serializer pour les types de rapports"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_rapport(cls):
        """Retourne tous les types de rapports disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypeRapport.choices]


class StatutRapportSerializer(serializers.Serializer):
    """Serializer pour les statuts des rapports"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_statuts_rapport(cls):
        """Retourne tous les statuts de rapport disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in StatutRapport.choices]


class RapportGenerationSerializer(serializers.Serializer):
    """Serializer pour la génération de rapports"""
    
    type_rapport = serializers.ChoiceField(choices=TypeRapport.choices)
    date_debut = serializers.DateField(required=False)
    date_fin = serializers.DateField(required=False)
    parametres = serializers.JSONField(required=False)
    
    def validate_date_fin(self, value):
        """Validation de la date de fin"""
        if hasattr(self, 'initial_data'):
            date_debut = self.initial_data.get('date_debut')
            if date_debut and value and value < date_debut:
                raise serializers.ValidationError(
                    "La date de fin doit être postérieure à la date de début."
                )
        return value






