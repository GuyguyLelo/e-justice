from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.comptes.models import Utilisateur
from apps.detenus.models import CentrePenitencier


class TypePersonnel(models.TextChoices):
    """Types de personnel"""
    DIRECTEUR = 'DIRECTEUR', _('Directeur')
    AGENT_SECURITE = 'AGENT_SECURITE', _('Agent de sécurité')
    AGENT_ADMINISTRATIF = 'AGENT_ADMINISTRATIF', _('Agent administratif')
    MEDECIN = 'MEDECIN', _('Médecin')
    INFIRMIER = 'INFIRMIER', _('Infirmier')
    PSYCHOLOGUE = 'PSYCHOLOGUE', _('Psychologue')
    CUISINIER = 'CUISINIER', _('Cuisinier')
    NETTOYEUR = 'NETTOYEUR', _('Agent de nettoyage')
    GARDIEN = 'GARDIEN', _('Gardien')


class StatutPersonnel(models.TextChoices):
    """Statuts du personnel"""
    ACTIF = 'ACTIF', _('Actif')
    INACTIF = 'INACTIF', _('Inactif')
    CONGE = 'CONGE', _('En congé')
    SUSPENDU = 'SUSPENDU', _('Suspendu')
    RETRAITE = 'RETRAITE', _('Retraité')


class Personnel(models.Model):
    """
    Modèle pour le personnel pénitentiaire
    """
    # Lien avec l'utilisateur (optionnel)
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='personnel',
        verbose_name=_('Utilisateur'),
        null=True,
        blank=True
    )
    
    # Centre d'affectation
    centre = models.ForeignKey(
        CentrePenitencier,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Centre pénitencier')
    )
    
    # Informations personnelles (si pas de compte utilisateur)
    nom = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Nom')
    )
    
    prenom = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Prénom')
    )
    
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Téléphone')
    )
    
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name=_('Email')
    )
    
    # Informations professionnelles
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Matricule')
    )
    
    type_personnel = models.CharField(
        max_length=30,
        choices=TypePersonnel.choices,
        verbose_name=_('Type de personnel')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutPersonnel.choices,
        default=StatutPersonnel.ACTIF,
        verbose_name=_('Statut')
    )
    
    date_embauche = models.DateField(
        verbose_name=_('Date d\'embauche')
    )
    
    date_fin_contrat = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de fin de contrat')
    )
    
    salaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Salaire')
    )
    
    # Informations professionnelles spécifiques
    specialite = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Spécialité')
    )
    
    numero_ordre = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Numéro d\'ordre (pour médecins)')
    )
    
    # Horaires de travail
    heures_travail_semaine = models.PositiveIntegerField(
        default=40,
        validators=[MinValueValidator(1), MaxValueValidator(80)],
        verbose_name=_('Heures de travail par semaine')
    )
    
    # Informations de contact d'urgence
    contact_urgence_nom = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Nom du contact d\'urgence')
    )
    
    contact_urgence_telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Téléphone du contact d\'urgence')
    )
    
    contact_urgence_relation = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Relation avec le contact d\'urgence')
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
        verbose_name = _('Personnel')
        verbose_name_plural = _('Personnel')
        ordering = ['-created_at']

    def __str__(self):
        if self.utilisateur:
            return f"{self.utilisateur.get_full_name()} - {self.matricule}"
        elif self.nom and self.prenom:
            return f"{self.nom} {self.prenom} - {self.matricule}"
        else:
            return f"{self.matricule}"

    @property
    def nom_complet(self):
        """Retourne le nom complet du personnel"""
        if self.utilisateur:
            return self.utilisateur.get_full_name()
        elif self.nom and self.prenom:
            return f"{self.nom} {self.prenom}"
        else:
            return self.matricule

    def is_medecin(self):
        """Vérifie si le personnel est médecin"""
        return self.type_personnel == TypePersonnel.MEDECIN

    def is_agent_securite(self):
        """Vérifie si le personnel est agent de sécurité"""
        return self.type_personnel == TypePersonnel.AGENT_SECURITE

    def is_actif(self):
        """Vérifie si le personnel est actif"""
        return self.statut == StatutPersonnel.ACTIF

    def anciennete_annees(self):
        """Calcule l'ancienneté en années"""
        from datetime import date
        today = date.today()
        return today.year - self.date_embauche.year - (
            (today.month, today.day) < (self.date_embauche.month, self.date_embauche.day)
        )


class FormationPersonnel(models.Model):
    """
    Formations suivies par le personnel
    """
    personnel = models.ForeignKey(
        Personnel,
        on_delete=models.CASCADE,
        related_name='formations',
        verbose_name=_('Personnel')
    )
    
    nom_formation = models.CharField(
        max_length=200,
        verbose_name=_('Nom de la formation')
    )
    
    organisme = models.CharField(
        max_length=200,
        verbose_name=_('Organisme formateur')
    )
    
    date_debut = models.DateField(
        verbose_name=_('Date de début')
    )
    
    date_fin = models.DateField(
        verbose_name=_('Date de fin')
    )
    
    duree_heures = models.PositiveIntegerField(
        verbose_name=_('Durée en heures')
    )
    
    certificat = models.FileField(
        upload_to='certificats/',
        blank=True,
        null=True,
        verbose_name=_('Certificat')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Formation personnel')
        verbose_name_plural = _('Formations personnel')
        ordering = ['-date_fin']

    def __str__(self):
        return f"{self.personnel.utilisateur.get_full_name()} - {self.nom_formation}"


class SanctionPersonnel(models.Model):
    """
    Sanctions appliquées au personnel
    """
    personnel = models.ForeignKey(
        Personnel,
        on_delete=models.CASCADE,
        related_name='sanctions',
        verbose_name=_('Personnel')
    )
    
    type_sanction = models.CharField(
        max_length=100,
        verbose_name=_('Type de sanction')
    )
    
    motif = models.TextField(
        verbose_name=_('Motif')
    )
    
    date_sanction = models.DateField(
        verbose_name=_('Date de sanction')
    )
    
    duree_jours = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Durée en jours')
    )
    
    sanctionne_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sanctions_appliquees',
        verbose_name=_('Sanctionné par')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Sanction personnel')
        verbose_name_plural = _('Sanctions personnel')
        ordering = ['-date_sanction']

    def __str__(self):
        return f"{self.personnel.utilisateur.get_full_name()} - {self.type_sanction}"