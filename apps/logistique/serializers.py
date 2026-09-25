from rest_framework import serializers
from apps.comptes.serializers import UtilisateurListSerializer
from .models import (
    Fournisseur, Produit, Commande, LigneCommande, MouvementStock,
    TypeProduit, StatutCommande, UniteMesure
)


class FournisseurSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Fournisseur"""
    
    class Meta:
        model = Fournisseur
        fields = [
            'id', 'nom', 'adresse', 'telephone', 'email', 'contact_principal',
            'specialite', 'est_actif', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FournisseurListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des fournisseurs"""
    
    class Meta:
        model = Fournisseur
        fields = [
            'id', 'nom', 'telephone', 'email', 'specialite', 'est_actif', 'created_at'
        ]


class ProduitSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Produit"""
    
    type_produit_display = serializers.CharField(source='get_type_produit_display', read_only=True)
    unite_mesure_display = serializers.CharField(source='get_unite_mesure_display', read_only=True)
    stock_faible = serializers.BooleanField(source='is_stock_faible', read_only=True)
    stock_plein = serializers.BooleanField(source='is_stock_plein', read_only=True)
    expire = serializers.BooleanField(source='is_expire', read_only=True)
    fournisseur_nom = serializers.CharField(source='fournisseur_principal.nom', read_only=True)
    
    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'description', 'type_produit', 'type_produit_display',
            'unite_mesure', 'unite_mesure_display', 'stock_actuel', 'stock_minimum',
            'stock_maximum', 'prix_unitaire', 'date_expiration', 'fournisseur_principal',
            'fournisseur_nom', 'stock_faible', 'stock_plein', 'expire',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_stock_actuel(self, value):
        """Validation du stock actuel"""
        if value < 0:
            raise serializers.ValidationError("Le stock ne peut pas être négatif.")
        return value
    
    def validate_stock_minimum(self, value):
        """Validation du stock minimum"""
        if hasattr(self, 'initial_data'):
            stock_maximum = self.initial_data.get('stock_maximum')
            if stock_maximum and value > stock_maximum:
                raise serializers.ValidationError(
                    "Le stock minimum ne peut pas être supérieur au stock maximum."
                )
        return value


class ProduitListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des produits"""
    
    type_produit_display = serializers.CharField(source='get_type_produit_display', read_only=True)
    stock_faible = serializers.BooleanField(source='is_stock_faible', read_only=True)
    
    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'type_produit', 'type_produit_display', 'stock_actuel',
            'stock_minimum', 'stock_faible', 'prix_unitaire', 'created_at'
        ]


class LigneCommandeSerializer(serializers.ModelSerializer):
    """Serializer pour les lignes de commande"""
    
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_unite = serializers.CharField(source='produit.get_unite_mesure_display', read_only=True)
    
    class Meta:
        model = LigneCommande
        fields = [
            'id', 'produit', 'produit_nom', 'produit_unite', 'quantite_commandee',
            'quantite_livree', 'prix_unitaire', 'montant_ligne'
        ]
        read_only_fields = ['id', 'montant_ligne']


class CommandeSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Commande"""
    
    fournisseur_info = FournisseurListSerializer(source='fournisseur', read_only=True)
    created_by_info = UtilisateurListSerializer(source='created_by', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    lignes = LigneCommandeSerializer(many=True, read_only=True)
    
    class Meta:
        model = Commande
        fields = [
            'id', 'numero_commande', 'fournisseur', 'fournisseur_info', 'statut',
            'statut_display', 'date_commande', 'date_livraison_prevue',
            'date_livraison_effective', 'montant_total', 'observations',
            'created_by', 'created_by_info', 'lignes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommandeListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour la liste des commandes"""
    
    fournisseur_nom = serializers.CharField(source='fournisseur.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    created_by_nom = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Commande
        fields = [
            'id', 'numero_commande', 'fournisseur_nom', 'statut', 'statut_display',
            'date_commande', 'montant_total', 'created_by_nom', 'created_at'
        ]


class CommandeCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une commande"""
    
    lignes = LigneCommandeSerializer(many=True)
    
    class Meta:
        model = Commande
        fields = [
            'fournisseur', 'date_commande', 'date_livraison_prevue',
            'observations', 'lignes'
        ]
    
    def create(self, validated_data):
        """Création d'une commande avec lignes"""
        lignes_data = validated_data.pop('lignes', [])
        commande = Commande.objects.create(**validated_data)
        
        montant_total = 0
        for ligne_data in lignes_data:
            ligne = LigneCommande.objects.create(commande=commande, **ligne_data)
            montant_total += ligne.montant_ligne
        
        commande.montant_total = montant_total
        commande.save()
        
        return commande


class MouvementStockSerializer(serializers.ModelSerializer):
    """Serializer pour les mouvements de stock"""
    
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    created_by_nom = serializers.CharField(source='created_by.get_full_name', read_only=True)
    type_mouvement_display = serializers.CharField(source='get_type_mouvement_display', read_only=True)
    
    class Meta:
        model = MouvementStock
        fields = [
            'id', 'produit', 'produit_nom', 'type_mouvement', 'type_mouvement_display',
            'quantite', 'motif', 'reference', 'created_by', 'created_by_nom',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MouvementStockCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer un mouvement de stock"""
    
    class Meta:
        model = MouvementStock
        fields = [
            'produit', 'type_mouvement', 'quantite', 'motif', 'reference'
        ]
    
    def validate_quantite(self, value):
        """Validation de la quantité"""
        if value <= 0:
            raise serializers.ValidationError("La quantité doit être positive.")
        return value


class CommandeStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques des commandes"""
    
    total = serializers.IntegerField()
    en_attente = serializers.IntegerField()
    validees = serializers.IntegerField()
    en_cours = serializers.IntegerField()
    livrees = serializers.IntegerField()
    annulees = serializers.IntegerField()
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    par_fournisseur = serializers.DictField()


class StockStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques du stock"""
    
    total_produits = serializers.IntegerField()
    stock_faible = serializers.IntegerField()
    stock_plein = serializers.IntegerField()
    expires = serializers.IntegerField()
    valeur_stock = serializers.DecimalField(max_digits=12, decimal_places=2)
    par_type = serializers.DictField()


class TypeProduitSerializer(serializers.Serializer):
    """Serializer pour les types de produits"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_types_produit(cls):
        """Retourne tous les types de produits disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in TypeProduit.choices]


class StatutCommandeSerializer(serializers.Serializer):
    """Serializer pour les statuts des commandes"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_statuts_commande(cls):
        """Retourne tous les statuts de commande disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in StatutCommande.choices]


class UniteMesureSerializer(serializers.Serializer):
    """Serializer pour les unités de mesure"""
    
    value = serializers.CharField()
    label = serializers.CharField()
    
    @classmethod
    def get_unites_mesure(cls):
        """Retourne toutes les unités de mesure disponibles"""
        return [{'value': choice[0], 'label': choice[1]} for choice in UniteMesure.choices]






