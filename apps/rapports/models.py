from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.comptes.models import Utilisateur


class TypeRapport(models.TextChoices):
    """Types de rapports"""
    STATISTIQUES = 'STATISTIQUES', _('Statistiques')
    DETENUS = 'DETENUS', _('Détenus')
    PERSONNEL = 'PERSONNEL', _('Personnel')
    VISITES = 'VISITES', _('Visites')
    SOINS = 'SOINS', _('Soins médicaux')
    LOGISTIQUE = 'LOGISTIQUE', _('Logistique')
    SECURITE = 'SECURITE', _('Sécurité')
    FINANCIER = 'FINANCIER', _('Financier')


class StatutRapport(models.TextChoices):
    """Statuts des rapports"""
    EN_COURS = 'EN_COURS', _('En cours')
    TERMINE = 'TERMINE', _('Terminé')
    ERREUR = 'ERREUR', _('Erreur')


class Rapport(models.Model):
    """
    Modèle pour les rapports générés
    """
    nom = models.CharField(
        max_length=200,
        verbose_name=_('Nom du rapport')
    )
    
    type_rapport = models.CharField(
        max_length=20,
        choices=TypeRapport.choices,
        verbose_name=_('Type de rapport')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutRapport.choices,
        default=StatutRapport.EN_COURS,
        verbose_name=_('Statut')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    
    # Paramètres du rapport
    date_debut = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de début')
    )
    
    date_fin = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de fin')
    )
    
    parametres = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Paramètres')
    )
    
    # Fichier généré
    fichier = models.FileField(
        upload_to='rapports/',
        blank=True,
        null=True,
        verbose_name=_('Fichier')
    )
    
    taille_fichier = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Taille du fichier (bytes)')
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='rapports_crees',
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
        verbose_name = _('Rapport')
        verbose_name_plural = _('Rapports')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nom} ({self.get_type_rapport_display()})"

    def is_en_cours(self):
        """Vérifie si le rapport est en cours de génération"""
        return self.statut == StatutRapport.EN_COURS

    def is_termine(self):
        """Vérifie si le rapport est terminé"""
        return self.statut == StatutRapport.TERMINE

    def is_erreur(self):
        """Vérifie si le rapport a une erreur"""
        return self.statut == StatutRapport.ERREUR

    def get_taille_fichier_mb(self):
        """Retourne la taille du fichier en MB"""
        if self.taille_fichier:
            return round(self.taille_fichier / (1024 * 1024), 2)
        return 0


class ModeleRapport(models.Model):
    """
    Modèle pour les modèles de rapports prédéfinis
    """
    nom = models.CharField(
        max_length=200,
        verbose_name=_('Nom du modèle')
    )
    
    type_rapport = models.CharField(
        max_length=20,
        choices=TypeRapport.choices,
        verbose_name=_('Type de rapport')
    )
    
    description = models.TextField(
        verbose_name=_('Description')
    )
    
    template = models.TextField(
        verbose_name=_('Template')
    )
    
    parametres_defaut = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Paramètres par défaut')
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
        verbose_name = _('Modèle de rapport')
        verbose_name_plural = _('Modèles de rapports')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class TableauBord(models.Model):
    """
    Modèle pour les tableaux de bord personnalisés
    """
    nom = models.CharField(
        max_length=200,
        verbose_name=_('Nom du tableau de bord')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    
    configuration = models.JSONField(
        verbose_name=_('Configuration')
    )
    
    est_public = models.BooleanField(
        default=False,
        verbose_name=_('Est public')
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='tableaux_bord',
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
        verbose_name = _('Tableau de bord')
        verbose_name_plural = _('Tableaux de bord')
        ordering = ['-created_at']

    def __str__(self):
        return self.nom