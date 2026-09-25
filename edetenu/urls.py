from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.http import JsonResponse

# Import des vues API
from apps.surveillance.api_simple import initialiser_systeme_simple, detecter_visage_simple
from apps.surveillance import views_web
from apps.visites.views_web import suivi_visiteur_view
from apps.detenus.views_simple import biometric_update_simple
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .views import api_info, accueil_view
from apps.comptes.views_auth import (
    login_view, logout_view, dashboard_view, profile_view, 
    change_password_view, register_view, admin_users_view,
    api_login, api_logout
)
from apps.detenus.views_web import (
    detenus_list_view, detenu_detail_view, detenu_create_view,
    detenu_edit_view, detenu_delete_view, detenu_liberation_view,
    detenu_transfert_view, detenu_stats_view, api_detenu_search,
    api_detenu_quick_action, download_photo_view, download_dossier_view, biometric_capture_view,
    centres_list_view, admins_prison_list_view, centre_create_view, centre_edit_view, admin_prison_create_view,
    api_cellules_centre
)

urlpatterns = [
    path('', accueil_view, name='accueil'),
    path('accounts/login/', login_view, name='accounts_login'),
    
    # Authentification
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('profile/', profile_view, name='profile'),
    path('change-password/', change_password_view, name='change_password'),
    path('register/', register_view, name='register'),
    path('admin-users/', admin_users_view, name='admin_users'),
    
    # API d'authentification
    path('api/login/', api_login, name='api_login'),
    path('api/logout/', api_logout, name='api_logout'),
    
    # Gestion des détenus
    path('detenus/', detenus_list_view, name='detenus_list'),
    path('detenus/nouveau/', detenu_create_view, name='detenu_create'),
    path('detenus/<int:detenu_id>/', detenu_detail_view, name='detenu_detail'),
    path('detenus/<int:detenu_id>/modifier/', detenu_edit_view, name='detenu_edit'),
    path('detenus/<int:detenu_id>/supprimer/', detenu_delete_view, name='detenu_delete'),
    path('detenus/<int:detenu_id>/liberer/', detenu_liberation_view, name='detenu_liberation'),
    path('detenus/<int:detenu_id>/transférer/', detenu_transfert_view, name='detenu_transfert'),
    path('detenus/<int:detenu_id>/biometric-update-simple/', biometric_update_simple, name='biometric_update_simple'),
    path('detenus/statistiques/', detenu_stats_view, name='detenu_stats'),
    
    # Gestion des visites (interface web personnalisée)
    path('visites/', include('apps.visites.urls')),
    
    # Gestion du personnel (interface web personnalisée)
    path('personnel/', include('apps.personnel.urls')),
    
    # Gestion de la surveillance (interface web) - COMMENTÉ pour éviter les menus inutiles
    # path('surveillance/', include('apps.surveillance.urls_web')),
    
    # Surveillance professionnelle finale UNIQUEMENT
    path('surveillance/', lambda request: render(request, 'surveillance_pro_final.html'), name='surveillance_pro_final'),
    
    # Pages de surveillance avec filtres
    path('surveillance/detections/', views_web.detections_list, name='surveillance_detections_list'),
    path('surveillance/detections/<int:detection_id>/image/', views_web.detection_image_view, name='surveillance_detection_image'),
    path('surveillance/detections/<int:detection_id>/', views_web.detection_detail_view, name='surveillance_detection_detail'),
    
    # API Surveillance (directe pour éviter les menus)
    path('surveillance/api/initialiser-systeme/', initialiser_systeme_simple, name='api_surveillance_initialiser'),
    path('surveillance/api/detecter-visage/', detecter_visage_simple, name='api_surveillance_detecter'),
    
    # API des détenus
    path('detenus/api/cellules/', api_cellules_centre, name='api_cellules_centre'),
    path('api/detenus/cellules/', api_cellules_centre),
    path('api/detenus/search/', api_detenu_search, name='api_detenu_search'),
    path('api/detenus/<int:detenu_id>/action/', api_detenu_quick_action, name='api_detenu_quick_action'),
    
    # Téléchargement des photos
    path('detenus/<int:detenu_id>/photo/<str:photo_type>/', download_photo_view, name='download_photo'),
    path('detenus/<int:detenu_id>/dossier/', download_dossier_view, name='download_dossier'),
    
    # Capture biométrique
    path('biometric-capture/', biometric_capture_view, name='biometric_capture'),
    
    # Gestion des centres et administrateurs (admin central)
    path('centres/', centres_list_view, name='centres_list'),
    path('centres/creer/', centre_create_view, name='centre_create'),
    path('centres/<int:centre_id>/modifier/', centre_edit_view, name='centre_edit'),
    path('admins-prison/', admins_prison_list_view, name='admins_prison_list'),
    path('admins-prison/creer/', admin_prison_create_view, name='admin_prison_create'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation (temporairement désactivé)
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Routes
    path('api/auth/', include('apps.comptes.urls')),
    path('api/detenus/', include('apps.detenus.urls')),
    path('api/personnel/', include('apps.personnel.urls')),
    # Visites gérées uniquement via API REST (retirées de l'admin Django)
    path('api/visites/', include('apps.visites.urls')),
    path('suivi-visiteur/', suivi_visiteur_view, name='suivi_visiteur'),
    path('api/soins/', include('apps.soins.urls')),
    path('api/logistique/', include('apps.logistique.urls')),
    path('api/rapports/', include('apps.rapports.urls')),
    path('api/surveillance/', include('apps.surveillance.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)