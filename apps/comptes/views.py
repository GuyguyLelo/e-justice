from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import Utilisateur, Role
from .serializers import (
    UtilisateurSerializer, UtilisateurListSerializer, UtilisateurDetailSerializer,
    ChangePasswordSerializer, RoleSerializer
)


class UtilisateurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des utilisateurs
    """
    queryset = Utilisateur.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return UtilisateurListSerializer
        elif self.action == 'retrieve':
            return UtilisateurDetailSerializer
        return UtilisateurSerializer
    
    def get_queryset(self):
        """Filtre les utilisateurs selon les permissions"""
        user = self.request.user
        
        # Les administrateurs voient tous les utilisateurs
        if user.is_admin():
            return Utilisateur.objects.all()
        
        # Les directeurs voient tous sauf les administrateurs
        elif user.is_directeur():
            return Utilisateur.objects.exclude(role=Role.ADMIN)
        
        # Les autres voient seulement les agents et visiteurs
        else:
            return Utilisateur.objects.filter(role__in=[Role.AGENT, Role.VISITEUR])
    
    def perform_create(self, serializer):
        """Création d'un utilisateur avec l'utilisateur connecté comme créateur"""
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retourne les informations de l'utilisateur connecté"""
        serializer = UtilisateurDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change le mot de passe de l'utilisateur connecté"""
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Mot de passe modifié avec succès.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Active un utilisateur"""
        user = self.get_object()
        user.est_actif = True
        user.save()
        return Response({'message': 'Utilisateur activé avec succès.'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Désactive un utilisateur"""
        user = self.get_object()
        user.est_actif = False
        user.save()
        return Response({'message': 'Utilisateur désactivé avec succès.'})
    
    @action(detail=False, methods=['get'])
    def roles(self, request):
        """Retourne la liste des rôles disponibles"""
        roles = RoleSerializer.get_roles()
        return Response(roles)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des utilisateurs"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'actifs': queryset.filter(est_actif=True).count(),
            'inactifs': queryset.filter(est_actif=False).count(),
            'par_role': {}
        }
        
        # Statistiques par rôle
        for role_value, role_label in Role.choices:
            stats['par_role'][role_label] = queryset.filter(role=role_value).count()
        
        return Response(stats)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Vue personnalisée pour l'obtention des tokens JWT
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Ajouter des informations utilisateur à la réponse
            user = authenticate(
                username=request.data.get('username'),
                password=request.data.get('password')
            )
            
            if user:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                    'nom_complet': user.get_full_name(),
                    'permissions': {
                        'can_manage_detenus': user.can_manage_detenus(),
                        'can_manage_personnel': user.can_manage_personnel(),
                        'can_view_medical_records': user.can_view_medical_records(),
                        'can_manage_visits': user.can_manage_visits(),
                    }
                }
                response.data['user'] = user_data
        
        return response