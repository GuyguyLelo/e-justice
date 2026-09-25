from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PersonnelViewSet, FormationPersonnelViewSet, SanctionPersonnelViewSet
from .views_web import (
    personnel_list_view, personnel_detail_view, personnel_create_view, 
    personnel_edit_view, personnel_delete_view, formation_create_view,
    sanction_create_view, api_personnel_search, api_personnel_action
)

router = DefaultRouter()
router.register(r'personnel', PersonnelViewSet)
router.register(r'formations', FormationPersonnelViewSet)
router.register(r'sanctions', SanctionPersonnelViewSet)

urlpatterns = [
    # API Routes
    path('', include(router.urls)),
    
    # Web Routes - Personnel
    path('web/personnel/', personnel_list_view, name='personnel_list'),
    path('web/personnel/nouveau/', personnel_create_view, name='personnel_create'),
    path('web/personnel/<int:personnel_id>/', personnel_detail_view, name='personnel_detail'),
    path('web/personnel/<int:personnel_id>/modifier/', personnel_edit_view, name='personnel_edit'),
    path('web/personnel/<int:personnel_id>/supprimer/', personnel_delete_view, name='personnel_delete'),
    
    # Web Routes - Formations
    path('web/personnel/<int:personnel_id>/formation/', formation_create_view, name='formation_create'),
    
    # Web Routes - Sanctions
    path('web/personnel/<int:personnel_id>/sanction/', sanction_create_view, name='sanction_create'),
    
    # API endpoints
    path('api/personnel/search/', api_personnel_search, name='api_personnel_search'),
    path('api/personnel/<int:personnel_id>/action/', api_personnel_action, name='api_personnel_action'),
]




