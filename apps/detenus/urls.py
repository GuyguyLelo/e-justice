from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DetenuViewSet, CentrePenitencierViewSet, AdminPrisonViewSet,
    biometric_update_view, create_test_data_view
)
from .views_simple import biometric_update_simple
from .views_web import (
    detenus_list_view, detenu_detail_view, detenu_create_view,
    detenu_edit_view, detenu_delete_view, detenu_liberation_view,
    detenu_transfert_view, detenu_stats_view, api_detenu_search,
    api_detenu_quick_action, biometric_capture_view, dashboard_central_view,
    centres_list_view, admins_prison_list_view, admin_prison_detail_view,
    admin_prison_edit_view, admin_prison_toggle_status_view,
    centre_dashboard_view, centre_create_view, centre_edit_view,
    generer_liste_detenus_centre, generer_fiche_detenu
)

router = DefaultRouter()
router.register(r'detenus', DetenuViewSet)
router.register(r'centres', CentrePenitencierViewSet)
router.register(r'admins-prison', AdminPrisonViewSet)

urlpatterns = [
    # Web URLs (prioritaires pour éviter les conflits avec l'API)
    path('web/', detenus_list_view, name='detenus_list'),
    path('web/list/', detenus_list_view, name='detenus_list_alt'),
    path('web/index/', detenus_list_view, name='detenus_list_index'),
    path('web/<int:detenu_id>/', detenu_detail_view, name='detenu_detail'),
    path('web/<int:detenu_id>/fiche/', generer_fiche_detenu, name='generer_fiche_detenu'),
    path('web/nouveau/', detenu_create_view, name='detenu_create'),
    path('web/<int:detenu_id>/modifier/', detenu_edit_view, name='detenu_edit'),
    path('web/<int:detenu_id>/supprimer/', detenu_delete_view, name='detenu_delete'),
    path('web/<int:detenu_id>/liberation/', detenu_liberation_view, name='detenu_liberation'),
    path('web/<int:detenu_id>/transfert/', detenu_transfert_view, name='detenu_transfert'),
    path('web/statistiques/', detenu_stats_view, name='detenu_stats'),
    path('web/biometric-capture/', biometric_capture_view, name='biometric_capture'),
    
    # Dashboard et gestion des prisons
    path('web/dashboard-central/', dashboard_central_view, name='dashboard_central'),
    path('web/centres/', centres_list_view, name='centres_list'),
    path('web/centres/<int:centre_id>/', centre_dashboard_view, name='centre_dashboard'),
    path('web/centres/<int:centre_id>/modifier/', centre_edit_view, name='centre_edit'),
    path('web/centres/<int:centre_id>/detenus/', detenus_list_view, name='centre_detenus_list'),
    path('web/centres/<int:centre_id>/generer-liste/', generer_liste_detenus_centre, name='generer_liste_detenus_centre'),
    path('web/admins-prison/', admins_prison_list_view, name='admins_prison_list'),
    path('web/admins-prison/<int:admin_id>/', admin_prison_detail_view, name='admin_prison_detail'),
    path('web/admins-prison/<int:admin_id>/modifier/', admin_prison_edit_view, name='admin_prison_edit'),
    path('web/admins-prison/<int:admin_id>/toggle-status/', admin_prison_toggle_status_view, name='admin_prison_toggle_status'),
    
    # API endpoints
    path('search/', api_detenu_search, name='api_detenu_search'),
    path('<int:detenu_id>/action/', api_detenu_quick_action, name='api_detenu_quick_action'),
    path('<int:detenu_id>/biometric-update/', biometric_update_view, name='api_biometric_update'),
    path('<int:detenu_id>/biometric-update-simple/', biometric_update_simple, name='api_biometric_update_simple'),
    path('create-test-data/', create_test_data_view, name='create_test_data'),
    
    # API URLs (en dernier pour éviter les conflits)
    path('', include(router.urls)),
]
