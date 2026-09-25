from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.TextChoices):
    """Choix des rôles utilisateur"""
    ADMIN_CENTRAL = 'ADMIN_CENTRAL', _('Administrateur Central')
    ADMIN = 'ADMIN', _('Administrateur')
    DIRECTEUR = 'DIRECTEUR', _('Directeur')
    AGENT = 'AGENT', _('Agent')
    MEDECIN = 'MEDECIN', _('Médecin')
    VISITEUR = 'VISITEUR', _('Visiteur')


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé basé sur AbstractUser
    """
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.AGENT,
        verbose_name=_('Rôle')
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
    
    date_embauche = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date d\'embauche')
    )
    
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_('Est actif')
    )
    
    photo = models.ImageField(
        upload_to='photos_utilisateurs/',
        blank=True,
        null=True,
        verbose_name=_('Photo')
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
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def full_name(self):
        """Propriété pour le nom complet de l'utilisateur"""
        return self.get_full_name()

    def is_admin_central(self):
        """Vérifie si l'utilisateur est administrateur central"""
        return self.role == Role.ADMIN_CENTRAL

    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == Role.ADMIN

    def is_directeur(self):
        """Vérifie si l'utilisateur est directeur"""
        return self.role == Role.DIRECTEUR

    def is_agent(self):
        """Vérifie si l'utilisateur est agent"""
        return self.role == Role.AGENT

    def is_medecin(self):
        """Vérifie si l'utilisateur est médecin"""
        return self.role == Role.MEDECIN

    def is_visiteur(self):
        """Vérifie si l'utilisateur est visiteur"""
        return self.role == Role.VISITEUR

    def is_consultation_only(self):
        """Admin central : pas de modification des données opérationnelles des prisons."""
        return self.role == Role.ADMIN_CENTRAL

    def can_manage_centres(self):
        """L'administrateur central peut modifier les prisons."""
        return self.role == Role.ADMIN_CENTRAL

    def can_create_centres(self):
        """L'administrateur central peut créer des prisons."""
        return self.role == Role.ADMIN_CENTRAL

    def can_manage_admins(self):
        """L'administrateur central gère les comptes des admins de prison."""
        return self.role == Role.ADMIN_CENTRAL

    def can_create_admins(self):
        """L'administrateur central crée les administrateurs de prison."""
        return self.role == Role.ADMIN_CENTRAL

    def can_view_all_centres(self):
        """Vérifie si l'utilisateur peut voir tous les centres (admin central)."""
        return self.role == Role.ADMIN_CENTRAL

    def can_view_all_data(self):
        """Vérifie si l'utilisateur peut voir toutes les données (admin central, lecture seule)."""
        return self.role == Role.ADMIN_CENTRAL

    def can_edit_centre_info(self):
        """L'administrateur central peut modifier les informations d'une prison."""
        return self.role == Role.ADMIN_CENTRAL

    def can_manage_centre_info(self):
        """Alias template : modification des infos centre."""
        return self.can_edit_centre_info()

    def can_manage_centre_detenus(self):
        """Vérifie si l'utilisateur peut gérer les détenus de son centre"""
        return (self.role in [Role.ADMIN, Role.DIRECTEUR, Role.AGENT] and 
                hasattr(self, 'adminprison'))

    def can_edit_detenus(self):
        """Vérifie si l'utilisateur peut modifier les détenus"""
        # Admin central ne peut PAS modifier les détenus (lecture seule)
        # Admins de centre peuvent modifier les détenus de leur centre
        return (self.role in [Role.ADMIN, Role.DIRECTEUR, Role.AGENT] and 
                hasattr(self, 'adminprison'))

    def can_edit_personnel(self):
        """Vérifie si l'utilisateur peut modifier le personnel"""
        # Admin central ne peut PAS modifier le personnel (lecture seule)
        # Admins de centre peuvent modifier le personnel de leur centre
        return (self.role in [Role.ADMIN, Role.DIRECTEUR] and 
                hasattr(self, 'adminprison'))

    def can_edit_visites(self):
        """Vérifie si l'utilisateur peut modifier les visites"""
        # Admin central ne peut PAS modifier les visites (lecture seule)
        # Admins de centre peuvent modifier les visites de leur centre
        return (self.role in [Role.ADMIN, Role.DIRECTEUR, Role.AGENT] and 
                hasattr(self, 'adminprison'))

    def can_view_visites(self):
        """Consultation des visites : admin central (toutes) ou personnel de prison."""
        if self.role == Role.ADMIN_CENTRAL:
            return True
        return self.can_edit_visites()

    def get_accessible_centre(self):
        """Retourne le centre accessible par l'utilisateur (pour admins de centre)"""
        if hasattr(self, 'adminprison'):
            return self.adminprison.centre
        return None