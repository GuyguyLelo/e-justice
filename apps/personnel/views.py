from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Personnel, FormationPersonnel, SanctionPersonnel, TypePersonnel, StatutPersonnel
from .serializers import (
    PersonnelSerializer, PersonnelListSerializer, PersonnelDetailSerializer,
    FormationPersonnelSerializer, SanctionPersonnelSerializer, PersonnelStatsSerializer,
    TypePersonnelSerializer, StatutPersonnelSerializer
)


class PersonnelViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion du personnel
    """
    queryset = Personnel.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return PersonnelListSerializer
        elif self.action == 'retrieve':
            return PersonnelDetailSerializer
        return PersonnelSerializer
    
    def get_queryset(self):
        """Filtre le personnel selon les permissions"""
        user = self.request.user
        queryset = Personnel.objects.all()
        
        # Si l'utilisateur est un admin de prison, il ne voit que le personnel de son centre
        if hasattr(user, 'adminprison'):
            queryset = queryset.filter(centre=user.adminprison.centre)
        
        # Filtres par paramètres de requête
        type_personnel = self.request.query_params.get('type_personnel')
        if type_personnel:
            queryset = queryset.filter(type_personnel=type_personnel)
        
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Recherche par nom ou matricule
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(utilisateur__last_name__icontains=search) |
                Q(utilisateur__first_name__icontains=search) |
                Q(matricule__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Création d'un membre du personnel avec le centre de l'admin"""
        user = self.request.user
        
        # Si l'utilisateur est un admin de prison, assigner automatiquement son centre
        if hasattr(user, 'adminprison'):
            serializer.save(centre=user.adminprison.centre)
        else:
            # Pour l'admin central, le centre doit être spécifié dans les données
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Active un membre du personnel"""
        personnel = self.get_object()
        personnel.statut = StatutPersonnel.ACTIF
        personnel.save()
        return Response({'message': 'Personnel activé avec succès.'})
    
    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """Désactive un membre du personnel"""
        personnel = self.get_object()
        personnel.statut = StatutPersonnel.INACTIF
        personnel.save()
        return Response({'message': 'Personnel désactivé avec succès.'})
    
    @action(detail=True, methods=['post'])
    def suspendre(self, request, pk=None):
        """Suspend un membre du personnel"""
        personnel = self.get_object()
        personnel.statut = StatutPersonnel.SUSPENDU
        personnel.save()
        return Response({'message': 'Personnel suspendu avec succès.'})
    
    @action(detail=True, methods=['post'])
    def mettre_retraite(self, request, pk=None):
        """Met un membre du personnel à la retraite"""
        personnel = self.get_object()
        personnel.statut = StatutPersonnel.RETRAITE
        personnel.save()
        return Response({'message': 'Personnel mis à la retraite avec succès.'})
    
    @action(detail=True, methods=['get'])
    def formations(self, request, pk=None):
        """Retourne les formations d'un membre du personnel"""
        personnel = self.get_object()
        formations = personnel.formations.all()
        serializer = FormationPersonnelSerializer(formations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sanctions(self, request, pk=None):
        """Retourne les sanctions d'un membre du personnel"""
        personnel = self.get_object()
        sanctions = personnel.sanctions.all()
        serializer = SanctionPersonnelSerializer(sanctions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def ajouter_formation(self, request, pk=None):
        """Ajoute une formation à un membre du personnel"""
        personnel = self.get_object()
        serializer = FormationPersonnelSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(personnel=personnel)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def ajouter_sanction(self, request, pk=None):
        """Ajoute une sanction à un membre du personnel"""
        personnel = self.get_object()
        serializer = SanctionPersonnelSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(personnel=personnel, sanctionne_par=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques du personnel"""
        queryset = self.get_queryset()
        
        # Statistiques générales
        stats = {
            'total': queryset.count(),
            'actifs': queryset.filter(statut=StatutPersonnel.ACTIF).count(),
            'inactifs': queryset.filter(statut=StatutPersonnel.INACTIF).count(),
            'en_conge': queryset.filter(statut=StatutPersonnel.CONGE).count(),
            'suspendus': queryset.filter(statut=StatutPersonnel.SUSPENDU).count(),
            'retraites': queryset.filter(statut=StatutPersonnel.RETRAITE).count(),
        }
        
        # Statistiques par type de personnel
        stats['par_type'] = {}
        for type_value, type_label in TypePersonnel.choices:
            stats['par_type'][type_label] = queryset.filter(type_personnel=type_value).count()
        
        # Statistiques par ancienneté
        now = timezone.now().date()
        stats['par_anciennete'] = {
            '0-2 ans': queryset.filter(date_embauche__gte=now.replace(year=now.year-2)).count(),
            '3-5 ans': queryset.filter(date_embauche__gte=now.replace(year=now.year-5),
                                     date_embauche__lt=now.replace(year=now.year-3)).count(),
            '6-10 ans': queryset.filter(date_embauche__gte=now.replace(year=now.year-10),
                                      date_embauche__lt=now.replace(year=now.year-6)).count(),
            '10+ ans': queryset.filter(date_embauche__lt=now.replace(year=now.year-10)).count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def types_personnel(self, request):
        """Retourne la liste des types de personnel disponibles"""
        types = TypePersonnelSerializer.get_types_personnel()
        return Response(types)
    
    @action(detail=False, methods=['get'])
    def statuts_personnel(self, request):
        """Retourne la liste des statuts du personnel disponibles"""
        statuts = StatutPersonnelSerializer.get_statuts_personnel()
        return Response(statuts)
    
    @action(detail=False, methods=['get'])
    def embauches_recentes(self, request):
        """Retourne les embauches des 30 derniers jours"""
        date_limite = timezone.now().date() - timedelta(days=30)
        personnel = self.get_queryset().filter(date_embauche__gte=date_limite)
        serializer = PersonnelListSerializer(personnel, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def anciennete_elevee(self, request):
        """Retourne le personnel avec plus de 10 ans d'ancienneté"""
        date_limite = timezone.now().date().replace(year=timezone.now().year-10)
        personnel = self.get_queryset().filter(
            statut=StatutPersonnel.ACTIF,
            date_embauche__lte=date_limite
        )
        serializer = PersonnelListSerializer(personnel, many=True)
        return Response(serializer.data)


class FormationPersonnelViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des formations du personnel
    """
    queryset = FormationPersonnel.objects.all()
    serializer_class = FormationPersonnelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les formations selon le personnel"""
        queryset = FormationPersonnel.objects.all()
        
        personnel_id = self.request.query_params.get('personnel')
        if personnel_id:
            queryset = queryset.filter(personnel_id=personnel_id)
        
        return queryset.order_by('-date_fin')


class SanctionPersonnelViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des sanctions du personnel
    """
    queryset = SanctionPersonnel.objects.all()
    serializer_class = SanctionPersonnelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les sanctions selon le personnel"""
        queryset = SanctionPersonnel.objects.all()
        
        personnel_id = self.request.query_params.get('personnel')
        if personnel_id:
            queryset = queryset.filter(personnel_id=personnel_id)
        
        return queryset.order_by('-date_sanction')
    
    def perform_create(self, serializer):
        """Création d'une sanction avec l'utilisateur connecté"""
        serializer.save(sanctionne_par=self.request.user)