from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Utilisateur, Role


class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Utilisateur"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'telephone', 'adresse', 'date_embauche',
            'est_actif', 'photo', 'created_at', 'updated_at',
            'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validation personnalisée"""
        if 'password' in attrs and 'password_confirm' in attrs:
            if attrs['password'] != attrs['password_confirm']:
                raise serializers.ValidationError("Les mots de passe ne correspondent pas.")
        return attrs
    
    def create(self, validated_data):
        """Création d'un utilisateur avec mot de passe hashé"""
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = Utilisateur.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Mise à jour d'un utilisateur"""
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UtilisateurListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des utilisateurs"""
    
    nom_complet = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'nom_complet', 'role',
            'role_display', 'telephone', 'est_actif', 'created_at'
        ]


class UtilisateurDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un utilisateur"""
    
    nom_complet = serializers.CharField(source='get_full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nom_complet', 'role', 'role_display', 'telephone',
            'adresse', 'date_embauche', 'est_actif', 'photo',
            'permissions', 'created_at', 'updated_at'
        ]
    
    def get_permissions(self, obj):
        """Retourne les permissions de l'utilisateur"""
        return {
            'can_manage_detenus': obj.can_manage_detenus(),
            'can_manage_personnel': obj.can_manage_personnel(),
            'can_view_medical_records': obj.can_view_medical_records(),
            'can_manage_visits': obj.can_manage_visits(),
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour changer le mot de passe"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validation du changement de mot de passe"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Les nouveaux mots de passe ne correspondent pas.")
        return attrs
    
    def validate_old_password(self, value):
        """Validation de l'ancien mot de passe"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("L'ancien mot de passe est incorrect.")
        return value


class RoleSerializer(serializers.Serializer):
    """Serializer pour les rôles"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_roles(cls):
        """Retourne tous les rôles disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in Role.choices]
