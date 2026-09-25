from rest_framework import serializers
from apps.comptes.serializers import UtilisateurListSerializer
from .models import (
    Detenu, HistoriqueDetenu, StatutDetenu, TypePeine,
    CentrePenitencier, CentrePhoto, AdminPrison, TypeCentre
)


class DetenuSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Detenu"""
    
    nom_complet = serializers.CharField(source='nom_complet', read_only=True)
    age = serializers.IntegerField(source='age', read_only=True)
    duree_detention = serializers.IntegerField(source='duree_detention', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Detenu
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet', 'sexe',
            'date_naissance', 'lieu_naissance', 'nationalite', 'profession',
            'adresse', 'telephone', 'date_arrestation', 'date_incarceration',
            'motif_incarceration', 'tribunal', 'numero_dossier', 'dossier', 'avocat',
            'telephone_avocat', 'cellule', 'regime', 'statut', 'duree_peine_mois',
            'date_liberation_prevue', 'date_liberation_effective', 'motif_liberation',
            'groupe_sanguin', 'allergies', 'maladies_chroniques', 'age',
            'duree_detention', 'created_by', 'created_by_name', 'created_at', 'updated_at',
            # Données biométriques
            'taille', 'poids', 'couleur_yeux', 'couleur_cheveux', 'type_cheveux',
            'couleur_peau', 'cicatrices', 'photo_face', 'photo_profil',
            'empreintes_digitales', 'adn'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_matricule(self, value):
        """Validation de l'unicité du matricule"""
        if self.instance and self.instance.matricule == value:
            return value
        
        if Detenu.objects.filter(matricule=value).exists():
            raise serializers.ValidationError("Ce matricule existe déjà.")
        return value
    
    def validate_date_liberation_prevue(self, value):
        """Validation de la date de libération prévue"""
        if value and hasattr(self, 'initial_data'):
            date_incarceration = self.initial_data.get('date_incarceration')
            if date_incarceration and value <= date_incarceration:
                raise serializers.ValidationError(
                    "La date de libération prévue doit être postérieure à la date d'incarcération."
                )
        return value


class DetenuListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des détenus"""
    
    nom_complet = serializers.CharField(source='nom_complet', read_only=True)
    age = serializers.IntegerField(source='age', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    regime_display = serializers.CharField(source='get_regime_display', read_only=True)
    
    class Meta:
        model = Detenu
        fields = [
            'id', 'matricule', 'nom_complet', 'sexe', 'age',
            'date_incarceration', 'cellule', 'regime', 'regime_display',
            'statut', 'statut_display', 'created_at'
        ]


class DetenuDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un détenu"""
    
    nom_complet = serializers.CharField(source='nom_complet', read_only=True)
    age = serializers.IntegerField(source='age', read_only=True)
    duree_detention = serializers.IntegerField(source='duree_detention', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    regime_display = serializers.CharField(source='get_regime_display', read_only=True)
    created_by_info = UtilisateurListSerializer(source='created_by', read_only=True)
    historique = serializers.SerializerMethodField()
    
    class Meta:
        model = Detenu
        fields = [
            'id', 'matricule', 'nom', 'prenom', 'nom_complet', 'sexe',
            'date_naissance', 'lieu_naissance', 'nationalite', 'profession',
            'adresse', 'telephone', 'date_arrestation', 'date_incarceration',
            'motif_incarceration', 'tribunal', 'numero_dossier', 'dossier', 'avocat',
            'telephone_avocat', 'cellule', 'regime', 'regime_display', 'statut',
            'statut_display', 'duree_peine_mois', 'date_liberation_prevue',
            'date_liberation_effective', 'motif_liberation', 'groupe_sanguin',
            'allergies', 'maladies_chroniques', 'age', 'duree_detention',
            'created_by_info', 'historique', 'created_at', 'updated_at',
            # Données biométriques
            'taille', 'poids', 'couleur_yeux', 'couleur_cheveux', 'type_cheveux',
            'couleur_peau', 'cicatrices', 'photo_face', 'photo_profil',
            'empreintes_digitales', 'adn'
        ]
    
    def get_historique(self, obj):
        """Retourne l'historique du détenu"""
        historique = obj.historique.all()[:10]  # 10 derniers éléments
        return HistoriqueDetenuSerializer(historique, many=True).data


class HistoriqueDetenuSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des détenus"""
    
    utilisateur_name = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    
    class Meta:
        model = HistoriqueDetenu
        fields = [
            'id', 'action', 'ancienne_valeur', 'nouvelle_valeur',
            'utilisateur_name', 'created_at'
        ]


class DetenuStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des détenus"""
    
    total = serializers.IntegerField()
    incarceres = serializers.IntegerField()
    liberes = serializers.IntegerField()
    transferes = serializers.IntegerField()
    evades = serializers.IntegerField()
    decedes = serializers.IntegerField()
    par_sexe = serializers.DictField()
    par_age = serializers.DictField()
    par_regime = serializers.DictField()


class LiberationSerializer(serializers.Serializer):
    """Serializer pour la libération d'un détenu"""
    
    date_liberation = serializers.DateField()
    motif_liberation = serializers.CharField(max_length=500)
    
    def validate_date_liberation(self, value):
        """Validation de la date de libération"""
        detenu = self.context['detenu']
        if value < detenu.date_incarceration:
            raise serializers.ValidationError(
                "La date de libération doit être postérieure à la date d'incarcération."
            )
        return value


class TransfertSerializer(serializers.Serializer):
    """Serializer pour le transfert d'un détenu"""
    
    destination = serializers.CharField(max_length=200)
    motif_transfert = serializers.CharField(max_length=500)
    date_transfert = serializers.DateField()
    
    def validate_date_transfert(self, value):
        """Validation de la date de transfert"""
        detenu = self.context['detenu']
        if value < detenu.date_incarceration:
            raise serializers.ValidationError(
                "La date de transfert doit être postérieure à la date d'incarcération."
            )
        return value


class StatutDetenuSerializer(serializers.Serializer):
    """Serializer pour les statuts de détenus"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_statuts(cls):
        """Retourne tous les statuts disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in StatutDetenu.choices]


class TypePeineSerializer(serializers.Serializer):
    """Serializer pour les types de peines"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_peine(cls):
        """Retourne tous les types de peines disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypePeine.choices]


class CentrePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentrePhoto
        fields = ['id', 'image', 'legende', 'ordre']


class CentrePenitencierSerializer(serializers.ModelSerializer):
    """Serializer pour les centres pénitenciers"""
    
    taux_occupation = serializers.FloatField(source='taux_occupation', read_only=True)
    places_disponibles = serializers.IntegerField(source='places_disponibles', read_only=True)
    type_centre_display = serializers.CharField(source='get_type_centre_display', read_only=True)
    photos = CentrePhotoSerializer(many=True, read_only=True)
    
    class Meta:
        model = CentrePenitencier
        fields = [
            'id', 'nom', 'code', 'type_centre', 'type_centre_display',
            'adresse', 'province', 'ville', 'latitude', 'longitude',
            'telephone', 'email', 'capacite_max', 'capacite_actuelle',
            'taux_occupation', 'places_disponibles', 'directeur', 'date_ouverture',
            'photos', 'statut', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_capacite_actuelle(self, value):
        """Validation de la capacité actuelle"""
        if value > self.initial_data.get('capacite_max', 0):
            raise serializers.ValidationError(
                "La capacité actuelle ne peut pas dépasser la capacité maximale."
            )
        return value


class CentrePenitencierListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des centres"""
    
    type_centre_display = serializers.CharField(source='get_type_centre_display', read_only=True)
    taux_occupation = serializers.FloatField(source='taux_occupation', read_only=True)
    
    class Meta:
        model = CentrePenitencier
        fields = [
            'id', 'nom', 'code', 'type_centre', 'type_centre_display',
            'province', 'ville', 'latitude', 'longitude',
            'capacite_max', 'capacite_actuelle', 'taux_occupation',
            'directeur', 'statut'
        ]


class AdminPrisonSerializer(serializers.ModelSerializer):
    """Serializer pour les administrateurs de prison"""
    
    utilisateur_info = UtilisateurListSerializer(source='utilisateur', read_only=True)
    centre_info = CentrePenitencierListSerializer(source='centre', read_only=True)
    
    class Meta:
        model = AdminPrison
        fields = [
            'id', 'utilisateur', 'utilisateur_info', 'centre', 'centre_info',
            'matricule_admin', 'poste', 'date_affectation', 'statut',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminPrisonListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des admins"""
    
    utilisateur_name = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    centre_name = serializers.CharField(source='centre.nom', read_only=True)
    
    class Meta:
        model = AdminPrison
        fields = [
            'id', 'utilisateur_name', 'centre_name', 'matricule_admin',
            'poste', 'date_affectation', 'statut'
        ]


class TypeCentreSerializer(serializers.Serializer):
    """Serializer pour les types de centres"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_centre(cls):
        """Retourne tous les types de centres disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypeCentre.choices]


class CentreStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des centres"""
    
    total_centres = serializers.IntegerField()
    centres_actifs = serializers.IntegerField()
    capacite_totale = serializers.IntegerField()
    capacite_utilisee = serializers.IntegerField()
    taux_occupation_global = serializers.FloatField()
    places_disponibles_totales = serializers.IntegerField()
    par_type_centre = serializers.DictField()
    centres_plus_charges = serializers.ListField()






