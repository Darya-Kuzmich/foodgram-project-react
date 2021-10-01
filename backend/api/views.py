from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from io import BytesIO

from djoser.views import UserViewSet
from rest_framework import status, serializers, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse

from users.models import User, Subscription
from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
)

from .serializers import (
    CustomUserSerializer,
    SubscriptionSerializer,
    AuthorSerializer, TagSerializer,
    IngredientSerializer,
    RecipeGetSerializer,
    RecipePostSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer,
    RecipeSubscriptionSerializer,
)

from .filters import IngredientFilterSet, RecipeFilterSet


class CustomUserViewSet(UserViewSet):
    serializer_class = CustomUserSerializer
    queryset = User.objects.all()

    @action(detail=False, methods=['get'],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        subscribes = User.objects.filter(
            author__in=self.request.user.subscriber.all()
        )
        page = self.paginate_queryset(subscribes)
        if page is not None:
            serializer = AuthorSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = AuthorSerializer(
            subscribes, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, *args, **kwargs):
        subscriber = self.request.user
        author = self.get_object()
        serializer = SubscriptionSerializer(
            data={'author': author.id, 'subscriber': subscriber.id}
        )
        if serializer.is_valid():
            if request.method == 'GET':
                serializer.save()
                response = AuthorSerializer(
                    author, context={'request': request}
                )
                return Response(response.data, status=status.HTTP_201_CREATED)
            if not Subscription.objects.filter(
                    **serializer.validated_data).exists():
                raise serializers.ValidationError(
                    'Чтобы отписаться, нужно сначала подписаться ;)'
                )
            get_object_or_404(Subscription,
                              **serializer.validated_data).delete()
            return Response(
                {'status': 'Подписка удалена.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


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
    queryset = Recipe.objects.all().order_by('-id')

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
        if serializer.is_valid():
            if request.method == 'GET':
                serializer.save()
                response = RecipeSubscriptionSerializer(
                    recipe, context={'request': request}
                )
                return Response(response.data, status=status.HTTP_201_CREATED)
            if not Favorite.objects.filter(
                    **serializer.validated_data).exists():
                raise serializers.ValidationError(
                    'Чтобы удалить рецепт из избранного,'
                    'нужно сначала его добавить.'
                )
            get_object_or_404(Favorite, **serializer.validated_data).delete()
            return Response(
                {'status': 'Рецепт удалён из избранного.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'delete'],
            permission_classes=[permissions.IsAuthenticated])
    def shopping_cart(self, request, *args, **kwargs):
        user = self.request.user
        recipe = self.get_object()
        serializer = ShoppingCartSerializer(
            data={'recipe': recipe.id, 'user': user.id}
        )
        if serializer.is_valid():
            if request.method == 'GET':
                serializer.save()
                response = RecipeSubscriptionSerializer(
                    recipe, context={'request': request}
                )
                return Response(response.data, status=status.HTTP_201_CREATED)
            if not ShoppingCart.objects.filter(
                    **serializer.validated_data).exists():
                raise serializers.ValidationError(
                    'Чтобы удалить рецепт из корзины,'
                    'нужно сначала его добавить.'
                )
            get_object_or_404(ShoppingCart,
                              **serializer.validated_data).delete()
            return Response(
                {'status': 'Рецепт удалён из корзины.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class DownloadPDFShoppingCartAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        ingredient_elements = user.shopping_carts.values_list(
            'recipe__ingredients_amount__ingredient__name',
            'recipe__ingredients_amount__ingredient__measurement_unit',
            'recipe__ingredients_amount__amount'
        )
        shopping_cart = {}

        for ingredient_element in ingredient_elements:
            name, measurement_unit, amount = ingredient_element
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
