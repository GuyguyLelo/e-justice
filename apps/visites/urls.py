from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VisiteurViewSet, VisiteViewSet
from .views_web import (
    visiteurs_list_view, visiteur_detail_view, visiteur_create_view, 
    visiteur_edit_view, visites_list_view, visite_detail_view, 
    visite_create_view, visite_edit_view, visite_delete_view,
    api_visiteur_search, api_visite_action
)

router = DefaultRouter()
router.register(r'visiteurs', VisiteurViewSet)
router.register(r'visites', VisiteViewSet)

urlpatterns = [
    # API Routes
    path('', include(router.urls)),
    
    # Web Routes - Visiteurs
    path('web/visiteurs/', visiteurs_list_view, name='visiteurs_list'),
    path('web/visiteurs/nouveau/', visiteur_create_view, name='visiteur_create'),
    path('web/visiteurs/<int:visiteur_id>/', visiteur_detail_view, name='visiteur_detail'),
    path('web/visiteurs/<int:visiteur_id>/modifier/', visiteur_edit_view, name='visiteur_edit'),
    
    # Web Routes - Visites
    path('web/visites/', visites_list_view, name='visites_list'),
    path('web/visites/nouvelle/', visite_create_view, name='visite_create'),
    path('web/visites/<int:visite_id>/', visite_detail_view, name='visite_detail'),
    path('web/visites/<int:visite_id>/modifier/', visite_edit_view, name='visite_edit'),
    path('web/visites/<int:visite_id>/supprimer/', visite_delete_view, name='visite_delete'),
    
    # API endpoints
    path('api/visiteurs/search/', api_visiteur_search, name='api_visiteur_search'),
    path('api/visites/<int:visite_id>/action/', api_visite_action, name='api_visite_action'),
]




