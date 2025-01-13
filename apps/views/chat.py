import logging
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, permissions, status, filters

from apps.utils import CustomAuthenticated

from apps.models import (Conversation,
                        Follower,
                        Message,
                        ConversationSettings,
                        Profile,
                        Attachments)
from apps.serializers import (MessageSerializer,
                            MessageInfoSerializer,
                            ConversationSerializer,
                            ConversationInfoSerializer,
                            ConversationSettingsSerializer,
                            ConversationSettingsInfoSerializer,
                            FollowerSerializer,
                            FollowerInfoSerializer)
log = logging.getLogger(__file__)


class MessageViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 'put', 'delete', 'patch', "post"]
    queryset = Message.objects.filter(is_active=True).order_by("-created_at")
    search_fields = ['id', "conversation__id"]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ['exact'],
        'conversation__id': ['exact'],
    }
    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            is_active=True,
            conversation__profiles__in = [user]
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return MessageInfoSerializer
        return MessageSerializer
    
class ConversationViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 
                         'put', 
                         'delete', 
                         'patch', 
                         "post"]
    queryset = Conversation.objects.filter(is_active=True).order_by("-created_at")
    search_fields = ['id', 
                     "name", 
                     "profiles", 
                     "created_at", 
                     "updated_at", 
                     "message_limit"]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ['exact'],
    }
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            is_active=True,
            profiles__in=[user]
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ConversationInfoSerializer
        return ConversationSerializer
    
class ConversationSettingsViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 
                         'put', 
                         'delete', 
                         'patch', 
                         "post"]
    queryset = ConversationSettings.objects.filter(is_active=True).order_by("-created_at")
    search_fields = ['id', 
                     "name", 
                     "profiles", 
                     "created_at", 
                     "updated_at", 
                     "message_limit"]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ['exact'],
    }
    def get_queryset(self):
        user = self.request.user
        return ConversationSettings.objects.filter(
            is_active=True,
            profiles__in=[user]
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ConversationSettingsInfoSerializer
        return ConversationSettingsSerializer
    
class FollowerViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 
                         'put', 
                         'delete', 
                         'patch', 
                         "post"]
    queryset = Follower.objects.filter(is_active=True).order_by("-created_at")
    search_fields = ['id', 
                     "follower__id",
                     "follower__first_name",
                     "follower__last_name",
                     "follower__email",
                     "following__id",
                     "following__first_name",
                     "following__last_name",
                     "following__email",
                     "is_mutual"
                     ]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ["exact"], 
        "follower__id": ["exact"],
        "follower__first_name": ["exact"],
        "follower__last_name": ["exact"],
        "follower__email": ["exact"],
        "following__id": ["exact"],
        "following__first_name": ["exact"],
        "following__last_name": ["exact"],
        "following__email": ["exact"],
        "is_mutual": ["exact"]
    }
    def get_queryset(self):
        user = self.request.user
        return Follower.objects.filter(
            is_active=True,
            profiles__in=[user]
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return FollowerInfoSerializer
        return FollowerSerializer
    
