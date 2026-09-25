from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RapportViewSet, ModeleRapportViewSet, TableauBordViewSet

router = DefaultRouter()
router.register(r'rapports', RapportViewSet)
router.register(r'modeles', ModeleRapportViewSet)
router.register(r'tableaux-bord', TableauBordViewSet)

urlpatterns = [
    path('', include(router.urls)),
]






