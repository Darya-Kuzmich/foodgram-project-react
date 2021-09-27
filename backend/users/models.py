from django.contrib.auth.models import AbstractUser
from django.core.validators import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import CheckConstraint, F, Q, UniqueConstraint
from django.db import models

from users.validators import UsernameValidators


class User(AbstractUser):
    username_validator = UsernameValidators()

    email = models.EmailField(
        verbose_name=_('E-mail'),
        unique=True,
    )
    username = models.CharField(
        verbose_name=_('Логин'),
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': _('Пользователь с таким логином уже существует'),
        },
    )
    first_name = models.CharField(
        verbose_name=_('Имя'),
        max_length=150
    )
    last_name = models.CharField(
        verbose_name=_('Фамилия'),
        max_length=150
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return 'Пользователь {}'.format(self.username)


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='subscriber',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='author',
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=['subscriber', 'author'],
                             name='unique_subscription'),
            CheckConstraint(check=~Q(subscriber=F('author')),
                            name='subscriber_not_author'),
        ]
        ordering = ('id',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return '{} подписался на {}'.format(self.subscriber.username,
                                            self.author.username)

    def clean(self):
        if self.subscriber == self.author:
            raise ValidationError(
                _('Пользователь не может подписаться сам на себя.')
            )
