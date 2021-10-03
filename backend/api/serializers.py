from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer
from rest_framework import serializers

from users.models import User, Subscription
from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    IngredientAmount,
    Favorite,
    ShoppingCart,
)


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        try:
            user = self.context['request'].user
            author = obj.username
            return Subscription.objects.filter(
                author__username=author,
                subscriber__username=user.username).exists()
        except (TypeError, AttributeError, KeyError):
            return False


class AuthorSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(CustomUserSerializer.Meta):
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        author = obj
        request = self.context['request']
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = author.recipes.all()
        try:
            recipes = recipes[:int(recipes_limit)]
        except TypeError:
            recipes = recipes
        return RecipeSubscriptionSerializer(
            recipes, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, obj):
        author = obj
        return author.recipes.count()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'

    def create(self, validated_data):
        author = validated_data.get('author')
        subscriber = validated_data.get('subscriber')
        if author == subscriber:
            raise serializers.ValidationError(
                'Пользователь не может подписаться на себя.'
            )
        _, created = Subscription.objects.get_or_create(
            author=author, subscriber=subscriber
        )
        if not created:
            raise serializers.ValidationError(
                'Нельзя подписаться второй раз.'
            )
        return validated_data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountGetSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    id = serializers.ReadOnlyField(source='ingredient.id')

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientAmountPostSerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True, min_value=1)
    amount = serializers.IntegerField(write_only=True)


class RecipeSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeGetSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    ingredients = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, obj):
        queryset = IngredientAmount.objects.filter(recipe=obj)
        return IngredientAmountGetSerializer(queryset, many=True).data

    def get_is_favorited(self, obj):
        try:
            request = self.context['request']
            user = request.user
            recipe = obj
            return Favorite.objects.filter(user=user, recipe=recipe).exists()
        except (TypeError, KeyError):
            return False

    def get_is_in_shopping_cart(self, obj):
        try:
            request = self.context['request']
            user = request.user
            recipe = obj
            return ShoppingCart.objects.filter(
                user=user, recipe=recipe
            ).exists()
        except (TypeError, KeyError):
            return False


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountPostSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name', 'text',
                  'cooking_time')

    def validate(self, data):
        ingredients = self.initial_data.get('ingredients')
        for ingredient_elements in ingredients:
            if int(ingredient_elements['amount']) < 1:
                raise serializers.ValidationError(
                    {'ingredients': (
                        'Количество должно быть больше 1.'
                    )
                    }
                )
        return data

    def create_ingredient_elements(self, ingredients_data, recipe):
        ingredients = []
        for ingredient in ingredients_data:
            ingredient_id = ingredient['id']
            amount = ingredient['amount']
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)
            ingredients.append(
                IngredientAmount(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount,
                )
            )
        IngredientAmount.objects.bulk_create(ingredients)

    def create(self, validated_data):
        request = self.context['request']
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=request.user, **validated_data
        )
        recipe.tags.set(tags_data)

        try:
            self.create_ingredient_elements(ingredients_data, recipe)
        except IntegrityError:
            recipe.delete()
            raise serializers.ValidationError(
                'В списке есть повторяющиеся ингредиенты.'
            )
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients_amount.all().delete()
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)

        try:
            self.create_ingredient_elements(ingredients_data, instance)
        except IntegrityError:
            instance.ingredients_amount.all().delete()
            raise serializers.ValidationError(
                'В списке есть повторяющиеся ингредиенты.'
            )
        return instance

    def to_representation(self, instance):
        return RecipeGetSerializer(instance).data


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = '__all__'

    def create(self, validated_data):
        user = validated_data.get('user')
        recipe = validated_data.get('recipe')
        _, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                'Нельзя добавить рецпет в избранное второй раз.'
            )
        return validated_data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def create(self, validated_data):
        user = validated_data.get('user')
        recipe = validated_data.get('recipe')
        _, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                'Рецепт уже в корзине.'
            )
        return validated_data
