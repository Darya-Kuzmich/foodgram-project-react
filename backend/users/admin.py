from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User, Subscription


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'pk',
        'is_staff',
        'is_active',
        'email',
        'username',
        'first_name',
        'last_name',
        'password',
    )
    list_filter = (
        'email',
        'username',
    )
    fieldsets = (
        (None, {'fields': ('username', 'first_name', 'last_name', 'email',
                           'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')})
    )
    search_fields = ('username',)
    empty_value_display = '-пусто-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'subscriber',
        'author',
    )
    list_filter = (
        'subscriber',
        'author',
    )
    search_fields = (
        'subscriber',
        'author',
    )
    empty_value_display = '-пусто-'
