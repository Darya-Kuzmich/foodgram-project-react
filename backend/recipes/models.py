from colorfield.fields import ColorField

from django.db import models
from django.db.models import UniqueConstraint
from django.utils.text import slugify
from django.core.validators import MinValueValidator, validate_unicode_slug

from users.models import User
from recipes.translation import get_translate_ru_to_en, get_alternative


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
        unique=True,
        error_messages={
            'unique': 'Тег с таким названием и слагом уже существует',
        },
    )
    color = ColorField(
        verbose_name='Цвет в HEX',
        max_length=7
    )
    slug = models.CharField(
        verbose_name='Уникальный слаг',
        max_length=200,
        unique=True,
        validators=[validate_unicode_slug]
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.slug is not None:
            self.slug = slugify(get_alternative(self.name))
        else:
            self.slug = slugify(get_translate_ru_to_en(self.name))
        super().save(*args, **kwargs)


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
        db_index=True
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/'
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='IngredientAmount',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[MinValueValidator(1, 'Время приготовления не может '
                                         'быть меньше 1 минуты')]
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    MEASUREMENT_UNIT_CHOICES = (
        ('г', 'г'),
        ('кг', 'кг'),
        ('шт.', 'шт.'),
        ('ч. л.', 'ч. л.'),
        ('ст. л.', 'ст. л.'),
        ('мл', 'мл'),
        ('л', 'л'),
        ('стакан', 'стакан'),
        ('долька', 'долька'),
        ('веточка', 'веточка'),
        ('горсть', 'горсть'),
        ('пучок', 'пучок'),
        ('щепотка', 'щепотка'),
        ('по вкусу', 'по вкусу'),
        ('кусок', 'кусок'),
        ('банка', 'банка'),
        ('упаковка', 'упаковка'),
        ('батон', 'батон'),
        ('капля', 'капля'),
        ('бутылка', 'бутылка'),
        ('зубчик', 'зубчик'),
    )
    name = models.CharField(
        verbose_name='Ингредиент',
        max_length=200,
        unique=True
    )
    measurement_unit = models.CharField(
        verbose_name='Единица Измерения',
        max_length=200,
        choices=MEASUREMENT_UNIT_CHOICES
    )

    class Meta:
        ordering = ('id',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    recipe = models.ForeignKey(
        'Recipe',
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='ingredients_amount'
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        verbose_name='Ингредиент',
        on_delete=models.CASCADE,
        related_name='ingredients_amount'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1, 'Количество не может быть меньше 1')]
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=['recipe', 'ingredient'],
                             name='unique_recipe_ingredient')
        ]
        ordering = ('id',)
        verbose_name = 'Элемент рецепта'
        verbose_name_plural = 'Элементы рецепта'


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='favorites'
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_favorite')
        ]
        ordering = ('id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return 'Пользователь {} добавил рецепт {} в избранное'.format(
            self.user.username, self.recipe.name
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='shopping_carts'
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='shopping_carts'
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_shopping_cart')
        ]
        ordering = ('id',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return 'Пользователь {} добавил рецепт {} в список покупок'.format(
            self.user.username, self.recipe.name
        )
