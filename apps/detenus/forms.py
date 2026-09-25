from django import forms
from django.core.exceptions import ValidationError
from .models import Detenu, StatutDetenu, TypePeine, CentrePenitencier, CentrePhoto, AdminPrison, TypeCentre
from .juridictions import choix_tribunal
from .cellules import choix_cellules
from apps.comptes.models import Utilisateur, Role


class DetenuForm(forms.ModelForm):
    """Formulaire pour la gestion des détenus"""

    tribunal = forms.ChoiceField(
        label='Tribunal',
        choices=choix_tribunal(),
        widget=forms.Select(attrs={'class': 'form-control form-select'}),
    )
    cellule = forms.ChoiceField(
        label='Cellule',
        choices=choix_cellules(),
        widget=forms.Select(attrs={'class': 'form-control form-select'}),
    )

    class Meta:
        model = Detenu
        fields = [
            'centre', 'matricule', 'nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance',
            'nationalite', 'profession', 'adresse', 'telephone', 'date_arrestation',
            'date_incarceration', 'motif_incarceration', 'tribunal', 'numero_dossier',
            'dossier',
            'avocat', 'telephone_avocat', 'cellule', 'regime', 'statut',
            'duree_peine_mois', 'date_liberation_prevue', 'date_liberation_effective',
            'motif_liberation', 'groupe_sanguin', 'allergies', 'maladies_chroniques',
            # Données biométriques
            'taille', 'poids', 'couleur_yeux', 'couleur_cheveux', 'type_cheveux',
            'couleur_peau', 'cicatrices', 'photo_face', 'photo_profil',
            'empreintes_digitales', 'adn'
        ]
        widgets = {
            'centre': forms.Select(attrs={'class': 'form-control'}),
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_arrestation': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'date_incarceration': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'motif_incarceration': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'numero_dossier': forms.TextInput(attrs={'class': 'form-control'}),
            'dossier': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.odt,application/pdf',
            }),
            'avocat': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone_avocat': forms.TextInput(attrs={'class': 'form-control'}),
            'regime': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'duree_peine_mois': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_liberation_prevue': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'date_liberation_effective': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
            'motif_liberation': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'groupe_sanguin': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'maladies_chroniques': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'cicatrices': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # Données biométriques
            'taille': forms.NumberInput(attrs={'class': 'form-control', 'min': '100', 'max': '250'}),
            'poids': forms.NumberInput(attrs={'class': 'form-control', 'min': '20', 'max': '300', 'step': '0.1'}),
            'couleur_yeux': forms.Select(attrs={'class': 'form-control'}),
            'couleur_cheveux': forms.Select(attrs={'class': 'form-control'}),
            'type_cheveux': forms.Select(attrs={'class': 'form-control'}),
            'couleur_peau': forms.Select(attrs={'class': 'form-control'}),
            'photo_face': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'photo_profil': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'empreintes_digitales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Données encodées des empreintes digitales'}),
            'adn': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Profil ADN encodé'}),
        }

    DATE_FIELDS = (
        'date_naissance',
        'date_arrestation',
        'date_incarceration',
        'date_liberation_prevue',
        'date_liberation_effective',
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        tribunal_actuel = ''
        if self.instance and self.instance.pk:
            tribunal_actuel = self.instance.tribunal or ''
        self.fields['tribunal'].choices = choix_tribunal(tribunal_actuel)
        self.fields['tribunal'].widget.choices = self.fields['tribunal'].choices

        if self.user and hasattr(self.user, 'adminprison'):
            centre_user = self.user.adminprison.centre
            self.fields['centre'].queryset = CentrePenitencier.objects.filter(pk=centre_user.pk)
            self.fields['centre'].initial = centre_user

        centre = self._centre_courant()
        if not centre and self.user and hasattr(self.user, 'adminprison'):
            centre = self.user.adminprison.centre
        sexe = self._sexe_courant()
        cellule_actuelle = ''
        if self.instance and self.instance.pk:
            cellule_actuelle = self.instance.cellule or ''
        self.fields['cellule'].choices = choix_cellules(centre, sexe, cellule_actuelle)
        self.fields['cellule'].widget.choices = self.fields['cellule'].choices

        for name in self.DATE_FIELDS:
            field = self.fields[name]
            field.input_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
            if self.instance and self.instance.pk:
                value = getattr(self.instance, name, None)
                if value:
                    field.widget.attrs['value'] = value.strftime('%Y-%m-%d')

    def _centre_courant(self):
        raw = self.data.get('centre') if self.is_bound else None
        if not raw:
            if self.instance and getattr(self.instance, 'centre_id', None):
                return self.instance.centre
            initial = self.initial.get('centre')
            if initial and not isinstance(initial, CentrePenitencier):
                return CentrePenitencier.objects.filter(pk=initial).first()
            return initial
        return CentrePenitencier.objects.filter(pk=raw).first()

    def _sexe_courant(self):
        if self.is_bound:
            return self.data.get('sexe') or ''
        if self.instance and self.instance.pk:
            return self.instance.sexe or ''
        return self.initial.get('sexe') or ''

    def clean_cellule(self):
        from .models import Cellule
        code = self.cleaned_data.get('cellule')
        centre = self.cleaned_data.get('centre') or self._centre_courant()
        if not code:
            return code
        if centre and not Cellule.objects.filter(centre=centre, code=code, actif=True).exists():
            if self.instance and self.instance.pk and self.instance.cellule == code:
                return code
            raise ValidationError("Cette cellule n'appartient pas à la structure du centre sélectionné.")
        return code

    def clean_matricule(self):
        matricule = self.cleaned_data.get('matricule')
        if self.instance.pk:
            # Modification d'un détenu existant
            if Detenu.objects.filter(matricule=matricule).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Ce matricule existe déjà.")
        else:
            # Création d'un nouveau détenu
            if Detenu.objects.filter(matricule=matricule).exists():
                raise ValidationError("Ce matricule existe déjà.")
        return matricule

    def clean_date_liberation_prevue(self):
        date_liberation_prevue = self.cleaned_data.get('date_liberation_prevue')
        date_incarceration = self.cleaned_data.get('date_incarceration')
        
        if date_liberation_prevue and date_incarceration:
            if date_liberation_prevue <= date_incarceration:
                raise ValidationError(
                    "La date de libération prévue doit être postérieure à la date d'incarcération."
                )
        return date_liberation_prevue

    def clean_date_liberation_effective(self):
        date_liberation_effective = self.cleaned_data.get('date_liberation_effective')
        date_incarceration = self.cleaned_data.get('date_incarceration')
        
        if date_liberation_effective and date_incarceration:
            if date_liberation_effective <= date_incarceration:
                raise ValidationError(
                    "La date de libération effective doit être postérieure à la date d'incarcération."
                )
        return date_liberation_effective
    
    def clean_taille(self):
        taille = self.cleaned_data.get('taille')
        if taille and (taille < 100 or taille > 250):
            raise ValidationError("La taille doit être entre 100 et 250 cm.")
        return taille
    
    def clean_poids(self):
        poids = self.cleaned_data.get('poids')
        if poids and (poids < 20 or poids > 300):
            raise ValidationError("Le poids doit être entre 20 et 300 kg.")
        return poids
    
    def clean_photo_face(self):
        photo = self.cleaned_data.get('photo_face')
        if photo:
            # Vérifier si c'est un nouveau fichier uploadé
            if hasattr(photo, 'content_type'):
                # Nouveau fichier uploadé
                # Vérifier la taille du fichier (max 5MB)
                if photo.size > 5 * 1024 * 1024:
                    raise ValidationError("La photo ne doit pas dépasser 5MB.")
                # Vérifier le type de fichier
                if not photo.content_type.startswith('image/'):
                    raise ValidationError("Seuls les fichiers image sont autorisés.")
            # Si pas de content_type, c'est un fichier existant, pas de validation nécessaire
        return photo
    
    def clean_photo_profil(self):
        photo = self.cleaned_data.get('photo_profil')
        if photo:
            # Vérifier si c'est un nouveau fichier uploadé
            if hasattr(photo, 'content_type'):
                # Nouveau fichier uploadé
                # Vérifier la taille du fichier (max 5MB)
                if photo.size > 5 * 1024 * 1024:
                    raise ValidationError("La photo ne doit pas dépasser 5MB.")
                # Vérifier le type de fichier
                if not photo.content_type.startswith('image/'):
                    raise ValidationError("Seuls les fichiers image sont autorisés.")
            # Si pas de content_type, c'est un fichier existant, pas de validation nécessaire
        return photo

    def clean_dossier(self):
        dossier = self.cleaned_data.get('dossier')
        if dossier and hasattr(dossier, 'content_type'):
            if dossier.size > 10 * 1024 * 1024:
                raise ValidationError("Le dossier ne doit pas dépasser 10 Mo.")
            allowed = {
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.oasis.opendocument.text',
                'image/jpeg',
                'image/png',
                'image/jpg',
            }
            name = (dossier.name or '').lower()
            if dossier.content_type not in allowed and not name.endswith(
                ('.pdf', '.doc', '.docx', '.odt', '.jpg', '.jpeg', '.png')
            ):
                raise ValidationError("Formats acceptés : PDF, Word, ODT, JPEG, PNG.")
        return dossier
    
    def save(self, commit=True):
        detenu = super().save(commit=False)
        
        # Gérer la suppression des photos
        if self.data.get('photo_face_clear'):
            detenu.photo_face = None
        if self.data.get('photo_profil_clear'):
            detenu.photo_profil = None
        if self.data.get('dossier-clear') or self.data.get('dossier_clear'):
            detenu.dossier = None
        
        # Sauvegarder les fichiers uploadés manuellement
        if 'photo_face' in self.files:
            detenu.photo_face = self.files['photo_face']
        if 'photo_profil' in self.files:
            detenu.photo_profil = self.files['photo_profil']
        if 'dossier' in self.files:
            detenu.dossier = self.files['dossier']
            
        if commit:
            detenu.save()
        return detenu


class LiberationForm(forms.Form):
    """Formulaire pour la libération d'un détenu"""
    
    date_liberation = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    motif_liberation = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def __init__(self, detenu, *args, **kwargs):
        self.detenu = detenu
        super().__init__(*args, **kwargs)

    def clean_date_liberation(self):
        date_liberation = self.cleaned_data.get('date_liberation')
        if date_liberation and date_liberation <= self.detenu.date_incarceration:
            raise ValidationError(
                "La date de libération doit être postérieure à la date d'incarcération."
            )
        return date_liberation


class TransfertForm(forms.Form):
    """Formulaire pour le transfert d'un détenu"""
    
    destination = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    motif_transfert = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    date_transfert = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, detenu, *args, **kwargs):
        self.detenu = detenu
        super().__init__(*args, **kwargs)

    def clean_date_transfert(self):
        date_transfert = self.cleaned_data.get('date_transfert')
        if date_transfert and date_transfert <= self.detenu.date_incarceration:
            raise ValidationError(
                "La date de transfert doit être postérieure à la date d'incarcération."
            )
        return date_transfert


class RechercheDetenuForm(forms.Form):
    """Formulaire de recherche de détenus"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, prénom ou matricule...'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(StatutDetenu.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    regime = forms.ChoiceField(
        choices=[('', 'Tous les régimes')] + list(TypePeine.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sexe = forms.ChoiceField(
        choices=[('', 'Tous')] + [('M', 'Masculin'), ('F', 'Féminin')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    """Champ fichier acceptant plusieurs images."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data if item]
        cleaned = single_clean(data, initial)
        return [cleaned] if cleaned else []


class CentreForm(forms.ModelForm):
    """Formulaire pour la création et modification de centres"""

    photos = MultipleImageField(
        required=False,
        label='Photos du centre',
        help_text='Vous pouvez sélectionner plusieurs images (JPG, PNG, WebP — 5 Mo max chacune).',
    )
    
    class Meta:
        model = CentrePenitencier
        fields = [
            'nom', 'code', 'type_centre', 'adresse', 'province', 'ville',
            'latitude', 'longitude', 'telephone', 'email',
            'directeur', 'capacite_max', 'date_ouverture', 'statut'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Prison centrale de Makala',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: C001',
                'required': True
            }),
            'type_centre': forms.Select(attrs={
                'class': 'form-control form-select',
                'required': True
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète du centre...',
                'required': True
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Kinshasa'
            }),
            'ville': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Kinshasa'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0000001',
                'placeholder': '-4.3625000'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0000001',
                'placeholder': '15.2858333'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+243 XXX XXX XXX',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'contact@centre.example.com'
            }),
            'directeur': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom et prénom du directeur'
            }),
            'capacite_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Ex: 500',
                'required': True
            }),
            'date_ouverture': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }, format='%Y-%m-%d'),
            'statut': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if self.instance.pk:
            # Modification d'un centre existant
            if CentrePenitencier.objects.filter(code=code).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Ce code de centre existe déjà.")
        else:
            # Création d'un nouveau centre
            if CentrePenitencier.objects.filter(code=code).exists():
                raise ValidationError("Ce code de centre existe déjà.")
        return code
    
    def clean_capacite_max(self):
        capacite_max = self.cleaned_data.get('capacite_max')
        if capacite_max and capacite_max <= 0:
            raise ValidationError("La capacité maximale doit être supérieure à 0.")
        return capacite_max

    def clean_photos(self):
        photos = self.cleaned_data.get('photos') or []
        allowed = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')
        max_size = 5 * 1024 * 1024
        for photo in photos:
            content_type = getattr(photo, 'content_type', '') or ''
            if content_type and content_type not in allowed and not content_type.startswith('image/'):
                raise ValidationError("Seules les images sont acceptées.")
            if hasattr(photo, 'size') and photo.size > max_size:
                raise ValidationError("Chaque photo ne doit pas dépasser 5 Mo.")
        return photos

    def save(self, commit=True):
        centre = super().save(commit=commit)
        if commit:
            self._delete_photos(centre)
            self._save_photos(centre)
        return centre

    def _delete_photos(self, centre):
        ids = self.data.getlist('photos_a_supprimer')
        if not ids:
            return
        centre.photos.filter(pk__in=ids).delete()

    def _save_photos(self, centre):
        photos = self.cleaned_data.get('photos') or []
        start = centre.photos.count()
        for index, photo in enumerate(photos):
            CentrePhoto.objects.create(
                centre=centre,
                image=photo,
                ordre=start + index,
            )


class AdminPrisonForm(forms.Form):
    """Formulaire pour la création d'administrateurs de prison"""
    
    # Informations utilisateur
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: admin.makala',
            'required': True
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom',
            'required': True
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de famille',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@email.com',
            'required': True
        })
    )
    
    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+243 XXX XXX XXX'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 8 caractères',
            'required': True
        })
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe',
            'required': True
        })
    )
    
    # Informations administrateur
    centre = forms.ModelChoiceField(
        queryset=CentrePenitencier.objects.filter(statut=True),
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
            'required': True
        })
    )
    
    matricule_admin = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: ADM-2024-001',
            'required': True
        })
    )
    
    poste = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Directeur, Administrateur',
            'required': True
        })
    )
    
    date_affectation = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            ('ADMIN', 'Administrateur'),
            ('DIRECTEUR', 'Directeur'),
            ('AGENT', 'Agent')
        ],
        initial='ADMIN',
        widget=forms.Select(attrs={
            'class': 'form-control form-select'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Utilisateur.objects.filter(username=username).exists():
            raise ValidationError("Ce nom d'utilisateur existe déjà.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise ValidationError("Cet email existe déjà.")
        return email
    
    def clean_matricule_admin(self):
        matricule_admin = self.cleaned_data.get('matricule_admin')
        if AdminPrison.objects.filter(matricule_admin=matricule_admin).exists():
            raise ValidationError("Ce matricule d'administrateur existe déjà.")
        return matricule_admin
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Les mots de passe ne correspondent pas.")
        
        return cleaned_data
    
    def save(self):
        # Créer l'utilisateur
        utilisateur = Utilisateur.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            telephone=self.cleaned_data.get('telephone', ''),
            role=self.cleaned_data['role'],
            is_active=True,
            is_staff=True
        )
        
        # Créer l'administrateur de prison
        admin_prison = AdminPrison.objects.create(
            utilisateur=utilisateur,
            centre=self.cleaned_data['centre'],
            matricule_admin=self.cleaned_data['matricule_admin'],
            poste=self.cleaned_data['poste'],
            date_affectation=self.cleaned_data['date_affectation'],
            statut=True
        )
        
        return admin_prison
