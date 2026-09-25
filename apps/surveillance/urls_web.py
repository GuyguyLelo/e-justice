from django.urls import path
from . import views_web
from . import api_views_fixed
from . import api_simple
from django.shortcuts import render

app_name = 'surveillance'

urlpatterns = [
    # Dashboard
    path('', views_web.surveillance_dashboard, name='dashboard'),
    
    # Caméras
    path('cameras/', views_web.CameraListView.as_view(), name='camera_list'),
    path('cameras/<int:pk>/', views_web.CameraDetailView.as_view(), name='camera_detail'),
    path('cameras/<int:camera_id>/stream/', views_web.camera_stream, name='camera_stream'),
    
    # Détections
    path('detections/', views_web.detections_list, name='detections_list'),
    path('detections/<int:detection_id>/', views_web.detection_detail_view, name='detection_detail'),
    
    # Alertes
    path('alertes/', views_web.AlerteListView.as_view(), name='alerte_list'),
    path('alertes/<int:alerte_id>/', views_web.alerte_detail, name='alerte_detail'),
    
    # Profils faciaux
    path('profils-faciaux/', views_web.profils_faciaux_list, name='profils_faciaux_list'),
    
    # API endpoints pour les vues web
    path('api/camera-stats/', views_web.api_camera_stats, name='api_camera_stats'),
    path('api/detection-stats/', views_web.api_detection_stats, name='api_detection_stats'),
    path('api/alerte-stats/', views_web.api_alerte_stats, name='api_alerte_stats'),
    
    # API endpoints pour la reconnaissance faciale (sans authentification pour les tests)
    path('api/initialiser-systeme/', api_simple.initialiser_systeme_simple, name='api_initialiser_systeme'),
    path('api/tester-reconnaissance/', api_views_fixed.tester_reconnaissance, name='api_tester_reconnaissance'),
    path('api/encoder-visage/<int:detenu_id>/', api_views_fixed.encoder_visage_detenu, name='api_encoder_visage'),
    path('api/detecter-visage/', api_simple.detecter_visage_simple, name='api_detecter_visage'),
    
    # Test de reconnaissance faciale
    path('test-reconnaissance/', lambda request: render(request, 'surveillance/test_reconnaissance.html'), name='test_reconnaissance'),
]
