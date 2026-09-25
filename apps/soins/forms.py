from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Consultation, Medicament, Prescription, AntecedentMedical, Vaccination,
    TypeConsultation, StatutConsultation, TypeMedicament
)
from apps.detenus.models import Detenu
from apps.comptes.models import Utilisateur


class ConsultationForm(forms.ModelForm):
    """Formulaire pour les consultations médicales"""
    
    class Meta:
        model = Consultation
        fields = [
            'detenu', 'medecin', 'type_consultation', 'date_consultation', 'statut',
            'symptomes', 'diagnostic', 'traitement_prescrit', 'recommandations',
            'date_controle', 'urgence'
        ]
        widgets = {
            'detenu': forms.Select(attrs={'class': 'form-control'}),
            'medecin': forms.Select(attrs={'class': 'form-control'}),
            'type_consultation': forms.Select(attrs={'class': 'form-control'}),
            'date_consultation': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'symptomes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'diagnostic': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'traitement_prescrit': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recommandations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_controle': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'urgence': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les médecins
        self.fields['medecin'].queryset = Utilisateur.objects.filter(role='MEDECIN')
        # Filtrer les détenus incarcérés
        self.fields['detenu'].queryset = Detenu.objects.filter(statut='INCARCERE')

    def clean_date_consultation(self):
        from datetime import datetime
        date_consultation = self.cleaned_data.get('date_consultation')
        if date_consultation and date_consultation > datetime.now():
            raise ValidationError("La date de consultation ne peut pas être dans le futur.")
        return date_consultation


class MedicamentForm(forms.ModelForm):
    """Formulaire pour la gestion des médicaments"""
    
    class Meta:
        model = Medicament
        fields = [
            'nom', 'nom_commercial', 'type_medicament', 'forme_pharmaceutique',
            'dosage', 'stock_actuel', 'stock_minimum',
            'prix_unitaire', 'date_expiration'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'nom_commercial': forms.TextInput(attrs={'class': 'form-control'}),
            'type_medicament': forms.Select(attrs={'class': 'form-control'}),
            'forme_pharmaceutique': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_actuel': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimum': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_expiration': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_stock_actuel(self):
        stock_actuel = self.cleaned_data.get('stock_actuel')
        if stock_actuel and stock_actuel < 0:
            raise ValidationError("Le stock ne peut pas être négatif.")
        return stock_actuel

    def clean_stock_minimum(self):
        stock_minimum = self.cleaned_data.get('stock_minimum')
        stock_actuel = self.cleaned_data.get('stock_actuel')
        
        if stock_minimum and stock_actuel and stock_minimum > stock_actuel:
            raise ValidationError(
                "Le stock minimum ne peut pas être supérieur au stock actuel."
            )
        return stock_minimum


class PrescriptionForm(forms.ModelForm):
    """Formulaire pour les prescriptions médicales"""
    
    class Meta:
        model = Prescription
        fields = [
            'consultation', 'medicament', 'posologie', 'duree_jours',
            'quantite_prescrit', 'instructions'
        ]
        widgets = {
            'consultation': forms.Select(attrs={'class': 'form-control'}),
            'medicament': forms.Select(attrs={'class': 'form-control'}),
            'posologie': forms.TextInput(attrs={'class': 'form-control'}),
            'duree_jours': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantite_prescrit': forms.NumberInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AntecedentMedicalForm(forms.ModelForm):
    """Formulaire pour les antécédents médicaux"""
    
    class Meta:
        model = AntecedentMedical
        fields = [
            'detenu', 'type_antecedent', 'description', 'date_debut',
            'date_fin', 'traitement_suivi'
        ]
        widgets = {
            'detenu': forms.Select(attrs={'class': 'form-control'}),
            'type_antecedent': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'traitement_suivi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les détenus incarcérés
        self.fields['detenu'].queryset = Detenu.objects.filter(statut='INCARCERE')

    def clean_date_fin(self):
        date_fin = self.cleaned_data.get('date_fin')
        date_debut = self.cleaned_data.get('date_debut')
        
        if date_fin and date_debut and date_fin <= date_debut:
            raise ValidationError(
                "La date de fin doit être postérieure à la date de début."
            )
        return date_fin


class VaccinationForm(forms.ModelForm):
    """Formulaire pour les vaccinations"""
    
    class Meta:
        model = Vaccination
        fields = [
            'detenu', 'nom_vaccin', 'date_vaccination', 'lot_vaccin',
            'medecin_vaccinateur', 'effets_secondaires'
        ]
        widgets = {
            'detenu': forms.Select(attrs={'class': 'form-control'}),
            'nom_vaccin': forms.TextInput(attrs={'class': 'form-control'}),
            'date_vaccination': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lot_vaccin': forms.TextInput(attrs={'class': 'form-control'}),
            'medecin_vaccinateur': forms.Select(attrs={'class': 'form-control'}),
            'effets_secondaires': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les médecins
        self.fields['medecin_vaccinateur'].queryset = Utilisateur.objects.filter(role='MEDECIN')
        # Filtrer les détenus incarcérés
        self.fields['detenu'].queryset = Detenu.objects.filter(statut='INCARCERE')


class RechercheConsultationForm(forms.Form):
    """Formulaire de recherche des consultations"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par détenu ou médecin...'
        })
    )
    
    type_consultation = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(TypeConsultation.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(StatutConsultation.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    urgence = forms.ChoiceField(
        choices=[('', 'Toutes'), ('True', 'Urgences'), ('False', 'Non urgentes')],
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


class RechercheMedicamentForm(forms.Form):
    """Formulaire de recherche des médicaments"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom...'
        })
    )
    
    type_medicament = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(TypeMedicament.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    stock_faible = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    expire = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
