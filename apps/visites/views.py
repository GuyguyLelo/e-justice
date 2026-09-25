from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Visiteur, Visite, ObjetVisite, TypeVisiteur, StatutVisite
from .serializers import (
    VisiteurSerializer, VisiteurListSerializer, VisiteSerializer, VisiteListSerializer,
    VisiteDetailSerializer, VisiteCreateSerializer, VisiteUpdateSerializer, VisiteStatsSerializer,
    TypeVisiteurSerializer, StatutVisiteSerializer
)


class VisiteurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des visiteurs
    """
    queryset = Visiteur.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return VisiteurListSerializer
        return VisiteurSerializer
    
    def get_queryset(self):
        """Filtre les visiteurs selon les paramètres"""
        queryset = Visiteur.objects.all()
        
        # Filtres par paramètres de requête
        type_visiteur = self.request.query_params.get('type_visiteur')
        if type_visiteur:
            queryset = queryset.filter(type_visiteur=type_visiteur)
        
        # Recherche par nom
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def types_visiteur(self, request):
        """Retourne la liste des types de visiteurs disponibles"""
        types = TypeVisiteurSerializer.get_types_visiteur()
        return Response(types)


class VisiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour la gestion des visites
    """
    queryset = Visite.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action"""
        if self.action == 'list':
            return VisiteListSerializer
        elif self.action == 'retrieve':
            return VisiteDetailSerializer
        elif self.action == 'create':
            return VisiteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VisiteUpdateSerializer
        return VisiteSerializer
    
    def get_queryset(self):
        """Filtre les visites selon les paramètres"""
        queryset = Visite.objects.all()
        
        # Filtres par paramètres de requête
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        detenu_id = self.request.query_params.get('detenu')
        if detenu_id:
            queryset = queryset.filter(detenu_id=detenu_id)
        
        visiteur_id = self.request.query_params.get('visiteur')
        if visiteur_id:
            queryset = queryset.filter(visiteur_id=visiteur_id)
        
        # Filtre par date
        date_debut = self.request.query_params.get('date_debut')
        if date_debut:
            queryset = queryset.filter(date_visite__date__gte=date_debut)
        
        date_fin = self.request.query_params.get('date_fin')
        if date_fin:
            queryset = queryset.filter(date_visite__date__lte=date_fin)
        
        return queryset.order_by('-date_visite')
    
    def perform_create(self, serializer):
        """Création d'une visite avec l'utilisateur connecté"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def commencer(self, request, pk=None):
        """Commence une visite"""
        visite = self.get_object()
        if visite.statut != StatutVisite.PROGRAMMEE:
            return Response(
                {'error': 'Cette visite ne peut pas être commencée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visite.statut = StatutVisite.EN_COURS
        visite.agent_controle = request.user
        visite.save()
        
        return Response({'message': 'Visite commencée avec succès.'})
    
    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        """Termine une visite"""
        visite = self.get_object()
        if visite.statut != StatutVisite.EN_COURS:
            return Response(
                {'error': 'Cette visite n\'est pas en cours.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visite.statut = StatutVisite.TERMINEE
        visite.observations = request.data.get('observations', '')
        visite.save()
        
        return Response({'message': 'Visite terminée avec succès.'})
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        """Annule une visite"""
        visite = self.get_object()
        if visite.statut in [StatutVisite.TERMINEE, StatutVisite.ANNULEE]:
            return Response(
                {'error': 'Cette visite ne peut pas être annulée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visite.statut = StatutVisite.ANNULEE
        visite.motif_refus = request.data.get('motif', '')
        visite.save()
        
        return Response({'message': 'Visite annulée avec succès.'})
    
    @action(detail=True, methods=['post'])
    def refuser(self, request, pk=None):
        """Refuse une visite"""
        visite = self.get_object()
        if visite.statut not in [StatutVisite.PROGRAMMEE, StatutVisite.EN_COURS]:
            return Response(
                {'error': 'Cette visite ne peut pas être refusée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        visite.statut = StatutVisite.REFUSEE
        visite.motif_refus = request.data.get('motif', '')
        visite.agent_controle = request.user
        visite.save()
        
        return Response({'message': 'Visite refusée avec succès.'})
    
    @action(detail=True, methods=['get'])
    def objets(self, request, pk=None):
        """Retourne les objets d'une visite"""
        visite = self.get_object()
        objets = visite.objets.all()
        from .serializers import ObjetVisiteSerializer
        serializer = ObjetVisiteSerializer(objets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def autoriser_objets(self, request, pk=None):
        """Autorise ou refuse les objets d'une visite"""
        visite = self.get_object()
        objets_data = request.data.get('objets', [])
        
        for objet_data in objets_data:
            objet_id = objet_data.get('id')
            autorise = objet_data.get('autorise', False)
            motif_refus = objet_data.get('motif_refus', '')
            
            try:
                objet = visite.objets.get(id=objet_id)
                objet.autorise = autorise
                if not autorise:
                    objet.motif_refus = motif_refus
                objet.save()
            except ObjetVisite.DoesNotExist:
                continue
        
        return Response({'message': 'Objets mis à jour avec succès.'})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retourne les statistiques des visites"""
        queryset = self.get_queryset()
        
        # Statistiques générales
        stats = {
            'total': queryset.count(),
            'programmees': queryset.filter(statut=StatutVisite.PROGRAMMEE).count(),
            'en_cours': queryset.filter(statut=StatutVisite.EN_COURS).count(),
            'terminees': queryset.filter(statut=StatutVisite.TERMINEE).count(),
            'annulees': queryset.filter(statut=StatutVisite.ANNULEE).count(),
            'refusees': queryset.filter(statut=StatutVisite.REFUSEE).count(),
        }
        
        # Statistiques par type de visiteur
        stats['par_type_visiteur'] = {}
        for type_value, type_label in TypeVisiteur.choices:
            count = queryset.filter(visiteur__type_visiteur=type_value).count()
            stats['par_type_visiteur'][type_label] = count
        
        # Statistiques par jour (7 derniers jours)
        stats['par_jour'] = {}
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            count = queryset.filter(date_visite__date=date).count()
            stats['par_jour'][date.strftime('%Y-%m-%d')] = count
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def statuts_visite(self, request):
        """Retourne la liste des statuts de visite disponibles"""
        statuts = StatutVisiteSerializer.get_statuts_visite()
        return Response(statuts)
    
    @action(detail=False, methods=['get'])
    def aujourd_hui(self, request):
        """Retourne les visites du jour"""
        aujourd_hui = timezone.now().date()
        visites = self.get_queryset().filter(date_visite__date=aujourd_hui)
        serializer = VisiteListSerializer(visites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def cette_semaine(self, request):
        """Retourne les visites de la semaine"""
        debut_semaine = timezone.now().date() - timedelta(days=7)
        visites = self.get_queryset().filter(date_visite__date__gte=debut_semaine)
        serializer = VisiteListSerializer(visites, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def en_attente(self, request):
        """Retourne les visites en attente de validation"""
        visites = self.get_queryset().filter(statut=StatutVisite.PROGRAMMEE)
        serializer = VisiteListSerializer(visites, many=True)
        return Response(serializer.data)