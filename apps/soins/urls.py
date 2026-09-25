from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MedicamentViewSet, ConsultationViewSet, AntecedentMedicalViewSet, VaccinationViewSet
)

router = DefaultRouter()
router.register(r'medicaments', MedicamentViewSet)
router.register(r'consultations', ConsultationViewSet)
router.register(r'antecedents', AntecedentMedicalViewSet)
router.register(r'vaccinations', VaccinationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]






