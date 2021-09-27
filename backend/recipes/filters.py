from django_filters import rest_framework as filters

from recipes.models import Ingredient, Tag
from users.models import User


class IngredientFilterSet(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilterSet(filters.FilterSet):
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    author = filters.ModelChoiceFilter(queryset=User.objects.all())
