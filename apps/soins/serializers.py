from rest_framework import serializers
from apps.detenus.serializers import DetenuListSerializer
from apps.comptes.serializers import UtilisateurListSerializer
from .models import (
    Consultation, Medicament, Prescription, AntecedentMedical, Vaccination,
    TypeConsultation, StatutConsultation, TypeMedicament
)


class MedicamentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Medicament"""
    
    type_medicament_display = serializers.CharField(source='get_type_medicament_display', read_only=True)
    unite_mesure_display = serializers.CharField(source='get_unite_mesure_display', read_only=True)
    stock_faible = serializers.BooleanField(source='is_stock_faible', read_only=True)
    expire = serializers.BooleanField(source='is_expire', read_only=True)
    
    class Meta:
        model = Medicament
        fields = [
            'id', 'nom', 'nom_commercial', 'type_medicament', 'type_medicament_display',
            'forme_pharmaceutique', 'dosage', 'stock_actuel', 'stock_minimum',
            'date_expiration', 'prix_unitaire', 'stock_faible', 'expire',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_stock_actuel(self, value):
        """Validation du stock actuel"""
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif.")
        return value


class MedicamentListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des médicaments"""
    
    type_medicament_display = serializers.CharField(source='get_type_medicament_display', read_only=True)
    stock_faible = serializers.BooleanField(source='is_stock_faible', read_only=True)
    
    class Meta:
        model = Medicament
        fields = [
            'id', 'nom', 'type_medicament', 'type_medicament_display',
            'stock_actuel', 'stock_minimum', 'stock_faible', 'created_at'
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Prescription"""
    
    medicament_nom = serializers.CharField(source='medicament.nom', read_only=True)
    medicament_dosage = serializers.CharField(source='medicament.dosage', read_only=True)
    
    class Meta:
        model = Prescription
        fields = [
            'id', 'medicament', 'medicament_nom', 'medicament_dosage',
            'posologie', 'duree_jours', 'quantite_prescrit', 'instructions',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ConsultationSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Consultation"""
    
    detenu_info = DetenuListSerializer(source='detenu', read_only=True)
    medecin_info = UtilisateurListSerializer(source='medecin', read_only=True)
    type_consultation_display = serializers.CharField(source='get_type_consultation_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'detenu', 'detenu_info', 'medecin', 'medecin_info',
            'type_consultation', 'type_consultation_display', 'date_consultation',
            'statut', 'statut_display', 'symptomes', 'diagnostic', 'traitement_prescrit',
            'recommandations', 'date_controle', 'urgence', 'prescriptions',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_date_consultation(self, value):
        """Validation de la date de consultation"""
        from datetime import datetime
        if value > datetime.now():
            raise serializers.ValidationError("La date de consultation ne peut pas être dans le futur.")
        return value


class ConsultationListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des consultations"""
    
    detenu_nom = serializers.CharField(source='detenu.nom_complet', read_only=True)
    medecin_nom = serializers.CharField(source='medecin.get_full_name', read_only=True)
    type_consultation_display = serializers.CharField(source='get_type_consultation_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'detenu_nom', 'medecin_nom', 'type_consultation',
            'type_consultation_display', 'date_consultation', 'statut',
            'statut_display', 'urgence', 'created_at'
        ]


class ConsultationDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une consultation"""
    
    detenu_info = DetenuListSerializer(source='detenu', read_only=True)
    medecin_info = UtilisateurListSerializer(source='medecin', read_only=True)
    type_consultation_display = serializers.CharField(source='get_type_consultation_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'detenu', 'detenu_info', 'medecin', 'medecin_info',
            'type_consultation', 'type_consultation_display', 'date_consultation',
            'statut', 'statut_display', 'symptomes', 'diagnostic', 'traitement_prescrit',
            'recommandations', 'date_controle', 'urgence', 'prescriptions',
            'created_at', 'updated_at'
        ]


class AntecedentMedicalSerializer(serializers.ModelSerializer):
    """Serializer pour les antécédents médicaux"""
    
    class Meta:
        model = AntecedentMedical
        fields = [
            'id', 'type_antecedent', 'description', 'date_debut', 'date_fin',
            'traitement_suivi', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_date_fin(self, value):
        """Validation de la date de fin"""
        if hasattr(self, 'initial_data'):
            date_debut = self.initial_data.get('date_debut')
            if date_debut and value and value <= date_debut:
                raise serializers.ValidationError(
                    "La date de fin doit être postérieure à la date de début."
                )
        return value


class VaccinationSerializer(serializers.ModelSerializer):
    """Serializer pour les vaccinations"""
    
    detenu_nom = serializers.CharField(source='detenu.nom_complet', read_only=True)
    medecin_nom = serializers.CharField(source='medecin_vaccinateur.get_full_name', read_only=True)
    
    class Meta:
        model = Vaccination
        fields = [
            'id', 'detenu', 'detenu_nom', 'nom_vaccin', 'date_vaccination',
            'lot_vaccin', 'medecin_vaccinateur', 'medecin_nom', 'effets_secondaires',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une consultation"""
    
    prescriptions = PrescriptionSerializer(many=True, required=False)
    
    class Meta:
        model = Consultation
        fields = [
            'detenu', 'type_consultation', 'date_consultation', 'symptomes',
            'diagnostic', 'traitement_prescrit', 'recommandations', 'date_controle',
            'urgence', 'prescriptions'
        ]
    
    def create(self, validated_data):
        """Création d'une consultation avec prescriptions"""
        prescriptions_data = validated_data.pop('prescriptions', [])
        consultation = Consultation.objects.create(**validated_data)
        
        for prescription_data in prescriptions_data:
            Prescription.objects.create(consultation=consultation, **prescription_data)
        
        return consultation


class MedicamentStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des médicaments"""
    
    total = serializers.IntegerField()
    stock_faible = serializers.IntegerField()
    expires = serializers.IntegerField()
    par_type = serializers.DictField()
    valeur_stock = serializers.DecimalField(max_digits=12, decimal_places=2)


class ConsultationStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des consultations"""
    
    total = serializers.IntegerField()
    programmees = serializers.IntegerField()
    en_cours = serializers.IntegerField()
    terminees = serializers.IntegerField()
    annulees = serializers.IntegerField()
    urgences = serializers.IntegerField()
    par_type = serializers.DictField()
    par_medecin = serializers.DictField()


class TypeConsultationSerializer(serializers.Serializer):
    """Serializer pour les types de consultations"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_consultation(cls):
        """Retourne tous les types de consultations disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypeConsultation.choices]


class StatutConsultationSerializer(serializers.Serializer):
    """Serializer pour les statuts des consultations"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_statuts_consultation(cls):
        """Retourne tous les statuts de consultation disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in StatutConsultation.choices]


class TypeMedicamentSerializer(serializers.Serializer):
    """Serializer pour les types de médicaments"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_medicament(cls):
        """Retourne tous les types de médicaments disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypeMedicament.choices]






