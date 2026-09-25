from django.contrib import admin
from .models import Detenu, HistoriqueDetenu, Cellule


@admin.register(Detenu)
class DetenuAdmin(admin.ModelAdmin):
    """Administration des détenus"""
    
    list_display = ('matricule', 'nom', 'prenom', 'sexe', 'age', 'cellule', 'statut', 'date_incarceration')
    list_filter = ('sexe', 'statut', 'regime', 'date_incarceration', 'created_at')
    search_fields = ('matricule', 'nom', 'prenom', 'numero_dossier')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance', 'nationalite', 'profession', 'adresse', 'telephone')
        }),
        ('Informations judiciaires', {
            'fields': ('date_arrestation', 'date_incarceration', 'motif_incarceration', 'tribunal', 'numero_dossier', 'dossier', 'avocat', 'telephone_avocat')
        }),
        ('Informations pénitentiaires', {
            'fields': ('cellule', 'regime', 'statut', 'duree_peine_mois', 'date_liberation_prevue', 'date_liberation_effective', 'motif_liberation')
        }),
        ('Informations médicales', {
            'fields': ('groupe_sanguin', 'allergies', 'maladies_chroniques')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def age(self, obj):
        return obj.age
    age.short_description = 'Âge'


@admin.register(HistoriqueDetenu)
class HistoriqueDetenuAdmin(admin.ModelAdmin):
    """Administration de l'historique des détenus"""
    
    list_display = ('detenu', 'action', 'utilisateur', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('detenu__nom', 'detenu__prenom', 'action')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)


@admin.register(Cellule)
class CelluleAdmin(admin.ModelAdmin):
    list_display = ('code', 'centre', 'pavillon', 'nom_pavillon', 'type_population', 'capacite', 'actif')
    list_filter = ('centre', 'pavillon', 'type_population', 'actif')
    search_fields = ('code', 'pavillon', 'nom_pavillon')
    ordering = ('centre', 'pavillon', 'code')