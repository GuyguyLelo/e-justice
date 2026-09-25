from django import forms
from django.core.exceptions import ValidationError
from .models import Visiteur, Visite, ObjetVisite, TypeVisiteur, StatutVisite
from apps.detenus.models import Detenu


class VisiteurForm(forms.ModelForm):
    """Formulaire pour la gestion des visiteurs"""
    
    class Meta:
        model = Visiteur
        fields = [
            'nom', 'prenom', 'type_visiteur', 'piece_identite', 'numero_piece',
            'telephone', 'adresse', 'relation_detenu', 'cabinet_avocat',
            'numero_ordre_avocat', 'photo',
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de famille'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'type_visiteur': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'piece_identite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Carte d\'identité, Passeport'
            }),
            'numero_piece': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro de la pièce d\'identité'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+243 XXX XXX XXX'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète du visiteur...'
            }),
            'relation_detenu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Père, Mère, Avocat, Ami'
            }),
            'cabinet_avocat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du cabinet d\'avocat'
            }),
            'numero_ordre_avocat': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro d\'ordre de l\'avocat'
            }),
            'photo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'size'):
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("La photo ne doit pas dépasser 5 Mo.")
            content_type = getattr(photo, 'content_type', '') or ''
            if content_type and not content_type.startswith('image/'):
                raise ValidationError("Seules les images sont acceptées.")
        return photo


class VisiteForm(forms.ModelForm):
    """Formulaire pour la gestion des visites"""

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'adminprison'):
            self.fields['detenu'].queryset = Detenu.objects.filter(
                centre=user.adminprison.centre
            )
        elif user and user.is_admin_central():
            self.fields['detenu'].queryset = Detenu.objects.all()
        else:
            self.fields['detenu'].queryset = Detenu.objects.none()

        self.fields['date_visite'].input_formats = [
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
        ]
        self.fields['agent_controle'].required = False
        self.fields['agent_controle'].empty_label = '—'

        if self.instance and self.instance.pk and self.instance.date_visite:
            self.fields['date_visite'].widget.attrs['value'] = (
                self.instance.date_visite.strftime('%Y-%m-%dT%H:%M')
            )
        elif not self.instance.pk:
            from datetime import timedelta
            from django.utils import timezone
            start = (timezone.now() + timedelta(hours=1)).replace(
                minute=0, second=0, microsecond=0
            )
            self.initial.setdefault('date_visite', start)
            self.initial.setdefault('duree_minutes', 30)
            self.fields['date_visite'].widget.attrs['value'] = start.strftime('%Y-%m-%dT%H:%M')

    class Meta:
        model = Visite
        fields = [
            'detenu', 'visiteur', 'date_visite', 'duree_minutes', 'statut',
            'motif_refus', 'objets_apportes', 'objets_autorises', 'objets_refuses',
            'agent_controle', 'observations',
        ]
        widgets = {
            'detenu': forms.Select(attrs={'class': 'form-control form-select'}),
            'visiteur': forms.Select(attrs={'class': 'form-control form-select'}),
            'date_visite': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
            'duree_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '30',
                'min': 15,
                'max': 180,
            }),
            'statut': forms.Select(attrs={'class': 'form-control form-select'}),
            'motif_refus': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Raison du refus…',
            }),
            'objets_apportes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Objets apportés…',
            }),
            'objets_autorises': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Objets autorisés…',
            }),
            'objets_refuses': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Objets refusés…',
            }),
            'agent_controle': forms.Select(attrs={'class': 'form-control form-select'}),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observations…',
            }),
        }

    def clean_date_visite(self):
        from django.utils import timezone
        date_visite = self.cleaned_data.get('date_visite')
        if self.instance and self.instance.pk:
            return date_visite
        if date_visite and date_visite < timezone.now():
            raise ValidationError("La date de visite ne peut pas être dans le passé.")
        return date_visite

    def clean_duree_minutes(self):
        duree_minutes = self.cleaned_data.get('duree_minutes')
        if duree_minutes and (duree_minutes < 15 or duree_minutes > 180):
            raise ValidationError("La durée doit être entre 15 et 180 minutes.")
        return duree_minutes


class ObjetVisiteForm(forms.ModelForm):
    """Formulaire pour les objets de visite"""
    
    class Meta:
        model = ObjetVisite
        fields = ['nom_objet', 'quantite', 'autorise', 'motif_refus']
        widgets = {
            'nom_objet': forms.TextInput(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'autorise': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'motif_refus': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RechercheVisiteForm(forms.Form):
    """Formulaire de recherche des visites"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par détenu ou visiteur...'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(StatutVisite.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    type_visiteur = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(TypeVisiteur.choices),
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


class PlanificationVisiteForm(forms.Form):
    """Formulaire pour planifier une visite"""
    
    detenu = forms.ModelChoiceField(
        queryset=Detenu.objects.filter(statut='INCARCERE'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    visiteur = forms.ModelChoiceField(
        queryset=Visiteur.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_visite = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'})
    )
    
    duree_minutes = forms.IntegerField(
        initial=30,
        min_value=15,
        max_value=180,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    objets_apportes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    observations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    def clean_date_visite(self):
        from django.utils import timezone
        date_visite = self.cleaned_data.get('date_visite')
        if date_visite and date_visite < timezone.now():
            raise ValidationError("La date de visite ne peut pas être dans le passé.")
        return date_visite


class ControleVisiteForm(forms.Form):
    """Formulaire pour contrôler une visite"""
    
    statut = forms.ChoiceField(
        choices=[
            ('EN_COURS', 'En cours'),
            ('TERMINEE', 'Terminée'),
            ('ANNULEE', 'Annulée'),
            ('REFUSEE', 'Refusée'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    objets_autorises = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    objets_refuses = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    motif_refus = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    observations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )





