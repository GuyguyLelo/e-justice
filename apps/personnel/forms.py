from django import forms
from django.core.exceptions import ValidationError
from .models import Personnel, FormationPersonnel, SanctionPersonnel, TypePersonnel, StatutPersonnel
from apps.comptes.models import Utilisateur


class PersonnelForm(forms.ModelForm):
    """Formulaire pour la gestion du personnel"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = Personnel
        fields = [
            'nom', 'prenom', 'telephone', 'email', 'matricule', 'type_personnel', 'statut', 'date_embauche',
            'date_fin_contrat', 'salaire', 'specialite', 'numero_ordre',
            'heures_travail_semaine', 'contact_urgence_nom', 'contact_urgence_telephone',
            'contact_urgence_relation'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du personnel'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom du personnel'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
            'matricule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: PER-2024-001'
            }),
            'type_personnel': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'statut': forms.Select(attrs={
                'class': 'form-control form-select'
            }),
            'date_embauche': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_fin_contrat': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'salaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Ex: 500.00'
            }),
            'specialite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Médecin, Psychologue, Éducateur'
            }),
            'numero_ordre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Numéro d\'ordre professionnel'
            }),
            'heures_travail_semaine': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 40',
                'min': 1,
                'max': 80
            }),
            'contact_urgence_nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du contact d\'urgence'
            }),
            'contact_urgence_telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+243 XXX XXX XXX'
            }),
            'contact_urgence_relation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Conjoint, Parent, Ami'
            }),
        }

    def clean_matricule(self):
        matricule = self.cleaned_data.get('matricule')
        if self.instance.pk:
            if Personnel.objects.filter(matricule=matricule).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Ce matricule existe déjà.")
        else:
            if Personnel.objects.filter(matricule=matricule).exists():
                raise ValidationError("Ce matricule existe déjà.")
        return matricule

    def clean_date_fin_contrat(self):
        date_fin_contrat = self.cleaned_data.get('date_fin_contrat')
        date_embauche = self.cleaned_data.get('date_embauche')
        
        if date_fin_contrat and date_embauche:
            if date_fin_contrat <= date_embauche:
                raise ValidationError(
                    "La date de fin de contrat doit être postérieure à la date d'embauche."
                )
        return date_fin_contrat
        date_embauche = self.cleaned_data.get('date_embauche')
        
        if date_fin_contrat and date_embauche:
            if date_fin_contrat <= date_embauche:
                raise ValidationError(
                    "La date de fin de contrat doit être postérieure à la date d'embauche."
                )
        return date_fin_contrat


class FormationPersonnelForm(forms.ModelForm):
    """Formulaire pour les formations du personnel"""
    
    class Meta:
        model = FormationPersonnel
        fields = [
            'personnel', 'nom_formation', 'organisme', 'date_debut', 'date_fin',
            'duree_heures', 'certificat'
        ]
        widgets = {
            'personnel': forms.Select(attrs={'class': 'form-control'}),
            'nom_formation': forms.TextInput(attrs={'class': 'form-control'}),
            'organisme': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duree_heures': forms.NumberInput(attrs={'class': 'form-control'}),
            'certificat': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_date_fin(self):
        date_fin = self.cleaned_data.get('date_fin')
        date_debut = self.cleaned_data.get('date_debut')
        
        if date_fin and date_debut:
            if date_fin <= date_debut:
                raise ValidationError(
                    "La date de fin doit être postérieure à la date de début."
                )
        return date_fin


class SanctionPersonnelForm(forms.ModelForm):
    """Formulaire pour les sanctions du personnel"""
    
    class Meta:
        model = SanctionPersonnel
        fields = [
            'personnel', 'type_sanction', 'motif', 'date_sanction', 'duree_jours',
            'sanctionne_par'
        ]
        widgets = {
            'personnel': forms.Select(attrs={'class': 'form-control'}),
            'type_sanction': forms.TextInput(attrs={'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_sanction': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duree_jours': forms.NumberInput(attrs={'class': 'form-control'}),
            'sanctionne_par': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les utilisateurs qui peuvent appliquer des sanctions
        self.fields['sanctionne_par'].queryset = Utilisateur.objects.filter(
            role__in=['ADMIN', 'DIRECTEUR']
        )


class RecherchePersonnelForm(forms.Form):
    """Formulaire de recherche du personnel"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, prénom ou matricule...'
        })
    )
    
    type_personnel = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(TypePersonnel.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(StatutPersonnel.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_embauche_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_embauche_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class UtilisateurPersonnelForm(forms.ModelForm):
    """Formulaire pour créer un utilisateur et l'associer au personnel"""
    
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    telephone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    adresse = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Personnel
        fields = [
            'matricule', 'type_personnel', 'statut', 'date_embauche',
            'date_fin_contrat', 'salaire', 'specialite', 'numero_ordre',
            'heures_travail_semaine', 'contact_urgence_nom', 'contact_urgence_telephone',
            'contact_urgence_relation'
        ]
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control'}),
            'type_personnel': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_contrat': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'specialite': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_ordre': forms.TextInput(attrs={'class': 'form-control'}),
            'heures_travail_semaine': forms.NumberInput(attrs={'class': 'form-control'}),
            'contact_urgence_nom': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_urgence_telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_urgence_relation': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        # Créer l'utilisateur d'abord
        user = Utilisateur.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password='password123',  # Mot de passe par défaut
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            telephone=self.cleaned_data['telephone'],
            adresse=self.cleaned_data['adresse'],
            role='AGENT'  # Rôle par défaut
        )
        
        # Créer le personnel
        personnel = super().save(commit=False)
        personnel.utilisateur = user
        
        if commit:
            personnel.save()
        
        return personnel






