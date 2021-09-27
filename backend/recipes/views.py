from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from io import BytesIO

from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status, serializers, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
    IngredientAmount,
)
from recipes.serializers import (
    TagSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    RecipeSubscriptionSerializer,
)
from recipes.filters import IngredientFilterSet, RecipeFilterSet


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilterSet
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilterSet

    def get_queryset(self):
        user = self.request.user.id
        queryset = Recipe.objects.all().order_by('-id')
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        favorites = Favorite.objects.filter(user=user)
        shopping_carts = ShoppingCart.objects.filter(user=user)
        if is_favorited == 'true':
            queryset = queryset.filter(favorites__in=favorites)
        elif is_favorited == 'false':
            queryset = queryset.exclude(favorites__in=favorites)
        if is_in_shopping_cart == 'true':
            queryset = queryset.filter(shopping_carts__in=shopping_carts)
        elif is_in_shopping_cart == 'false':
            queryset = queryset.exclude(shopping_carts__in=shopping_carts)
        return queryset.all().order_by('-id')

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        return RecipePostSerializer

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, *args, **kwargs):
        user = self.request.user
        recipe = self.get_object()
        serializer = FavoriteSerializer(
            data={'recipe': recipe.id, 'user': user.id}
        )
        if request.method == 'GET':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response = RecipeSubscriptionSerializer(
                recipe, context={'request': request}
            )
            return Response(response.data, status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        if not Favorite.objects.filter(**serializer.validated_data):
            raise serializers.ValidationError(
                _('Чтобы удалить рецепт из избранного,'
                  'нужно сначала его добавить.')
            )
        get_object_or_404(Favorite, **serializer.validated_data).delete()
        return Response(
            {'status': _('Рецепт удалён из избранного.')},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, *args, **kwargs):
        user = self.request.user
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={'recipe': recipe.id, 'user': user.id}
        )
        if request.method == 'GET':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response = RecipeSubscriptionSerializer(
                recipe, context={'request': request}
            )
            return Response(response.data, status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        if not ShoppingCart.objects.filter(**serializer.validated_data):
            raise serializers.ValidationError(
                _('Чтобы удалить рецепт из корзины,'
                  'нужно сначала его добавить.')
            )
        get_object_or_404(ShoppingCart, **serializer.validated_data).delete()
        return Response(
            {'status': _('Рецепт удалён из корзины.')},
            status=status.HTTP_204_NO_CONTENT
        )


class DownloadPDFShoppingCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        ingredients_amount = IngredientAmount.objects.filter(
            recipe__shopping_carts__user=user.id)
        shopping_cart = {}

        for ingredients_element in ingredients_amount:
            name = ingredients_element.ingredient.name
            measurement_unit = ingredients_element.ingredient.measurement_unit
            amount = ingredients_element.amount
            if name not in shopping_cart:
                shopping_cart[name] = {
                    'measurement_unit': measurement_unit,
                    'amount': amount
                }
            else:
                shopping_cart[name]['amount'] += amount

        pdfmetrics.registerFont(
            TTFont("DejaVuSerif", "DejaVuSerif.ttf", "UTF-8")
        )
        response = HttpResponse(content_type='application/pdf')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_cart.pdf"'
        buffer = BytesIO()
        page = canvas.Canvas(buffer)
        page.setFont('DejaVuSerif', size=15)
        page.drawString(230, 780, f'Список покупок:')
        page.setFont('DejaVuSerif', size=12)
        height = 730
        count = 1

        for name, data in shopping_cart.items():
            page.drawString(
                50,
                height,
                (
                    f'{count}. {name} - {data["amount"]} '
                    f'({data["measurement_unit"]})'
                ),
            )
            height -= 25
            count += 1
        page.showPage()
        page.save()
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        ShoppingCart.objects.filter(user=user).delete()
        return response
