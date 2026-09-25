from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Rapport, ModeleRapport, TableauBord, TypeRapport, StatutRapport
from .serializers import (
    RapportSerializer, RapportListSerializer, RapportCreateSerializer,
    ModeleRapportSerializer, ModeleRapportListSerializer, TableauBordSerializer,
    TableauBordListSerializer, RapportStatsSerializer, TypeRapportSerializer,
    StatutRapportSerializer, RapportGenerationSerializer
)


class RapportViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des rapports"""
    queryset = Rapport.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RapportListSerializer
        elif self.action == 'create':
            return RapportCreateSerializer
        return RapportSerializer
    
    def get_queryset(self):
        queryset = Rapport.objects.all()
        
        type_rapport = self.request.query_params.get('type_rapport')
        if type_rapport:
            queryset = queryset.filter(type_rapport=type_rapport)
        
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        date_debut = self.request.query_params.get('date_debut')
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
        
        date_fin = self.request.query_params.get('date_fin')
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generer(self, request, pk=None):
        rapport = self.get_object()
        if rapport.statut != StatutRapport.EN_COURS:
            return Response(
                {'error': 'Ce rapport ne peut pas être généré.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simulation de génération de rapport
        rapport.statut = StatutRapport.TERMINE
        rapport.fichier = 'rapports/rapport_' + str(rapport.id) + '.pdf'
        rapport.taille_fichier = 1024 * 1024  # 1MB
        rapport.save()
        
        return Response({'message': 'Rapport généré avec succès.'})
    
    @action(detail=True, methods=['post'])
    def telecharger(self, request, pk=None):
        rapport = self.get_object()
        if rapport.statut != StatutRapport.TERMINE:
            return Response(
                {'error': 'Ce rapport n\'est pas encore prêt.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Simulation de téléchargement
        return Response({'message': 'Téléchargement du rapport...'})
    
    @action(detail=False, methods=['post'])
    def generer_rapport(self, request):
        serializer = RapportGenerationSerializer(data=request.data)
        if serializer.is_valid():
            # Créer un nouveau rapport
            rapport = Rapport.objects.create(
                nom=f"Rapport {serializer.validated_data['type_rapport']}",
                type_rapport=serializer.validated_data['type_rapport'],
                date_debut=serializer.validated_data.get('date_debut'),
                date_fin=serializer.validated_data.get('date_fin'),
                parametres=serializer.validated_data.get('parametres', {}),
                statut=StatutRapport.EN_COURS,
                created_by=request.user
            )
            
            # Démarrer la génération en arrière-plan
            # Ici, vous pourriez utiliser Celery ou une tâche asynchrone
            
            return Response({
                'message': 'Génération du rapport démarrée.',
                'rapport_id': rapport.id
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        
        taille_totale = queryset.aggregate(total=Sum('taille_fichier'))['total'] or 0
        
        stats = {
            'total': queryset.count(),
            'en_cours': queryset.filter(statut=StatutRapport.EN_COURS).count(),
            'termines': queryset.filter(statut=StatutRapport.TERMINE).count(),
            'erreurs': queryset.filter(statut=StatutRapport.ERREUR).count(),
            'taille_totale_mb': round(taille_totale / (1024 * 1024), 2),
        }
        
        stats['par_type'] = {}
        for type_value, type_label in TypeRapport.choices:
            stats['par_type'][type_label] = queryset.filter(type_rapport=type_value).count()
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def types_rapport(self, request):
        types = TypeRapportSerializer.get_types_rapport()
        return Response(types)
    
    @action(detail=False, methods=['get'])
    def statuts_rapport(self, request):
        statuts = StatutRapportSerializer.get_statuts_rapport()
        return Response(statuts)
    
    @action(detail=False, methods=['get'])
    def mes_rapports(self, request):
        rapports = self.get_queryset().filter(created_by=request.user)
        serializer = RapportListSerializer(rapports, many=True)
        return Response(serializer.data)


class ModeleRapportViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des modèles de rapports"""
    queryset = ModeleRapport.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ModeleRapportListSerializer
        return ModeleRapportSerializer
    
    def get_queryset(self):
        queryset = ModeleRapport.objects.all()
        
        type_rapport = self.request.query_params.get('type_rapport')
        if type_rapport:
            queryset = queryset.filter(type_rapport=type_rapport)
        
        est_actif = self.request.query_params.get('est_actif')
        if est_actif is not None:
            queryset = queryset.filter(est_actif=est_actif.lower() == 'true')
        
        return queryset.order_by('nom')
    
    @action(detail=True, methods=['post'])
    def utiliser(self, request, pk=None):
        modele = self.get_object()
        
        # Créer un rapport basé sur le modèle
        rapport = Rapport.objects.create(
            nom=f"Rapport basé sur {modele.nom}",
            type_rapport=modele.type_rapport,
            description=modele.description,
            parametres=modele.parametres_defaut,
            statut=StatutRapport.EN_COURS,
            created_by=request.user
        )
        
        return Response({
            'message': 'Rapport créé à partir du modèle.',
            'rapport_id': rapport.id
        }, status=status.HTTP_201_CREATED)


class TableauBordViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des tableaux de bord"""
    queryset = TableauBord.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TableauBordListSerializer
        return TableauBordSerializer
    
    def get_queryset(self):
        queryset = TableauBord.objects.all()
        
        est_public = self.request.query_params.get('est_public')
        if est_public is not None:
            queryset = queryset.filter(est_public=est_public.lower() == 'true')
        
        # Les utilisateurs ne voient que leurs tableaux de bord ou les publics
        if not self.request.user.is_admin():
            queryset = queryset.filter(
                Q(created_by=self.request.user) | Q(est_public=True)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def partager(self, request, pk=None):
        tableau_bord = self.get_object()
        tableau_bord.est_public = True
        tableau_bord.save()
        
        return Response({'message': 'Tableau de bord partagé avec succès.'})
    
    @action(detail=True, methods=['post'])
    def priver(self, request, pk=None):
        tableau_bord = self.get_object()
        tableau_bord.est_public = False
        tableau_bord.save()
        
        return Response({'message': 'Tableau de bord rendu privé avec succès.'})
    
    @action(detail=False, methods=['get'])
    def publics(self, request):
        tableaux = self.get_queryset().filter(est_public=True)
        serializer = TableauBordListSerializer(tableaux, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def mes_tableaux(self, request):
        tableaux = self.get_queryset().filter(created_by=request.user)
        serializer = TableauBordListSerializer(tableaux, many=True)
        return Response(serializer.data)