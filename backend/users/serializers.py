from djoser.serializers import UserSerializer
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from users.models import User, Subscription


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
        from recipes.serializers import RecipeSubscriptionSerializer

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
                _('Пользователь не может подписаться на себя.')
            )
        subscription, created = Subscription.objects.get_or_create(
            author=author, subscriber=subscriber
        )
        if not created:
            raise serializers.ValidationError(
                _('Нельзя подписаться второй раз.')
            )
        return validated_data
