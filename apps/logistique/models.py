from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.comptes.models import Utilisateur


class TypeProduit(models.TextChoices):
    """Types de produits"""
    NOURRITURE = 'NOURRITURE', _('Nourriture')
    MEDICAMENT = 'MEDICAMENT', _('Médicament')
    VETEMENT = 'VETEMENT', _('Vêtement')
    LINGE = 'LINGE', _('Linge')
    MATERIEL_ENTRETIEN = 'MATERIEL_ENTRETIEN', _('Matériel d\'entretien')
    MATERIEL_BUREAU = 'MATERIEL_BUREAU', _('Matériel de bureau')
    SECURITE = 'SECURITE', _('Sécurité')
    AUTRE = 'AUTRE', _('Autre')


class StatutCommande(models.TextChoices):
    """Statuts des commandes"""
    EN_ATTENTE = 'EN_ATTENTE', _('En attente')
    VALIDEE = 'VALIDEE', _('Validée')
    EN_COURS = 'EN_COURS', _('En cours')
    LIVREE = 'LIVREE', _('Livrée')
    ANNULEE = 'ANNULEE', _('Annulée')


class UniteMesure(models.TextChoices):
    """Unités de mesure"""
    KILOGRAMME = 'KG', _('Kilogramme')
    GRAMME = 'G', _('Gramme')
    LITRE = 'L', _('Litre')
    MILLILITRE = 'ML', _('Millilitre')
    UNITE = 'UNITE', _('Unité')
    PAQUET = 'PAQUET', _('Paquet')
    CARTON = 'CARTON', _('Carton')
    METRE = 'M', _('Mètre')
    METRE_CARRE = 'M2', _('Mètre carré')


class Fournisseur(models.Model):
    """
    Modèle pour les fournisseurs
    """
    nom = models.CharField(
        max_length=200,
        verbose_name=_('Nom du fournisseur')
    )
    
    adresse = models.TextField(
        verbose_name=_('Adresse')
    )
    
    telephone = models.CharField(
        max_length=20,
        verbose_name=_('Téléphone')
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email')
    )
    
    contact_principal = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Contact principal')
    )
    
    specialite = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Spécialité')
    )
    
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_('Est actif')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de modification')
    )

    class Meta:
        verbose_name = _('Fournisseur')
        verbose_name_plural = _('Fournisseurs')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Produit(models.Model):
    """
    Modèle pour les produits
    """
    nom = models.CharField(
        max_length=200,
        verbose_name=_('Nom du produit')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    
    type_produit = models.CharField(
        max_length=30,
        choices=TypeProduit.choices,
        verbose_name=_('Type de produit')
    )
    
    unite_mesure = models.CharField(
        max_length=10,
        choices=UniteMesure.choices,
        verbose_name=_('Unité de mesure')
    )
    
    stock_actuel = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Stock actuel')
    )
    
    stock_minimum = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Stock minimum')
    )
    
    stock_maximum = models.PositiveIntegerField(
        default=1000,
        verbose_name=_('Stock maximum')
    )
    
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Prix unitaire')
    )
    
    date_expiration = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date d\'expiration')
    )
    
    fournisseur_principal = models.ForeignKey(
        Fournisseur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='produits',
        verbose_name=_('Fournisseur principal')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de modification')
    )

    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.get_unite_mesure_display()})"

    def is_stock_faible(self):
        """Vérifie si le stock est faible"""
        return self.stock_actuel <= self.stock_minimum

    def is_stock_plein(self):
        """Vérifie si le stock est plein"""
        return self.stock_actuel >= self.stock_maximum

    def is_expire(self):
        """Vérifie si le produit est expiré"""
        from datetime import date
        return self.date_expiration and self.date_expiration < date.today()


class Commande(models.Model):
    """
    Modèle pour les commandes
    """
    numero_commande = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Numéro de commande')
    )
    
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.CASCADE,
        related_name='commandes',
        verbose_name=_('Fournisseur')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutCommande.choices,
        default=StatutCommande.EN_ATTENTE,
        verbose_name=_('Statut')
    )
    
    date_commande = models.DateField(
        verbose_name=_('Date de commande')
    )
    
    date_livraison_prevue = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de livraison prévue')
    )
    
    date_livraison_effective = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de livraison effective')
    )
    
    montant_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Montant total')
    )
    
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observations')
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='commandes_crees',
        verbose_name=_('Créé par')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de modification')
    )

    class Meta:
        verbose_name = _('Commande')
        verbose_name_plural = _('Commandes')
        ordering = ['-date_commande']

    def __str__(self):
        return f"Commande {self.numero_commande} - {self.fournisseur.nom}"

    def is_en_attente(self):
        """Vérifie si la commande est en attente"""
        return self.statut == StatutCommande.EN_ATTENTE

    def is_validee(self):
        """Vérifie si la commande est validée"""
        return self.statut == StatutCommande.VALIDEE

    def is_livree(self):
        """Vérifie si la commande est livrée"""
        return self.statut == StatutCommande.LIVREE


class LigneCommande(models.Model):
    """
    Modèle pour les lignes de commande
    """
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name=_('Commande')
    )
    
    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name='lignes_commande',
        verbose_name=_('Produit')
    )
    
    quantite_commandee = models.PositiveIntegerField(
        verbose_name=_('Quantité commandée')
    )
    
    quantite_livree = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Quantité livrée')
    )
    
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Prix unitaire')
    )
    
    montant_ligne = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Montant de la ligne')
    )

    class Meta:
        verbose_name = _('Ligne de commande')
        verbose_name_plural = _('Lignes de commande')
        ordering = ['produit__nom']

    def __str__(self):
        return f"{self.produit.nom} - {self.quantite_commandee} {self.produit.get_unite_mesure_display()}"

    def save(self, *args, **kwargs):
        """Calcule automatiquement le montant de la ligne"""
        self.montant_ligne = self.quantite_commandee * self.prix_unitaire
        super().save(*args, **kwargs)


class MouvementStock(models.Model):
    """
    Modèle pour les mouvements de stock
    """
    TYPE_MOUVEMENT_CHOICES = [
        ('ENTREE', _('Entrée')),
        ('SORTIE', _('Sortie')),
        ('AJUSTEMENT', _('Ajustement')),
        ('PERTE', _('Perte')),
    ]

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name='mouvements',
        verbose_name=_('Produit')
    )
    
    type_mouvement = models.CharField(
        max_length=20,
        choices=TYPE_MOUVEMENT_CHOICES,
        verbose_name=_('Type de mouvement')
    )
    
    quantite = models.PositiveIntegerField(
        verbose_name=_('Quantité')
    )
    
    motif = models.CharField(
        max_length=200,
        verbose_name=_('Motif')
    )
    
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Référence')
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mouvements_stock',
        verbose_name=_('Créé par')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Mouvement de stock')
        verbose_name_plural = _('Mouvements de stock')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.produit.nom} - {self.get_type_mouvement_display()} ({self.quantite})"

    def save(self, *args, **kwargs):
        """Met à jour le stock du produit"""
        super().save(*args, **kwargs)
        
        # Mise à jour du stock
        if self.type_mouvement == 'ENTREE':
            self.produit.stock_actuel += self.quantite
        elif self.type_mouvement in ['SORTIE', 'PERTE']:
            self.produit.stock_actuel -= self.quantite
        
        self.produit.save(update_fields=['stock_actuel'])