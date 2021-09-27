from djoser.views import UserViewSet
from rest_framework import status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404

from users.models import User, Subscription
from users.serializers import (
    CustomUserSerializer,
    SubscriptionSerializer,
    AuthorSerializer
)


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
        if request.method == 'GET':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response = AuthorSerializer(
                author, context={'request': request}
            )
            return Response(response.data, status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        if not Subscription.objects.filter(**serializer.validated_data):
            raise serializers.ValidationError(
                _('Чтобы отписаться, нужно сначала подписаться ;)')
            )
        get_object_or_404(Subscription, **serializer.validated_data).delete()
        return Response(
            {'status': _('Подписка удалена.')},
            status=status.HTTP_204_NO_CONTENT
        )
