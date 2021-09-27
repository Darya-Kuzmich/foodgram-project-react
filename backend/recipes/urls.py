from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import (
    TagViewSet,
    IngredientViewSet,
    RecipeViewSet,
    DownloadPDFShoppingCartAPIView,
)

router = DefaultRouter()

router.register('tags', TagViewSet)
router.register('ingredients', IngredientViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('recipes/download_shopping_cart/',
         DownloadPDFShoppingCartAPIView.as_view()),
    path('', include(router.urls)),
]
