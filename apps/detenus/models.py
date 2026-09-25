from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from datetime import datetime
from apps.comptes.models import Utilisateur, Role


class StatutDetenu(models.TextChoices):
    """Choix des statuts de détenu"""
    INCARCERE = 'INCARCERE', _('Incarcéré')
    LIBERE = 'LIBERE', _('Libéré')
    TRANSFERE = 'TRANSFERE', _('Transféré')
    EVADE = 'EVADE', _('Évadé')
    DECEDE = 'DECEDE', _('Décédé')


class TypePeine(models.TextChoices):
    """Types de peines"""
    PREVENTIF = 'PREVENTIF', _('Préventif')
    CONDAMNE = 'CONDAMNE', _('Condamné')
    AMENDE = 'AMENDE', _('Amende')
    TRAVAUX_INTERET = 'TRAVAUX_INTERET', _('Travaux d\'intérêt général')


class TypeCentre(models.TextChoices):
    """Types de centres pénitenciers"""
    PRISON = 'PRISON', _('Prison')
    MAISON_D_ARRET = 'MAISON_D_ARRET', _('Maison d\'arrêt')
    CENTRE_DE_DETENTION = 'CENTRE_DE_DETENTION', _('Centre de détention')
    ETABLISSEMENT_PENITENTIAIRE = 'ETABLISSEMENT_PENITENTIAIRE', _('Établissement pénitentiaire')


class CentrePenitencier(models.Model):
    """
    Modèle pour les centres pénitenciers
    """
    nom = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Nom du centre')
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Code du centre')
    )
    
    type_centre = models.CharField(
        max_length=30,
        choices=TypeCentre.choices,
        default=TypeCentre.PRISON,
        verbose_name=_('Type de centre')
    )
    
    adresse = models.TextField(
        verbose_name=_('Adresse')
    )

    province = models.CharField(
        max_length=80,
        blank=True,
        default='',
        verbose_name=_('Province')
    )

    ville = models.CharField(
        max_length=80,
        blank=True,
        default='',
        verbose_name=_('Ville')
    )

    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name=_('Latitude')
    )

    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
        verbose_name=_('Longitude')
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
    
    capacite_max = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Capacité maximale')
    )
    
    capacite_actuelle = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Capacité actuelle')
    )
    
    directeur = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Directeur')
    )
    
    date_ouverture = models.DateField(
        verbose_name=_('Date d\'ouverture')
    )
    
    statut = models.BooleanField(
        default=True,
        verbose_name=_('Actif')
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
        verbose_name = _('Centre pénitencier')
        verbose_name_plural = _('Centres pénitenciers')
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    @property
    def taux_occupation(self):
        """Calcule le taux d'occupation"""
        if self.capacite_max == 0:
            return 0
        return (self.capacite_actuelle / self.capacite_max) * 100
    
    @property
    def places_disponibles(self):
        """Calcule le nombre de places disponibles"""
        return self.capacite_max - self.capacite_actuelle

    @property
    def has_geoloc(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def photo_couverture(self):
        photo = self.photos.first()
        return photo.image if photo else None


class CentrePhoto(models.Model):
    """Photos d'un centre pénitencier (façade, bâtiments, etc.)."""

    centre = models.ForeignKey(
        CentrePenitencier,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Centre'),
    )
    image = models.ImageField(
        upload_to='centres/photos/',
        verbose_name=_('Photo'),
    )
    legende = models.CharField(
        max_length=200,
        blank=True,
        default='',
        verbose_name=_('Légende'),
    )
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Ordre'),
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date d\'ajout'),
    )

    class Meta:
        verbose_name = _('Photo du centre')
        verbose_name_plural = _('Photos du centre')
        ordering = ['ordre', 'id']

    def __str__(self):
        return f"{self.centre.code} — photo {self.pk}"


class TypePopulationCellule(models.TextChoices):
    HOMMES = 'HOMMES', _('Hommes')
    FEMMES = 'FEMMES', _('Femmes')


class Cellule(models.Model):
    """Cellule rattachée à un pavillon du centre pénitencier."""

    centre = models.ForeignKey(
        CentrePenitencier,
        on_delete=models.CASCADE,
        related_name='cellules',
        verbose_name=_('Centre'),
    )
    pavillon = models.CharField(max_length=20, verbose_name=_('Pavillon'))
    nom_pavillon = models.CharField(max_length=100, verbose_name=_('Nom du pavillon'))
    code = models.CharField(max_length=20, verbose_name=_('Code cellule'))
    type_population = models.CharField(
        max_length=10,
        choices=TypePopulationCellule.choices,
        default=TypePopulationCellule.HOMMES,
        verbose_name=_('Population'),
    )
    capacite = models.PositiveIntegerField(default=4, verbose_name=_('Capacité'))
    actif = models.BooleanField(default=True, verbose_name=_('Active'))

    class Meta:
        verbose_name = _('Cellule')
        verbose_name_plural = _('Cellules')
        ordering = ['centre', 'pavillon', 'code']
        unique_together = [('centre', 'code')]

    def __str__(self):
        return f"{self.code} ({self.centre.code})"

    @property
    def libelle_pavillon(self):
        return f"Pavillon {self.pavillon} — {self.nom_pavillon}"


class AdminPrison(models.Model):
    """
    Modèle pour les administrateurs de prison
    """
    utilisateur = models.OneToOneField(
        Utilisateur,
        on_delete=models.CASCADE,
        verbose_name=_('Utilisateur')
    )
    
    centre = models.ForeignKey(
        CentrePenitencier,
        on_delete=models.CASCADE,
        verbose_name=_('Centre pénitencier')
    )
    
    matricule_admin = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Matricule administrateur')
    )
    
    poste = models.CharField(
        max_length=100,
        verbose_name=_('Poste')
    )
    
    date_affectation = models.DateField(
        verbose_name=_('Date d\'affectation')
    )
    
    statut = models.BooleanField(
        default=True,
        verbose_name=_('Actif')
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
        verbose_name = _('Administrateur de prison')
        verbose_name_plural = _('Administrateurs de prison')
        ordering = ['centre__nom', 'utilisateur__first_name']
    
    def __str__(self):
        return f"{self.utilisateur.get_full_name()} - {self.centre.nom}"


class Detenu(models.Model):
    """
    Modèle principal pour les détenus
    """
    # Informations personnelles
    matricule = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Matricule')
    )
    
    nom = models.CharField(
        max_length=100,
        verbose_name=_('Nom')
    )
    
    prenom = models.CharField(
        max_length=100,
        verbose_name=_('Prénom')
    )
    
    sexe = models.CharField(
        max_length=1,
        choices=[('M', _('Masculin')), ('F', _('Féminin'))],
        verbose_name=_('Sexe')
    )
    
    date_naissance = models.DateField(
        verbose_name=_('Date de naissance')
    )
    
    lieu_naissance = models.CharField(
        max_length=200,
        verbose_name=_('Lieu de naissance')
    )
    
    nationalite = models.CharField(
        max_length=100,
        default='Congolaise',
        verbose_name=_('Nationalité')
    )
    
    profession = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Profession')
    )
    
    adresse = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Adresse')
    )
    
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Téléphone')
    )
    
    # Centre pénitencier
    centre = models.ForeignKey(
        CentrePenitencier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_('Centre pénitencier')
    )
    
    # Informations judiciaires
    date_arrestation = models.DateField(
        verbose_name=_('Date d\'arrestation')
    )
    
    date_incarceration = models.DateField(
        verbose_name=_('Date d\'incarcération')
    )
    
    motif_incarceration = models.TextField(
        verbose_name=_('Motif d\'incarcération')
    )
    
    tribunal = models.CharField(
        max_length=200,
        verbose_name=_('Tribunal')
    )
    
    numero_dossier = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_('Numéro de dossier')
    )

    dossier = models.FileField(
        upload_to='detenus/dossiers/',
        blank=True,
        null=True,
        verbose_name=_('Dossier du détenu'),
        help_text=_('Fichier du dossier judiciaire (PDF, image ou document)')
    )
    
    avocat = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Avocat')
    )
    
    telephone_avocat = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('Téléphone avocat')
    )
    
    # Informations pénitentiaires
    cellule = models.CharField(
        max_length=20,
        verbose_name=_('Cellule')
    )
    
    regime = models.CharField(
        max_length=20,
        choices=TypePeine.choices,
        default=TypePeine.PREVENTIF,
        verbose_name=_('Régime')
    )
    
    statut = models.CharField(
        max_length=20,
        choices=StatutDetenu.choices,
        default=StatutDetenu.INCARCERE,
        verbose_name=_('Statut')
    )
    
    # Peine
    duree_peine_mois = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(1200)],
        verbose_name=_('Durée de peine (mois)')
    )
    
    date_liberation_prevue = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de libération prévue')
    )
    
    date_liberation_effective = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de libération effective')
    )
    
    motif_liberation = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Motif de libération')
    )
    
    # Informations médicales
    groupe_sanguin = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        verbose_name=_('Groupe sanguin')
    )
    
    allergies = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Allergies')
    )
    
    maladies_chroniques = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Maladies chroniques')
    )
    
    # Données biométriques
    taille = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(100), MaxValueValidator(250)],
        verbose_name=_('Taille (cm)'),
        help_text=_('Taille en centimètres')
    )
    
    poids = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(20), MaxValueValidator(300)],
        verbose_name=_('Poids (kg)'),
        help_text=_('Poids en kilogrammes')
    )
    
    couleur_yeux = models.CharField(
        max_length=20,
        choices=[
            ('NOIR', _('Noir')), ('MARRON', _('Marron')), ('BLEU', _('Bleu')),
            ('VERT', _('Vert')), ('GRIS', _('Gris')), ('NOISETTE', _('Noisette'))
        ],
        blank=True,
        null=True,
        verbose_name=_('Couleur des yeux')
    )
    
    couleur_cheveux = models.CharField(
        max_length=20,
        choices=[
            ('NOIR', _('Noir')), ('BRUN', _('Brun')), ('BLOND', _('Blond')),
            ('ROUX', _('Roux')), ('BLANC', _('Blanc')), ('CHATAIN', _('Châtain'))
        ],
        blank=True,
        null=True,
        verbose_name=_('Couleur des cheveux')
    )
    
    type_cheveux = models.CharField(
        max_length=20,
        choices=[
            ('LISSE', _('Lisse')), ('ONDULE', _('Ondulé')), ('BOUCLE', _('Bouclé')),
            ('CREPU', _('Crépu')), ('RAIDE', _('Raide'))
        ],
        blank=True,
        null=True,
        verbose_name=_('Type de cheveux')
    )
    
    couleur_peau = models.CharField(
        max_length=20,
        choices=[
            ('CLAIR', _('Clair')), ('MAT', _('Mat')), ('BRUN', _('Brun')),
            ('NOIR', _('Noir')), ('MIXTE', _('Mixte'))
        ],
        blank=True,
        null=True,
        verbose_name=_('Couleur de peau')
    )
    
    cicatrices = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Cicatrices et marques distinctives'),
        help_text=_('Description des cicatrices, tatouages, piercings, etc.')
    )
    
    photo_face = models.ImageField(
        upload_to='detenus/photos/',
        blank=True,
        null=True,
        verbose_name=_('Photo de face'),
        help_text=_('Photo de face du détenu')
    )
    
    photo_profil = models.ImageField(
        upload_to='detenus/photos/',
        blank=True,
        null=True,
        verbose_name=_('Photo de profil'),
        help_text=_('Photo de profil du détenu')
    )
    
    empreintes_digitales = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Empreintes digitales'),
        help_text=_('Données des empreintes digitales (encodées)')
    )
    
    adn = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Profil ADN'),
        help_text=_('Profil ADN du détenu (encodé)')
    )
    
    # Métadonnées
    created_by = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='detenus_crees',
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
        verbose_name = _('Détenu')
        verbose_name_plural = _('Détenus')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.matricule})"

    @property
    def nom_complet(self):
        """Retourne le nom complet du détenu"""
        return f"{self.nom} {self.prenom}"

    @property
    def age(self):
        """Calcule l'âge du détenu"""
        from datetime import date
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )

    @property
    def duree_detention(self):
        """Calcule la durée de détention en jours"""
        from datetime import date
        if self.statut == StatutDetenu.INCARCERE:
            return (date.today() - self.date_incarceration).days
        elif self.date_liberation_effective:
            return (self.date_liberation_effective - self.date_incarceration).days
        return 0

    def is_incarcerated(self):
        """Vérifie si le détenu est actuellement incarcéré"""
        return self.statut == StatutDetenu.INCARCERE

    def can_be_visited(self):
        """Vérifie si le détenu peut recevoir des visites"""
        return self.is_incarcerated()


class HistoriqueDetenu(models.Model):
    """
    Historique des modifications d'un détenu
    """
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name=_('Détenu')
    )
    
    action = models.CharField(
        max_length=100,
        verbose_name=_('Action')
    )
    
    ancienne_valeur = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Ancienne valeur')
    )
    
    nouvelle_valeur = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Nouvelle valeur')
    )
    
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Utilisateur')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )

    class Meta:
        verbose_name = _('Historique détenu')
        verbose_name_plural = _('Historiques détenus')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.detenu.nom_complet} - {self.action}"


@receiver(post_save, sender=CentrePenitencier)
def create_centre_admin(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement un administrateur du centre 
    lors de la création d'un nouveau centre
    """
    if created:
        # Compter le nombre d'admins existants pour déterminer le prochain numéro
        from apps.comptes.models import Utilisateur
        existing_admins_count = Utilisateur.objects.filter(
            role=Role.ADMIN,
            username__startswith='admin'
        ).count()
        
        # Incrémenter le numéro d'admin
        admin_number = existing_admins_count + 1
        username = f"admin{admin_number}"
        
        # Créer l'utilisateur avec le rôle ADMIN
        utilisateur = Utilisateur.objects.create_user(
            username=username,
            email=f"{username}@{instance.code.lower()}.com",
            password="admin123",
            first_name="Administrateur",
            last_name=instance.nom,
            role=Role.ADMIN  # Utiliser Role.ADMIN depuis apps.comptes.models
        )
        
        # Créer l'AdminPrison associé
        AdminPrison.objects.create(
            utilisateur=utilisateur,
            centre=instance,
            matricule_admin=f"ADM_{instance.code}_{admin_number}",
            poste="Administrateur du Centre",
            date_affectation=instance.date_ouverture,
            statut=True
        )


class FicheDetenu(models.Model):
    """
    Modèle pour gérer les fiches d'identification des détenus
    """
    detenu = models.ForeignKey(
        Detenu,
        on_delete=models.CASCADE,
        verbose_name=_('Détenu')
    )
    
    numero_fiche = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Numéro de fiche')
    )
    
    date_emission = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date d\'émission')
    )
    
    valide_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Validé par')
    )
    
    statut_validation = models.CharField(
        max_length=20,
        choices=[
            ('EN_ATTENTE', 'En attente'),
            ('VALIDE', 'Validé'),
            ('ANNULE', 'Annulé')
        ],
        default='VALIDE',
        verbose_name=_('Statut de validation')
    )
    
    # Informations supplémentaires pour la fiche
    informations_supplementaires = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Informations supplémentaires')
    )
    
    class Meta:
        verbose_name = _('Fiche détenu')
        verbose_name_plural = _('Fiches détenus')
        ordering = ['-date_emission']
    
    def __str__(self):
        return f"Fiche {self.numero_fiche} - {self.detenu.nom_complet}"
    
    @property
    def est_valide(self):
        return self.statut_validation == 'VALIDE'
    
    def save(self, *args, **kwargs):
        if not self.numero_fiche:
            # Générer un numéro de fiche unique
            last_fiche = FicheDetenu.objects.order_by('-id').first()
            last_id = last_fiche.id if last_fiche else 0
            self.numero_fiche = f"FD{datetime.now().strftime('%Y%m%d')}{last_id + 1:04d}"
        super().save(*args, **kwargs)