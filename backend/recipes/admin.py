from imagekit.admin import AdminThumbnail
from imagekit import ImageSpec
from imagekit.processors import ResizeToFill
from imagekit.cachefiles import ImageCacheFile

from django.contrib import admin

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    Favorite,
    ShoppingCart,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'color',
        'slug',
    )
    list_filter = (
        'name',
        'color',
        'slug',
    )
    fieldsets = (
        (None, {'fields': ('name', 'color',)}),
    )
    search_fields = ('name',)
    empty_value_display = '-пусто-'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    empty_value_display = '-пусто-'


class IngredientAmountInLine(admin.StackedInline):
    model = Recipe.ingredients.through
    extra = 0


class AdminThumbnailSpec(ImageSpec):
    processors = [ResizeToFill(200, 130)]
    format = 'JPEG'
    options = {'quality': 100}


def cached_admin_thumb(instance):
    cached = ImageCacheFile(AdminThumbnailSpec(instance.image))
    cached.generate()
    return cached


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    image_display = AdminThumbnail(image_field=cached_admin_thumb)
    image_display.short_description = 'Картинка'
    list_display = (
        'pk',
        'author',
        'name',
        'cooking_time',
        'image_display'
    )
    list_filter = (
        'author',
        'name',
        'tags'
    )
    inlines = (IngredientAmountInLine,)
    filter_horizontal = ('tags',)
    empty_value_display = '-пусто-'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe'
    )
    list_filter = (
        'user',
        'recipe'
    )
    empty_value_display = '-пусто-'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'user',
        'recipe'
    )
    list_filter = (
        'user',
        'recipe'
    )
    empty_value_display = '-пусто-'
