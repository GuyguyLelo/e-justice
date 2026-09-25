from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.comptes.models import Utilisateur
from apps.detenus.models import Detenu


class TypeConsultation(models.TextChoices):
    """Types de consultations"""
    CONSULTATION_GENERALE = 'CONSULTATION_GENERALE', _('Consultation générale')
    URGENCE = 'URGENCE', _('Urgence')
    SUIVI_MEDICAL = 'SUIVI_MEDICAL', _('Suivi médical')
    VACCINATION = 'VACCINATION', _('Vaccination')
    EXAMEN_LABORATOIRE = 'EXAMEN_LABORATOIRE', _('Examen de laboratoire')
    CONSULTATION_PSYCHOLOGIQUE = 'CONSULTATION_PSYCHOLOGIQUE', _('Consultation psychologique')


class StatutConsultation(models.TextChoices):
    """Statuts des consultations"""
    PROGRAMMEE = 'PROGRAMMEE', _('Programmée')
    EN_COURS = 'EN_COURS', _('En cours')
    TERMINEE = 'TERMINEE', _('Terminée')
    ANNULEE = 'ANNULEE', _('Annulée')


class TypeMedicament(models.TextChoices):
    """Types de médicaments"""
    ANTIBIOTIQUE = 'ANTIBIOTIQUE', _('Antibiotique')
    ANALGESIQUE = 'ANALGESIQUE', _('Analgésique')
    ANTI_INFLAMMATOIRE = 'ANTI_INFLAMMATOIRE', _('Anti-inflammatoire')
    VITAMINE = 'VITAMINE', _('Vitamine')
    CHRONIQUE = 'CHRONIQUE', _('Médicament chronique')
    URGENCE = 'URGENCE', _('Médicament d\'urgence')


class Consultation(models.Model):
    """
    Modèle pour les consultations médicales
    """
    # Relations
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        related_name='consultations',
        verbose_name=_('Détenu')
    )
    
    medecin = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='consultations_medicales',
        verbose_name=_('Médecin')
    )
    
    # Informations de la consultation
    type_consultation = models.CharField(
        max_length=30,
        choices=TypeConsultation.choices,
        verbose_name=_('Type de consultation')
    )
    
    date_consultation = models.DateTimeField(
        verbose_name=_('Date de consultation')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutConsultation.choices,
        default=StatutConsultation.PROGRAMMEE,
        verbose_name=_('Statut')
    )
    
    # Symptômes et diagnostic
    symptomes = models.TextField(
        verbose_name=_('Symptômes')
    )
    
    diagnostic = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Diagnostic')
    )
    
    traitement_prescrit = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Traitement prescrit')
    )
    
    recommandations = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Recommandations')
    )
    
    # Suivi
    date_controle = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Date de contrôle')
    )
    
    urgence = models.BooleanField(
        default=False,
        verbose_name=_('Urgence')
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
        verbose_name = _('Consultation')
        verbose_name_plural = _('Consultations')
        ordering = ['-date_consultation']

    def __str__(self):
        return f"{self.detenu.nom_complet} - {self.get_type_consultation_display()} ({self.date_consultation.strftime('%d/%m/%Y')})"

    def is_programmee(self):
        """Vérifie si la consultation est programmée"""
        return self.statut == StatutConsultation.PROGRAMMEE

    def is_en_cours(self):
        """Vérifie si la consultation est en cours"""
        return self.statut == StatutConsultation.EN_COURS

    def is_terminee(self):
        """Vérifie si la consultation est terminée"""
        return self.statut == StatutConsultation.TERMINEE


class Medicament(models.Model):
    """
    Modèle pour les médicaments
    """
    nom = models.CharField(
        max_length=200,
        verbose_name=_('Nom du médicament')
    )
    
    nom_commercial = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Nom commercial')
    )
    
    type_medicament = models.CharField(
        max_length=30,
        choices=TypeMedicament.choices,
        verbose_name=_('Type de médicament')
    )
    
    forme_pharmaceutique = models.CharField(
        max_length=100,
        verbose_name=_('Forme pharmaceutique')
    )
    
    dosage = models.CharField(
        max_length=100,
        verbose_name=_('Dosage')
    )
    
    stock_actuel = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Stock actuel')
    )
    
    stock_minimum = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Stock minimum')
    )
    
    date_expiration = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date d\'expiration')
    )
    
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Prix unitaire')
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
        verbose_name = _('Médicament')
        verbose_name_plural = _('Médicaments')
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.dosage})"

    def is_stock_faible(self):
        """Vérifie si le stock est faible"""
        return self.stock_actuel <= self.stock_minimum

    def is_expire(self):
        """Vérifie si le médicament est expiré"""
        from datetime import date
        return self.date_expiration and self.date_expiration < date.today()


class Prescription(models.Model):
    """
    Modèle pour les prescriptions médicales
    """
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name=_('Consultation')
    )
    
    medicament = models.ForeignKey(
        Medicament,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        verbose_name=_('Médicament')
    )
    
    posologie = models.CharField(
        max_length=200,
        verbose_name=_('Posologie')
    )
    
    duree_jours = models.PositiveIntegerField(
        verbose_name=_('Durée en jours')
    )
    
    quantite_prescrit = models.PositiveIntegerField(
        verbose_name=_('Quantité prescrite')
    )
    
    instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Instructions spéciales')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Prescription')
        verbose_name_plural = _('Prescriptions')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.medicament.nom} - {self.posologie}"


class AntecedentMedical(models.Model):
    """
    Modèle pour les antécédents médicaux des détenus
    """
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        related_name='antecedents',
        verbose_name=_('Détenu')
    )
    
    type_antecedent = models.CharField(
        max_length=100,
        verbose_name=_('Type d\'antécédent')
    )
    
    description = models.TextField(
        verbose_name=_('Description')
    )
    
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
    
    traitement_suivi = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Traitement suivi')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Antécédent médical')
        verbose_name_plural = _('Antécédents médicaux')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.detenu.nom_complet} - {self.type_antecedent}"


class Vaccination(models.Model):
    """
    Modèle pour les vaccinations des détenus
    """
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        related_name='vaccinations',
        verbose_name=_('Détenu')
    )
    
    nom_vaccin = models.CharField(
        max_length=200,
        verbose_name=_('Nom du vaccin')
    )
    
    date_vaccination = models.DateField(
        verbose_name=_('Date de vaccination')
    )
    
    lot_vaccin = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Lot du vaccin')
    )
    
    medecin_vaccinateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='vaccinations_effectuees',
        verbose_name=_('Médecin vaccinateur')
    )
    
    effets_secondaires = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Effets secondaires')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Vaccination')
        verbose_name_plural = _('Vaccinations')
        ordering = ['-date_vaccination']

    def __str__(self):
        return f"{self.detenu.nom_complet} - {self.nom_vaccin} ({self.date_vaccination.strftime('%d/%m/%Y')})"