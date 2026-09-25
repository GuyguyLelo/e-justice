from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.comptes.models import Utilisateur
from apps.detenus.models import Detenu


class TypeVisiteur(models.TextChoices):
    """Types de visiteurs"""
    FAMILLE = 'FAMILLE', _('Famille')
    AVOCAT = 'AVOCAT', _('Avocat')
    AMI = 'AMI', _('Ami')
    REPRESENTANT_LEGAL = 'REPRESENTANT_LEGAL', _('Représentant légal')
    AUTRE = 'AUTRE', _('Autre')


class StatutVisite(models.TextChoices):
    """Statuts des visites"""
    PROGRAMMEE = 'PROGRAMMEE', _('Programmée')
    EN_COURS = 'EN_COURS', _('En cours')
    TERMINEE = 'TERMINEE', _('Terminée')
    ANNULEE = 'ANNULEE', _('Annulée')
    REFUSEE = 'REFUSEE', _('Refusée')


class Visiteur(models.Model):
    """
    Modèle pour les visiteurs
    """
    # Informations personnelles
    nom = models.CharField(
        max_length=100,
        verbose_name=_('Nom')
    )
    
    prenom = models.CharField(
        max_length=100,
        verbose_name=_('Prénom')
    )
    
    type_visiteur = models.CharField(
        max_length=30,
        choices=TypeVisiteur.choices,
        verbose_name=_('Type de visiteur')
    )
    
    piece_identite = models.CharField(
        max_length=50,
        verbose_name=_('Pièce d\'identité')
    )
    
    numero_piece = models.CharField(
        max_length=50,
        verbose_name=_('Numéro de pièce')
    )
    
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Téléphone')
    )
    
    adresse = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Adresse')
    )
    
    # Relation avec le détenu
    relation_detenu = models.CharField(
        max_length=100,
        verbose_name=_('Relation avec le détenu')
    )

    photo = models.ImageField(
        upload_to='visiteurs/photos/',
        blank=True,
        null=True,
        verbose_name=_('Photo'),
        help_text=_('Photo d\'identité du visiteur'),
    )
    
    # Informations professionnelles (pour avocats)
    cabinet_avocat = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Cabinet d\'avocat')
    )
    
    numero_ordre_avocat = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Numéro d\'ordre avocat')
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
        verbose_name = _('Visiteur')
        verbose_name_plural = _('Visiteurs')
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.get_type_visiteur_display()})"

    @property
    def nom_complet(self):
        """Retourne le nom complet du visiteur"""
        return f"{self.nom} {self.prenom}"

    def is_avocat(self):
        """Vérifie si le visiteur est un avocat"""
        return self.type_visiteur == TypeVisiteur.AVOCAT


class Visite(models.Model):
    """
    Modèle pour les visites
    """
    # Relations
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        related_name='visites',
        verbose_name=_('Détenu')
    )
    
    visiteur = models.ForeignKey(
        Visiteur,
        on_delete=models.CASCADE,
        related_name='visites',
        verbose_name=_('Visiteur')
    )
    
    # Informations de la visite
    date_visite = models.DateTimeField(
        verbose_name=_('Date de visite')
    )
    
    duree_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(180)],
        verbose_name=_('Durée en minutes')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutVisite.choices,
        default=StatutVisite.PROGRAMMEE,
        verbose_name=_('Statut')
    )
    
    motif_refus = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Motif de refus')
    )
    
    # Objets apportés
    objets_apportes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Objets apportés')
    )
    
    objets_autorises = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Objets autorisés')
    )
    
    objets_refuses = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Objets refusés')
    )
    
    # Contrôle
    agent_controle = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='visites_controlees',
        verbose_name=_('Agent de contrôle')
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
        related_name='visites_crees',
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
        verbose_name = _('Visite')
        verbose_name_plural = _('Visites')
        ordering = ['-date_visite']

    def __str__(self):
        return f"{self.visiteur.nom_complet} -> {self.detenu.nom_complet} ({self.date_visite.strftime('%d/%m/%Y %H:%M')})"

    def is_programmee(self):
        """Vérifie si la visite est programmée"""
        return self.statut == StatutVisite.PROGRAMMEE

    def is_en_cours(self):
        """Vérifie si la visite est en cours"""
        return self.statut == StatutVisite.EN_COURS

    def is_terminee(self):
        """Vérifie si la visite est terminée"""
        return self.statut == StatutVisite.TERMINEE

    def is_annulee(self):
        """Vérifie si la visite est annulée"""
        return self.statut == StatutVisite.ANNULEE

    def is_refusee(self):
        """Vérifie si la visite est refusée"""
        return self.statut == StatutVisite.REFUSEE


class ObjetVisite(models.Model):
    """
    Objets apportés lors des visites
    """
    visite = models.ForeignKey(
        Visite,
        on_delete=models.CASCADE,
        related_name='objets',
        verbose_name=_('Visite')
    )
    
    nom_objet = models.CharField(
        max_length=200,
        verbose_name=_('Nom de l\'objet')
    )
    
    quantite = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Quantité')
    )
    
    autorise = models.BooleanField(
        default=False,
        verbose_name=_('Autorisé')
    )
    
    motif_refus = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Motif de refus')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Objet visite')
        verbose_name_plural = _('Objets visite')
        ordering = ['nom_objet']

    def __str__(self):
        return f"{self.nom_objet} ({self.quantite}) - {'Autorisé' if self.autorise else 'Refusé'}"