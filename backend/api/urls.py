from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CustomUserViewSet,
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    DownloadPDFShoppingCartAPIView,
)

router = DefaultRouter()

router.register('users', CustomUserViewSet)
router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('recipes/download_shopping_cart/',
         DownloadPDFShoppingCartAPIView.as_view(),
         name='download_shopping_cart'),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
