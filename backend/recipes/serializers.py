from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from users.serializers import CustomUserSerializer
from recipes.models import (
    Tag,
    Recipe,
    Ingredient,
    IngredientAmount,
    Favorite,
    ShoppingCart,
)


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
    id = serializers.SerializerMethodField()

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_id(self, obj):
        return obj.ingredient.id


class IngredientAmountPostSerializer(serializers.Serializer):
    id = serializers.IntegerField(write_only=True, min_value=1)
    amount = serializers.IntegerField(write_only=True, min_value=1)


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

    def create(self, validated_data):
        request = self.context['request']
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=request.user, **validated_data
        )
        recipe.tags.set(tags_data)

        ingredient_elements = []
        for ingredient_element in ingredients_data:
            id = ingredient_element['id']
            amount = ingredient_element['amount']
            ingredient = get_object_or_404(Ingredient, id=id)
            ingredient_elements.append(
                IngredientAmount(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=amount,
                )
            )
        try:
            IngredientAmount.objects.bulk_create(ingredient_elements)
        except IntegrityError:
            recipe.delete()
            raise serializers.ValidationError(
                _('В списке есть повторяющиеся ингредиенты.')
            )
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients_amount.all().delete()
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        try:
            image = validated_data.pop('image')
            instance.image = image
            instance.save()
        except KeyError:
            pass
        recipe = Recipe.objects.filter(id=instance.id)
        recipe.update(**validated_data)

        instance_tags = [tag for tag in instance.tags.all()]

        for tag in tags_data:
            if tag in instance_tags:
                instance_tags.remove(tag)
            else:
                instance.tags.add(tag)
        instance.tags.remove(*instance_tags)

        ingredient_elements = []
        for ingredient_element in ingredients_data:
            id = ingredient_element['id']
            amount = ingredient_element['amount']
            ingredient = get_object_or_404(Ingredient, id=id)
            ingredient_elements.append(
                IngredientAmount(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=amount,
                )
            )
        try:
            IngredientAmount.objects.bulk_create(ingredient_elements)
        except IntegrityError:
            instance.ingredients_amount.all().delete()
            raise serializers.ValidationError(
                _('В списке есть повторяющиеся ингредиенты.')
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
        favorite, created = Favorite.objects.get_or_create(
            user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                _('Нельзя добавить рецпет в избранное второй раз.')
            )
        return validated_data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShoppingCart
        fields = '__all__'

    def create(self, validated_data):
        user = validated_data.get('user')
        recipe = validated_data.get('recipe')
        favorite, created = ShoppingCart.objects.get_or_create(
            user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(
                _('Рецепт уже в корзине.')
            )
        return validated_data
