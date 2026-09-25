from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CameraViewSet, ZoneSurveillanceViewSet, ProfilFacialDetenuViewSet,
    DetectionFacialeViewSet, AlerteSurveillanceViewSet, SurveillanceDashboardViewSet
)

# Création du routeur
router = DefaultRouter()
router.register(r'cameras', CameraViewSet, basename='surveillance-camera')
router.register(r'zones', ZoneSurveillanceViewSet, basename='surveillance-zone')
router.register(r'profils-faciaux', ProfilFacialDetenuViewSet, basename='surveillance-profil')
router.register(r'detections', DetectionFacialeViewSet, basename='surveillance-detection')
router.register(r'alertes', AlerteSurveillanceViewSet, basename='surveillance-alerte')
router.register(r'dashboard', SurveillanceDashboardViewSet, basename='surveillance-dashboard')

app_name = 'surveillance'

urlpatterns = [
    path('', include(router.urls)),
]
