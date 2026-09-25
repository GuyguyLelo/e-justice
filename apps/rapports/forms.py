from django import forms
from django.core.exceptions import ValidationError
from .models import Rapport, ModeleRapport, TableauBord, TypeRapport, StatutRapport


class RapportForm(forms.ModelForm):
    """Formulaire pour la gestion des rapports"""
    
    class Meta:
        model = Rapport
        fields = [
            'nom', 'type_rapport', 'description', 'date_debut', 'date_fin',
            'parametres'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_rapport': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'parametres': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_date_fin(self):
        date_fin = self.cleaned_data.get('date_fin')
        date_debut = self.cleaned_data.get('date_debut')
        
        if date_fin and date_debut and date_fin < date_debut:
            raise ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return date_fin


class ModeleRapportForm(forms.ModelForm):
    """Formulaire pour la gestion des modèles de rapports"""
    
    class Meta:
        model = ModeleRapport
        fields = [
            'nom', 'type_rapport', 'description', 'template', 'parametres_defaut',
            'est_actif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_rapport': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'template': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'parametres_defaut': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'est_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TableauBordForm(forms.ModelForm):
    """Formulaire pour la gestion des tableaux de bord"""
    
    class Meta:
        model = TableauBord
        fields = [
            'nom', 'description', 'configuration', 'est_public'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'configuration': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'est_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RechercheRapportForm(forms.Form):
    """Formulaire de recherche des rapports"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom...'
        })
    )
    
    type_rapport = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(TypeRapport.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(StatutRapport.choices),
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


class GenerationRapportForm(forms.Form):
    """Formulaire pour la génération de rapports"""
    
    type_rapport = forms.ChoiceField(
        choices=TypeRapport.choices,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    nom = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    parametres = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

    def clean_date_fin(self):
        date_fin = self.cleaned_data.get('date_fin')
        date_debut = self.cleaned_data.get('date_debut')
        
        if date_fin and date_debut and date_fin < date_debut:
            raise ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return date_fin


class RechercheTableauBordForm(forms.Form):
    """Formulaire de recherche des tableaux de bord"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom...'
        })
    )
    
    est_public = forms.ChoiceField(
        choices=[
            ('', 'Tous'),
            ('True', 'Publics'),
            ('False', 'Privés'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class FiltreRapportForm(forms.Form):
    """Formulaire de filtrage pour les rapports"""
    
    # Filtres pour les détenus
    statut_detenu = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('INCARCERE', 'Incarcérés'),
            ('LIBERE', 'Libérés'),
            ('TRANSFERE', 'Transférés'),
            ('EVADE', 'Évadés'),
            ('DECEDE', 'Décédés'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    regime_detenu = forms.ChoiceField(
        choices=[
            ('', 'Tous les régimes'),
            ('PREVENTIF', 'Préventif'),
            ('CONDAMNE', 'Condamné'),
            ('AMENDE', 'Amende'),
            ('TRAVAUX_INTERET', 'Travaux d\'intérêt général'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtres pour le personnel
    type_personnel = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('DIRECTEUR', 'Directeur'),
            ('AGENT_SECURITE', 'Agent de sécurité'),
            ('AGENT_ADMINISTRATIF', 'Agent administratif'),
            ('MEDECIN', 'Médecin'),
            ('INFIRMIER', 'Infirmier'),
            ('PSYCHOLOGUE', 'Psychologue'),
            ('CUISINIER', 'Cuisinier'),
            ('NETTOYEUR', 'Agent de nettoyage'),
            ('GARDIEN', 'Gardien'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtres pour les visites
    statut_visite = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('PROGRAMMEE', 'Programmées'),
            ('EN_COURS', 'En cours'),
            ('TERMINEE', 'Terminées'),
            ('ANNULEE', 'Annulées'),
            ('REFUSEE', 'Refusées'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtres pour les consultations
    type_consultation = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('CONSULTATION_GENERALE', 'Consultation générale'),
            ('URGENCE', 'Urgence'),
            ('SUIVI_MEDICAL', 'Suivi médical'),
            ('VACCINATION', 'Vaccination'),
            ('EXAMEN_LABORATOIRE', 'Examen de laboratoire'),
            ('CONSULTATION_PSYCHOLOGIQUE', 'Consultation psychologique'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtres pour la logistique
    type_produit = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('NOURRITURE', 'Nourriture'),
            ('MEDICAMENT', 'Médicament'),
            ('VETEMENT', 'Vêtement'),
            ('LINGE', 'Linge'),
            ('MATERIEL_ENTRETIEN', 'Matériel d\'entretien'),
            ('MATERIEL_BUREAU', 'Matériel de bureau'),
            ('SECURITE', 'Sécurité'),
            ('AUTRE', 'Autre'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtres temporels
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )






