from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    """Administration des utilisateurs"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'est_actif', 'date_joined')
    list_filter = ('role', 'est_actif', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'telephone', 'adresse')}),
        ('Rôle et permissions', {'fields': ('role', 'is_active', 'est_actif', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Informations professionnelles', {'fields': ('date_embauche', 'photo')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')