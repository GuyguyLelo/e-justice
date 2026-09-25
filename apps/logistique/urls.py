from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FournisseurViewSet, ProduitViewSet, CommandeViewSet, MouvementStockViewSet
)

router = DefaultRouter()
router.register(r'fournisseurs', FournisseurViewSet)
router.register(r'produits', ProduitViewSet)
router.register(r'commandes', CommandeViewSet)
router.register(r'mouvements-stock', MouvementStockViewSet)

urlpatterns = [
    path('', include(router.urls)),
]






