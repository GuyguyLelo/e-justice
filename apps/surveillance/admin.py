from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import (
    Camera, ZoneSurveillance, ProfilFacialDetenu, 
    DetectionFaciale, AlerteSurveillance, HistoriqueSurveillance
)


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = [
        'nom', 'code', 'centre', 'type_camera', 'emplacement', 
        'statut', 'detection_active', 'reconnaissance_faciale_active'
    ]
    list_filter = [
        'centre', 'type_camera', 'statut', 'detection_active', 
        'reconnaissance_faciale_active', 'qualite_detection'
    ]
    search_fields = ['nom', 'code', 'emplacement', 'centre__nom']
    readonly_fields = ['date_installation', 'created_at', 'updated_at']
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'code', 'centre', 'type_camera', 'emplacement', 'description')
        }),
        ('Configuration réseau', {
            'fields': ('adresse_ip', 'port', 'url_flux', 'resolution', 'fps')
        }),
        ('Statut et fonctionnalités', {
            'fields': ('statut', 'detection_active', 'reconnaissance_faciale_active', 'qualite_detection')
        }),
        ('Caractéristiques techniques', {
            'fields': ('angle_vue', 'portee_max')
        }),
        ('Maintenance', {
            'fields': ('derniere_maintenance',)
        }),
        ('Métadonnées', {
            'fields': ('date_installation', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('centre')


@admin.register(ZoneSurveillance)
class ZoneSurveillanceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'camera', 'type_zone', 'detection_active', 'seuil_alerte']
    list_filter = ['camera__centre', 'type_zone', 'detection_active']
    search_fields = ['nom', 'camera__nom', 'camera__centre__nom']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('camera', 'camera__centre')


@admin.register(ProfilFacialDetenu)
class ProfilFacialAdmin(admin.ModelAdmin):
    list_display = [
        'detenu', 'qualite_image', 'actif', 'date_enregistrement', 'created_by'
    ]
    list_filter = ['qualite_image', 'actif', 'date_enregistrement']
    search_fields = ['detenu__nom', 'detenu__prenom', 'detenu__matricule']
    readonly_fields = ['date_enregistrement', 'derniere_mise_a_jour']
    fieldsets = (
        ('Informations détenu', {
            'fields': ('detenu',)
        }),
        ('Profil facial', {
            'fields': ('image_reference', 'encodage_facial', 'qualite_image', 'actif')
        }),
        ('Métadonnées', {
            'fields': ('date_enregistrement', 'derniere_mise_a_jour', 'created_by')
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('detenu', 'created_by')


@admin.register(DetectionFaciale)
class DetectionFacialeAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'camera', 'detenu_info', 'confiance', 'est_alerte', 'traitee'
    ]
    list_filter = [
        'camera__centre', 'camera', 'est_alerte', 'traitee', 'timestamp'
    ]
    search_fields = [
        'detenu__nom', 'detenu__prenom', 'camera__nom', 'camera__centre__nom'
    ]
    readonly_fields = [
        'timestamp', 'created_at', 'coordonnees_visage', 'confiance'
    ]
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Informations de détection', {
            'fields': ('camera', 'zone', 'timestamp', 'image_detection')
        }),
        ('Identification', {
            'fields': ('detenu', 'confiance', 'coordonnees_visage')
        }),
        ('Alerte et traitement', {
            'fields': ('est_alerte', 'motif_alerte', 'traitee', 'traitee_par', 'date_traitement')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def detenu_info(self, obj):
        if obj.detenu:
            return format_html(
                '<span style="color: green;">{} {}</span>',
                obj.detenu.nom, obj.detenu.prenom
            )
        return format_html('<span style="color: red;">Non identifié</span>')
    detenu_info.short_description = 'Détenu'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'camera', 'camera__centre', 'detenu', 'zone', 'traitee_par'
        )


@admin.register(AlerteSurveillance)
class AlerteSurveillanceAdmin(admin.ModelAdmin):
    list_display = [
        'titre', 'type_alerte', 'niveau_badge', 'statut_badge', 
        'camera_info', 'detenu_info', 'date_creation'
    ]
    list_filter = [
        'type_alerte', 'niveau', 'statut', 'camera__centre', 'date_creation'
    ]
    search_fields = [
        'titre', 'description', 'camera__nom', 'detenu__nom', 'detenu__prenom'
    ]
    readonly_fields = ['date_creation', 'created_at', 'updated_at']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'type_alerte', 'niveau', 'description')
        }),
        ('Entités concernées', {
            'fields': ('camera', 'detection', 'detenu')
        }),
        ('Traitement', {
            'fields': ('statut', 'assigne_a', 'traitee_par', 'date_traitement', 'resolution')
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def niveau_badge(self, obj):
        colors = {
            'INFO': 'blue',
            'ATTENTION': 'orange', 
            'WARNING': 'red',
            'CRITIQUE': 'darkred'
        }
        color = colors.get(obj.niveau, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.get_niveau_display()
        )
    niveau_badge.short_description = 'Niveau'
    
    def statut_badge(self, obj):
        colors = {
            'OUVERTE': 'red',
            'EN_COURS': 'orange',
            'RESOLUE': 'green',
            'FAUSSE_ALERTE': 'gray'
        }
        color = colors.get(obj.statut, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
    
    def camera_info(self, obj):
        if obj.camera:
            return f"{obj.camera.nom} ({obj.camera.centre.nom})"
        return "-"
    camera_info.short_description = 'Caméra'
    
    def detenu_info(self, obj):
        if obj.detenu:
            return f"{obj.detenu.nom} {obj.detenu.prenom}"
        return "-"
    detenu_info.short_description = 'Détenu'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'camera', 'camera__centre', 'detection', 'detenu', 
            'assigne_a', 'traitee_par'
        )


@admin.register(HistoriqueSurveillance)
class HistoriqueSurveillanceAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'type_evenement', 'description_courte', 
        'camera_info', 'utilisateur_info'
    ]
    list_filter = ['type_evenement', 'timestamp', 'camera__centre']
    search_fields = ['description', 'camera__nom', 'utilisateur__username']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Événement', {
            'fields': ('type_evenement', 'description')
        }),
        ('Entités concernées', {
            'fields': ('camera', 'detection', 'alerte', 'utilisateur')
        }),
        ('Informations techniques', {
            'fields': ('adresse_ip', 'user_agent', 'donnees_supplementaires')
        }),
        ('Métadonnées', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        })
    )
    
    def description_courte(self, obj):
        return obj.description[:100] + "..." if len(obj.description) > 100 else obj.description
    description_courte.short_description = 'Description'
    
    def camera_info(self, obj):
        if obj.camera:
            return f"{obj.camera.nom} ({obj.camera.centre.nom})"
        return "-"
    camera_info.short_description = 'Caméra'
    
    def utilisateur_info(self, obj):
        if obj.utilisateur:
            return obj.utilisateur.get_full_name() or obj.utilisateur.username
        return "-"
    utilisateur_info.short_description = 'Utilisateur'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'camera', 'camera__centre', 'detection', 'alerte', 'utilisateur'
        )


# Configuration du dashboard admin
class SurveillanceAdminSite(admin.AdminSite):
    site_header = "Administration e-Detenu - Surveillance"
    site_title = "Surveillance et Reconnaissance Faciale"
    index_title = "Tableau de bord de surveillance"
