from rest_framework import serializers
from apps.comptes.serializers import UtilisateurListSerializer
from .models import Personnel, FormationPersonnel, SanctionPersonnel, TypePersonnel, StatutPersonnel


class PersonnelSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Personnel"""
    
    utilisateur_info = UtilisateurListSerializer(source='utilisateur', read_only=True)
    anciennete = serializers.IntegerField(source='anciennete_annees', read_only=True)
    type_personnel_display = serializers.CharField(source='get_type_personnel_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = Personnel
        fields = [
            'id', 'utilisateur', 'utilisateur_info', 'matricule', 'type_personnel',
            'type_personnel_display', 'statut', 'statut_display', 'date_embauche',
            'date_fin_contrat', 'salaire', 'specialite', 'numero_ordre',
            'heures_travail_semaine', 'contact_urgence_nom', 'contact_urgence_telephone',
            'contact_urgence_relation', 'anciennete', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_matricule(self, value):
        """Validation de l'unicité du matricule"""
        if self.instance and self.instance.matricule == value:
            return value
        
        if Personnel.objects.filter(matricule=value).exists():
            raise serializers.ValidationError("Ce matricule existe déjà.")
        return value
    
    def validate_date_fin_contrat(self, value):
        """Validation de la date de fin de contrat"""
        if value and hasattr(self, 'initial_data'):
            date_embauche = self.initial_data.get('date_embauche')
            if date_embauche and value <= date_embauche:
                raise serializers.ValidationError(
                    "La date de fin de contrat doit être postérieure à la date d'embauche."
                )
        return value


class PersonnelListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste du personnel"""
    
    nom_complet = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    email = serializers.CharField(source='utilisateur.email', read_only=True)
    telephone = serializers.CharField(source='utilisateur.telephone', read_only=True)
    type_personnel_display = serializers.CharField(source='get_type_personnel_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    anciennete = serializers.IntegerField(source='anciennete_annees', read_only=True)
    
    class Meta:
        model = Personnel
        fields = [
            'id', 'matricule', 'nom_complet', 'email', 'telephone',
            'type_personnel', 'type_personnel_display', 'statut', 'statut_display',
            'date_embauche', 'anciennete', 'created_at'
        ]


class PersonnelDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un membre du personnel"""
    
    utilisateur_info = UtilisateurListSerializer(source='utilisateur', read_only=True)
    anciennete = serializers.IntegerField(source='anciennete_annees', read_only=True)
    type_personnel_display = serializers.CharField(source='get_type_personnel_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    formations = serializers.SerializerMethodField()
    sanctions = serializers.SerializerMethodField()
    
    class Meta:
        model = Personnel
        fields = [
            'id', 'utilisateur', 'utilisateur_info', 'matricule', 'type_personnel',
            'type_personnel_display', 'statut', 'statut_display', 'date_embauche',
            'date_fin_contrat', 'salaire', 'specialite', 'numero_ordre',
            'heures_travail_semaine', 'contact_urgence_nom', 'contact_urgence_telephone',
            'contact_urgence_relation', 'anciennete', 'formations', 'sanctions',
            'created_at', 'updated_at'
        ]
    
    def get_formations(self, obj):
        """Retourne les formations du personnel"""
        formations = obj.formations.all()[:5]  # 5 dernières formations
        return FormationPersonnelSerializer(formations, many=True).data
    
    def get_sanctions(self, obj):
        """Retourne les sanctions du personnel"""
        sanctions = obj.sanctions.all()[:5]  # 5 dernières sanctions
        return SanctionPersonnelSerializer(sanctions, many=True).data


class FormationPersonnelSerializer(serializers.ModelSerializer):
    """Serializer pour les formations du personnel"""
    
    class Meta:
        model = FormationPersonnel
        fields = [
            'id', 'nom_formation', 'organisme', 'date_debut', 'date_fin',
            'duree_heures', 'certificat', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_date_fin(self, value):
        """Validation de la date de fin de formation"""
        if hasattr(self, 'initial_data'):
            date_debut = self.initial_data.get('date_debut')
            if date_debut and value <= date_debut:
                raise serializers.ValidationError(
                    "La date de fin doit être postérieure à la date de début."
                )
        return value


class SanctionPersonnelSerializer(serializers.ModelSerializer):
    """Serializer pour les sanctions du personnel"""
    
    sanctionne_par_name = serializers.CharField(source='sanctionne_par.get_full_name', read_only=True)
    
    class Meta:
        model = SanctionPersonnel
        fields = [
            'id', 'type_sanction', 'motif', 'date_sanction', 'duree_jours',
            'sanctionne_par', 'sanctionne_par_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PersonnelStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du personnel"""
    
    total = serializers.IntegerField()
    actifs = serializers.IntegerField()
    inactifs = serializers.IntegerField()
    en_conge = serializers.IntegerField()
    suspendus = serializers.IntegerField()
    retraites = serializers.IntegerField()
    par_type = serializers.DictField()
    par_anciennete = serializers.DictField()


class TypePersonnelSerializer(serializers.Serializer):
    """Serializer pour les types de personnel"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_personnel(cls):
        """Retourne tous les types de personnel disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypePersonnel.choices]


class StatutPersonnelSerializer(serializers.Serializer):
    """Serializer pour les statuts du personnel"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_statuts_personnel(cls):
        """Retourne tous les statuts du personnel disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in StatutPersonnel.choices]






