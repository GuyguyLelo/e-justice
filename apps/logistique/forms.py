from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Fournisseur, Produit, Commande, LigneCommande, MouvementStock,
    TypeProduit, StatutCommande, UniteMesure
)


class FournisseurForm(forms.ModelForm):
    """Formulaire pour la gestion des fournisseurs"""
    
    class Meta:
        model = Fournisseur
        fields = [
            'nom', 'adresse', 'telephone', 'email', 'contact_principal',
            'specialite', 'est_actif'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_principal': forms.TextInput(attrs={'class': 'form-control'}),
            'specialite': forms.TextInput(attrs={'class': 'form-control'}),
            'est_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProduitForm(forms.ModelForm):
    """Formulaire pour la gestion des produits"""
    
    class Meta:
        model = Produit
        fields = [
            'nom', 'description', 'type_produit', 'unite_mesure', 'stock_actuel',
            'stock_minimum', 'stock_maximum', 'prix_unitaire', 'date_expiration',
            'fournisseur_principal'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'type_produit': forms.Select(attrs={'class': 'form-control'}),
            'unite_mesure': forms.Select(attrs={'class': 'form-control'}),
            'stock_actuel': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimum': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_maximum': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'date_expiration': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fournisseur_principal': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_stock_actuel(self):
        stock_actuel = self.cleaned_data.get('stock_actuel')
        if stock_actuel and stock_actuel < 0:
            raise ValidationError("Le stock ne peut pas être négatif.")
        return stock_actuel

    def clean_stock_minimum(self):
        stock_minimum = self.cleaned_data.get('stock_minimum')
        stock_maximum = self.cleaned_data.get('stock_maximum')
        
        if stock_minimum and stock_maximum and stock_minimum > stock_maximum:
            raise ValidationError(
                "Le stock minimum ne peut pas être supérieur au stock maximum."
            )
        return stock_minimum


class CommandeForm(forms.ModelForm):
    """Formulaire pour la gestion des commandes"""
    
    class Meta:
        model = Commande
        fields = [
            'fournisseur', 'date_commande', 'date_livraison_prevue',
            'observations'
        ]
        widgets = {
            'fournisseur': forms.Select(attrs={'class': 'form-control'}),
            'date_commande': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_livraison_prevue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_date_livraison_prevue(self):
        date_livraison_prevue = self.cleaned_data.get('date_livraison_prevue')
        date_commande = self.cleaned_data.get('date_commande')
        
        if date_livraison_prevue and date_commande and date_livraison_prevue <= date_commande:
            raise ValidationError(
                "La date de livraison prévue doit être postérieure à la date de commande."
            )
        return date_livraison_prevue


class LigneCommandeForm(forms.ModelForm):
    """Formulaire pour les lignes de commande"""
    
    class Meta:
        model = LigneCommande
        fields = [
            'produit', 'quantite_commandee', 'quantite_livree', 'prix_unitaire'
        ]
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'quantite_commandee': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantite_livree': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean_quantite_commandee(self):
        quantite_commandee = self.cleaned_data.get('quantite_commandee')
        if quantite_commandee and quantite_commandee <= 0:
            raise ValidationError("La quantité commandée doit être positive.")
        return quantite_commandee

    def clean_quantite_livree(self):
        quantite_livree = self.cleaned_data.get('quantite_livree')
        quantite_commandee = self.cleaned_data.get('quantite_commandee')
        
        if quantite_livree and quantite_commandee and quantite_livree > quantite_commandee:
            raise ValidationError(
                "La quantité livrée ne peut pas être supérieure à la quantité commandée."
            )
        return quantite_livree


class MouvementStockForm(forms.ModelForm):
    """Formulaire pour les mouvements de stock"""
    
    class Meta:
        model = MouvementStock
        fields = [
            'produit', 'type_mouvement', 'quantite', 'motif', 'reference'
        ]
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control'}),
            'type_mouvement': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'motif': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_quantite(self):
        quantite = self.cleaned_data.get('quantite')
        if quantite and quantite <= 0:
            raise ValidationError("La quantité doit être positive.")
        return quantite


class RechercheProduitForm(forms.Form):
    """Formulaire de recherche des produits"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom...'
        })
    )
    
    type_produit = forms.ChoiceField(
        choices=[('', 'Tous les types')] + list(TypeProduit.choices),
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


class RechercheCommandeForm(forms.Form):
    """Formulaire de recherche des commandes"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro ou fournisseur...'
        })
    )
    
    statut = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + list(StatutCommande.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fournisseur = forms.ModelChoiceField(
        queryset=Fournisseur.objects.all(),
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


class RechercheMouvementStockForm(forms.Form):
    """Formulaire de recherche des mouvements de stock"""
    
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    type_mouvement = forms.ChoiceField(
        choices=[
            ('', 'Tous les types'),
            ('ENTREE', 'Entrée'),
            ('SORTIE', 'Sortie'),
            ('AJUSTEMENT', 'Ajustement'),
            ('PERTE', 'Perte'),
        ],
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






