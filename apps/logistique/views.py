from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Fournisseur, Produit, Commande, LigneCommande, MouvementStock,
    TypeProduit, StatutCommande, UniteMesure
)
from .serializers import (
    FournisseurSerializer, FournisseurListSerializer, ProduitSerializer, ProduitListSerializer,
    CommandeSerializer, CommandeListSerializer, CommandeCreateSerializer, LigneCommandeSerializer,
    MouvementStockSerializer, MouvementStockCreateSerializer, CommandeStatsSerializer,
    StockStatsSerializer, TypeProduitSerializer, StatutCommandeSerializer, UniteMesureSerializer
)


class FournisseurViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des fournisseurs"""
    queryset = Fournisseur.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return FournisseurListSerializer
        return FournisseurSerializer
    
    def get_queryset(self):
        queryset = Fournisseur.objects.all()
        
        est_actif = self.request.query_params.get('est_actif')
        if est_actif is not None:
            queryset = queryset.filter(est_actif=est_actif.lower() == 'true')
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(specialite__icontains=search)
            )
        
        return queryset.order_by('nom')


class ProduitViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des produits"""
    queryset = Produit.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProduitListSerializer
        return ProduitSerializer
    
    def get_queryset(self):
        queryset = Produit.objects.all()
        
        type_produit = self.request.query_params.get('type_produit')
        if type_produit:
            queryset = queryset.filter(type_produit=type_produit)
        
        stock_faible = self.request.query_params.get('stock_faible')
        if stock_faible == 'true':
            queryset = queryset.filter(stock_actuel__lte=F('stock_minimum'))
        
        expire = self.request.query_params.get('expire')
        if expire == 'true':
            from datetime import date
            queryset = queryset.filter(date_expiration__lt=date.today())
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('nom')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        
        valeur_stock = queryset.aggregate(
            total=Sum(F('stock_actuel') * F('prix_unitaire'))
        )['total'] or 0
        
        stats = {
            'total_produits': queryset.count(),
            'stock_faible': queryset.filter(stock_actuel__lte=F('stock_minimum')).count(),
            'stock_plein': queryset.filter(stock_actuel__gte=F('stock_maximum')).count(),
            'expires': queryset.filter(date_expiration__lt=timezone.now().date()).count(),
            'valeur_stock': valeur_stock,
        }
        
        stats['par_type'] = {}
        for type_value, type_label in TypeProduit.choices:
            stats['par_type'][type_label] = queryset.filter(type_produit=type_value).count()
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def types_produit(self, request):
        types = TypeProduitSerializer.get_types_produit()
        return Response(types)
    
    @action(detail=False, methods=['get'])
    def stock_faible(self, request):
        produits = self.get_queryset().filter(stock_actuel__lte=F('stock_minimum'))
        serializer = ProduitListSerializer(produits, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expires(self, request):
        produits = self.get_queryset().filter(date_expiration__lt=timezone.now().date())
        serializer = ProduitListSerializer(produits, many=True)
        return Response(serializer.data)


class CommandeViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des commandes"""
    queryset = Commande.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CommandeListSerializer
        elif self.action == 'create':
            return CommandeCreateSerializer
        return CommandeSerializer
    
    def get_queryset(self):
        queryset = Commande.objects.all()
        
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        fournisseur_id = self.request.query_params.get('fournisseur')
        if fournisseur_id:
            queryset = queryset.filter(fournisseur_id=fournisseur_id)
        
        date_debut = self.request.query_params.get('date_debut')
        if date_debut:
            queryset = queryset.filter(date_commande__gte=date_debut)
        
        date_fin = self.request.query_params.get('date_fin')
        if date_fin:
            queryset = queryset.filter(date_commande__lte=date_fin)
        
        return queryset.order_by('-date_commande')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        commande = self.get_object()
        if commande.statut != StatutCommande.EN_ATTENTE:
            return Response(
                {'error': 'Cette commande ne peut pas être validée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        commande.statut = StatutCommande.VALIDEE
        commande.save()
        
        return Response({'message': 'Commande validée avec succès.'})
    
    @action(detail=True, methods=['post'])
    def livrer(self, request, pk=None):
        commande = self.get_object()
        if commande.statut != StatutCommande.EN_COURS:
            return Response(
                {'error': 'Cette commande n\'est pas en cours.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        commande.statut = StatutCommande.LIVREE
        commande.date_livraison_effective = timezone.now().date()
        commande.save()
        
        # Mettre à jour les stocks
        for ligne in commande.lignes.all():
            mouvement = MouvementStock.objects.create(
                produit=ligne.produit,
                type_mouvement='ENTREE',
                quantite=ligne.quantite_livree,
                motif=f'Livraison commande {commande.numero_commande}',
                reference=commande.numero_commande,
                created_by=request.user
            )
        
        return Response({'message': 'Commande livrée avec succès.'})
    
    @action(detail=True, methods=['post'])
    def annuler(self, request, pk=None):
        commande = self.get_object()
        if commande.statut in [StatutCommande.LIVREE, StatutCommande.ANNULEE]:
            return Response(
                {'error': 'Cette commande ne peut pas être annulée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        commande.statut = StatutCommande.ANNULEE
        commande.save()
        
        return Response({'message': 'Commande annulée avec succès.'})
    
    @action(detail=True, methods=['get'])
    def lignes(self, request, pk=None):
        commande = self.get_object()
        lignes = commande.lignes.all()
        serializer = LigneCommandeSerializer(lignes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.get_queryset()
        
        montant_total = queryset.aggregate(total=Sum('montant_total'))['total'] or 0
        
        stats = {
            'total': queryset.count(),
            'en_attente': queryset.filter(statut=StatutCommande.EN_ATTENTE).count(),
            'validees': queryset.filter(statut=StatutCommande.VALIDEE).count(),
            'en_cours': queryset.filter(statut=StatutCommande.EN_COURS).count(),
            'livrees': queryset.filter(statut=StatutCommande.LIVREE).count(),
            'annulees': queryset.filter(statut=StatutCommande.ANNULEE).count(),
            'montant_total': montant_total,
        }
        
        stats['par_fournisseur'] = {}
        fournisseurs = queryset.values('fournisseur__nom').annotate(count=Count('id'))
        for fournisseur in fournisseurs:
            if fournisseur['fournisseur__nom']:
                stats['par_fournisseur'][fournisseur['fournisseur__nom']] = fournisseur['count']
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def statuts_commande(self, request):
        statuts = StatutCommandeSerializer.get_statuts_commande()
        return Response(statuts)


class MouvementStockViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des mouvements de stock"""
    queryset = MouvementStock.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MouvementStockCreateSerializer
        return MouvementStockSerializer
    
    def get_queryset(self):
        queryset = MouvementStock.objects.all()
        
        produit_id = self.request.query_params.get('produit')
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        
        type_mouvement = self.request.query_params.get('type_mouvement')
        if type_mouvement:
            queryset = queryset.filter(type_mouvement=type_mouvement)
        
        date_debut = self.request.query_params.get('date_debut')
        if date_debut:
            queryset = queryset.filter(created_at__date__gte=date_debut)
        
        date_fin = self.request.query_params.get('date_fin')
        if date_fin:
            queryset = queryset.filter(created_at__date__lte=date_fin)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def types_mouvement(self, request):
        types = [
            {'value': 'ENTREE', 'label': 'Entrée'},
            {'value': 'SORTIE', 'label': 'Sortie'},
            {'value': 'AJUSTEMENT', 'label': 'Ajustement'},
            {'value': 'PERTE', 'label': 'Perte'},
        ]
        return Response(types)
    
    @action(detail=False, methods=['get'])
    def unites_mesure(self, request):
        unites = UniteMesureSerializer.get_unites_mesure()
        return Response(unites)