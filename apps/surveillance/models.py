from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.comptes.models import Utilisateur
from apps.detenus.models import CentrePenitencier, Detenu


class TypeCamera(models.TextChoices):
    """Types de caméras de surveillance"""
    INTERIEURE = 'INTERIEURE', _('Intérieure')
    EXTERIEURE = 'EXTERIEURE', _('Extérieure')
    PTZ = 'PTZ', _('PTZ (Pan-Tilt-Zoom)')
    DOME = 'DOME', _('Dôme')
    BULLET = 'BULLET', _('Bullet')
    FISHEYE = 'FISHEYE', _('Fisheye')


class StatutCamera(models.TextChoices):
    """Statuts des caméras"""
    ACTIVE = 'ACTIVE', _('Active')
    INACTIVE = 'INACTIVE', _('Inactive')
    MAINTENANCE = 'MAINTENANCE', _('En maintenance')
    HORS_SERVICE = 'HORS_SERVICE', _('Hors service')


class QualiteDetection(models.TextChoices):
    """Niveaux de qualité de détection"""
    FAIBLE = 'FAIBLE', _('Faible')
    MOYENNE = 'MOYENNE', _('Moyenne')
    BONNE = 'BONNE', _('Bonne')
    EXCELLENTE = 'EXCELLENTE', _('Excellente')


class Camera(models.Model):
    """
    Modèle pour les caméras de surveillance
    """
    nom = models.CharField(
        max_length=200,
        verbose_name=_('Nom de la caméra')
    )
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Code de la caméra')
    )
    
    centre = models.ForeignKey(
        CentrePenitencier,
        on_delete=models.CASCADE,
        verbose_name=_('Centre pénitencier')
    )
    
    type_camera = models.CharField(
        max_length=20,
        choices=TypeCamera.choices,
        default=TypeCamera.INTERIEURE,
        verbose_name=_('Type de caméra')
    )
    
    emplacement = models.CharField(
        max_length=200,
        verbose_name=_('Emplacement')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Description')
    )
    
    adresse_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('Adresse IP')
    )
    
    port = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(65535)],
        verbose_name=_('Port')
    )
    
    url_flux = models.URLField(
        blank=True,
        null=True,
        verbose_name=_('URL du flux vidéo')
    )
    
    resolution = models.CharField(
        max_length=20,
        default='1920x1080',
        verbose_name=_('Résolution')
    )
    
    fps = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name=_('Images par seconde')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutCamera.choices,
        default=StatutCamera.INACTIVE,
        verbose_name=_('Statut')
    )
    
    detection_active = models.BooleanField(
        default=True,
        verbose_name=_('Détection active')
    )
    
    reconnaissance_faciale_active = models.BooleanField(
        default=True,
        verbose_name=_('Reconnaissance faciale active')
    )
    
    qualite_detection = models.CharField(
        max_length=20,
        choices=QualiteDetection.choices,
        default=QualiteDetection.MOYENNE,
        verbose_name=_('Qualité de détection')
    )
    
    angle_vue = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(360)],
        verbose_name=_('Angle de vue (degrés)')
    )
    
    portee_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        verbose_name=_('Portée maximale (mètres)')
    )
    
    date_installation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date d\'installation')
    )
    
    derniere_maintenance = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Dernière maintenance')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de mise à jour')
    )
    
    class Meta:
        verbose_name = _('Caméra')
        verbose_name_plural = _('Caméras')
        ordering = ['centre__nom', 'nom']
        unique_together = ['centre', 'code']
    
    def __str__(self):
        return f"{self.nom} - {self.centre.nom}"
    
    @property
    def est_en_ligne(self):
        """Vérifie si la caméra est en ligne"""
        return self.statut == StatutCamera.ACTIVE
    
    @property
    def url_complete(self):
        """Retourne l'URL complète du flux vidéo"""
        if self.adresse_ip and self.port:
            return f"rtsp://{self.adresse_ip}:{self.port}/stream"
        return self.url_flux


class ZoneSurveillance(models.Model):
    """
    Modèle pour les zones de surveillance spécifiques
    """
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name='zones',
        verbose_name=_('Caméra')
    )
    
    nom = models.CharField(
        max_length=100,
        verbose_name=_('Nom de la zone')
    )
    
    coordonnees = models.JSONField(
        verbose_name=_('Coordonnées de la zone'),
        help_text=_('Coordonnées polygonales de la zone [x1,y1, x2,y2, ...]')
    )
    
    type_zone = models.CharField(
        max_length=50,
        choices=[
            ('ENTREE', _('Entrée')),
            ('SORTIE', _('Sortie')),
            ('COULOIR', _('Couloir')),
            ('COUR', _('Cour')),
            ('CELLULE', _('Cellule')),
            ('REFECTOIRE', _('Réfectoire')),
            ('ATELIER', _('Atelier')),
            ('INFIRMERIE', _('Infirmerie')),
            ('AUTRE', _('Autre'))
        ],
        default='AUTRE',
        verbose_name=_('Type de zone')
    )
    
    detection_active = models.BooleanField(
        default=True,
        verbose_name=_('Détection active')
    )
    
    seuil_alerte = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Seuil d\'alerte'),
        help_text=_('Nombre de détections avant alerte')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de mise à jour')
    )
    
    class Meta:
        verbose_name = _('Zone de surveillance')
        verbose_name_plural = _('Zones de surveillance')
        ordering = ['camera__nom', 'nom']
    
    def __str__(self):
        return f"{self.nom} - {self.camera.nom}"


class ProfilFacialDetenu(models.Model):
    """
    Modèle pour stocker les profils faciaux des détenus
    """
    detenu = models.OneToOneField(
        Detenu,
        on_delete=models.CASCADE,
        related_name='profil_facial',
        verbose_name=_('Détenu')
    )
    
    encodage_facial = models.JSONField(
        verbose_name=_('Encodage facial'),
        help_text=_('Encodage numérique du visage pour la reconnaissance')
    )
    
    image_reference = models.ImageField(
        upload_to='surveillance/references/',
        verbose_name=_('Image de référence')
    )
    
    qualite_image = models.CharField(
        max_length=20,
        choices=QualiteDetection.choices,
        default=QualiteDetection.MOYENNE,
        verbose_name=_('Qualité de l\'image')
    )
    
    date_enregistrement = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date d\'enregistrement')
    )
    
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Dernière mise à jour')
    )
    
    actif = models.BooleanField(
        default=True,
        verbose_name=_('Profil actif')
    )
    
    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Créé par')
    )
    
    class Meta:
        verbose_name = _('Profil facial de détenu')
        verbose_name_plural = _('Profils faciaux de détenus')
        ordering = ['-date_enregistrement']
    
    def __str__(self):
        return f"Profil facial - {self.detenu.nom_complet}"


class DetectionFaciale(models.Model):
    """
    Modèle pour enregistrer les détections faciales
    """
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Caméra')
    )
    
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Détenu identifié')
    )
    
    zone = models.ForeignKey(
        ZoneSurveillance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Zone de détection')
    )
    
    image_detection = models.ImageField(
        upload_to='surveillance/detections/',
        verbose_name=_('Image de détection')
    )
    
    confiance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Taux de confiance (%)')
    )
    
    coordonnees_visage = models.JSONField(
        verbose_name=_('Coordonnées du visage'),
        help_text=_('Coordonnées du rectangle englobant le visage [x, y, largeur, hauteur]')
    )
    
    timestamp = models.DateTimeField(
        verbose_name=_('Date et heure de détection')
    )
    
    est_alerte = models.BooleanField(
        default=False,
        verbose_name=_('Alerte générée')
    )
    
    motif_alerte = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Motif de l\'alerte')
    )
    
    traitee = models.BooleanField(
        default=False,
        verbose_name=_('Détection traitée')
    )
    
    traitee_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Traitée par')
    )
    
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de traitement')
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Notes')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    class Meta:
        verbose_name = _('Détection faciale')
        verbose_name_plural = _('Détections faciales')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['camera', 'timestamp']),
            models.Index(fields=['detenu', 'timestamp']),
            models.Index(fields=['est_alerte', 'traitee']),
        ]
    
    def __str__(self):
        if self.detenu:
            return f"Detection - {self.detenu.nom_complet} - {self.camera.nom}"
        return f"Detection inconnue - {self.camera.nom}"

    def image_existe(self):
        """True si le fichier image est réellement présent sur le disque."""
        if not self.image_detection:
            return False
        try:
            return self.image_detection.storage.exists(self.image_detection.name)
        except Exception:
            return False

    @property
    def image_publique_url(self):
        from django.urls import reverse
        return reverse('surveillance_detection_image', args=[self.pk])

    def enregistrer_image(self, image_bytes, filename):
        """Enregistre l'image de détection sur disque (upload_to)."""
        from django.core.files.base import ContentFile
        self.image_detection.save(filename, ContentFile(image_bytes), save=True)
    
    @property
    def est_identifie(self):
        """Vérifie si la détection a été identifiée"""
        return self.detenu is not None
    
    @property
    def niveau_confiance(self):
        """Retourne le niveau de confiance"""
        if self.confiance >= 80:
            return 'Élevé'
        elif self.confiance >= 60:
            return 'Moyen'
        else:
            return 'Faible'


class AlerteSurveillance(models.Model):
    """
    Modèle pour gérer les alertes de surveillance
    """
    TYPE_ALERTE_CHOICES = [
        ('DETECTION_INCONNUE', _('Détection visage inconnu')),
        ('DETENU_INTERDIT', _('Détenu dans zone interdite')),
        ('DETECTION_MULTIPLE', _('Détections multiples suspectes')),
        ('ABSENCE_DETENU', _('Absence de détenu attendu')),
        ('MOUVEMENT_SUSPECT', _('Mouvement suspect')),
        ('CAMERA_HORS_SERVICE', _('Caméra hors service')),
        ('AUTRE', _('Autre')),
    ]
    
    NIVEAU_ALERTE_CHOICES = [
        ('INFO', _('Information')),
        ('ATTENTION', _('Attention')),
        ('WARNING', _('Avertissement')),
        ('CRITIQUE', _('Critique')),
    ]
    
    STATUT_ALERTE_CHOICES = [
        ('OUVERTE', _('Ouverte')),
        ('EN_COURS', _('En cours de traitement')),
        ('RESOLUE', _('Résolue')),
        ('FAUSSE_ALERTE', _('Fausse alerte')),
    ]
    
    titre = models.CharField(
        max_length=200,
        verbose_name=_('Titre de l\'alerte')
    )
    
    type_alerte = models.CharField(
        max_length=30,
        choices=TYPE_ALERTE_CHOICES,
        verbose_name=_('Type d\'alerte')
    )
    
    niveau = models.CharField(
        max_length=20,
        choices=NIVEAU_ALERTE_CHOICES,
        default='ATTENTION',
        verbose_name=_('Niveau d\'alerte')
    )
    
    description = models.TextField(
        verbose_name=_('Description')
    )
    
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Caméra concernée')
    )
    
    detection = models.ForeignKey(
        DetectionFaciale,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Détection concernée')
    )
    
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Détenu concerné')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_ALERTE_CHOICES,
        default='OUVERTE',
        verbose_name=_('Statut')
    )
    
    assigne_a = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_assignees',
        verbose_name=_('Assignée à')
    )
    
    traitee_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_traitees',
        verbose_name=_('Traitée par')
    )
    
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    date_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de traitement')
    )
    
    resolution = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Résolution')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de mise à jour')
    )
    
    class Meta:
        verbose_name = _('Alerte de surveillance')
        verbose_name_plural = _('Alertes de surveillance')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['statut', 'date_creation']),
            models.Index(fields=['niveau', 'date_creation']),
        ]
    
    def __str__(self):
        return f"{self.titre} - {self.get_niveau_display()}"
    
    @property
    def est_ouverte(self):
        """Vérifie si l'alerte est ouverte"""
        return self.statut in ['OUVERTE', 'EN_COURS']
    
    @property
    def delai_resolution(self):
        """Calcule le délai de résolution"""
        if self.date_traitement and self.date_creation:
            return self.date_traitement - self.date_creation
        return None


class HistoriqueSurveillance(models.Model):
    """
    Modèle pour l'historique des événements de surveillance
    """
    TYPE_EVENEMENT_CHOICES = [
        ('DETECTION', _('Détection faciale')),
        ('ALERTE', _('Alerte générée')),
        ('CAMERA_ON', _('Caméra mise en marche')),
        ('CAMERA_OFF', _('Caméra arrêtée')),
        ('MAINTENANCE', _('Maintenance caméra')),
        ('CONFIG_CHANGE', _('Changement configuration')),
        ('SYSTEM_START', _('Démarrage système')),
        ('SYSTEM_STOP', _('Arrêt système')),
    ]
    
    type_evenement = models.CharField(
        max_length=30,
        choices=TYPE_EVENEMENT_CHOICES,
        verbose_name=_('Type d\'événement')
    )
    
    description = models.TextField(
        verbose_name=_('Description')
    )
    
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Caméra concernée')
    )
    
    detection = models.ForeignKey(
        DetectionFaciale,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Détection concernée')
    )
    
    alerte = models.ForeignKey(
        AlerteSurveillance,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Alerte concernée')
    )
    
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Utilisateur concerné')
    )
    
    donnees_supplementaires = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('Données supplémentaires')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp')
    )
    
    adresse_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name=_('Adresse IP source')
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('User Agent')
    )
    
    class Meta:
        verbose_name = _('Historique de surveillance')
        verbose_name_plural = _('Historiques de surveillance')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['type_evenement', 'timestamp']),
            models.Index(fields=['camera', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_type_evenement_display()} - {self.timestamp}"
