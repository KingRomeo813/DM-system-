import logging
from django.db.models import Q
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, permissions, status, filters

from apps.utils import CustomAuthenticated

from apps.models import (Conversation,
                        Follower,
                        Message,
                        ConversationSettings,
                        Profile,
                        Request,
                        Attachments)
from apps.serializers import (MessageSerializer,
                            MessageInfoSerializer,
                            ConversationSerializer,
                            ConversationInfoSerializer,
                            ConversationSettingsSerializer,
                            ConversationSettingsInfoSerializer,
                            FollowerSerializer,
                            FollowerInfoSerializer,
                            RequestSerializer,
                            RequestInfoSerializer)
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
        print(type(user))
        return Conversation.objects.filter(
            is_active=True,
            profiles__in=[user]
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ConversationInfoSerializer
        return ConversationSerializer
    
    def create(self, request, *args, **kwargs):
        data = request.data
        profiles = list(Profile.objects.filter(id__in = data["profiles"]))
        if Conversation.objects.filter(profiles__in = profiles).exists():
            raise ValueError("A private conversation between these two profiles already exists.")

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save()
            for profile in profiles:
                conversation.settings.get_or_create(profile=profile)
        
        # Return the created conversation data in the response
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class ConversationSettingsViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 
                         'put', 
                         'delete', 
                         'patch', 
                         "post"]
    queryset = ConversationSettings.objects.filter(is_active=True).order_by("-created_at")
    search_fields = ['id', 
                     "conversation__id",
                     "is_muted",
                     "is_blocked",
                     "is_trashed",
                     "is_last_muted_at",
                     "is_last_blocked_at",
                     "is_last_trashed_at",
                     "created_at", 
                     "updated_at", 
                     ]
    
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ['exact'],
    }
    def get_queryset(self):
        user = self.request.user
        return ConversationSettings.objects.filter(
            is_active=True,
            profile=user
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
            Q(follower=user) | Q(following=user),
            is_active=True,
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return FollowerInfoSerializer
        return FollowerSerializer
    

class RequestViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 
                         'put', 
                         'delete', 
                         'patch', 
                         "post"]
    queryset = Request.objects.filter(is_active=True).order_by("-created_at")
    search_fields = ['id', 
                     "sender__id",
                     "sender__first_name",
                     "sender__last_name",
                     "sender__email",

                     "receiver__id",
                     "receiver__first_name",
                     "receiver__last_name",
                     "receiver__email",
                     "status",
                     ]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ["exact"], 
        "sender__id": ["exact"],
        "sender__first_name": ["exact"],
        "sender__last_name": ["exact"],
        "sender__email": ["exact"],
        "receiver__id": ["exact"],
        "receiver__first_name": ["exact"],
        "receiver__last_name": ["exact"],
        "receiver__email": ["exact"],
        "status": ["exact"],
    }
    def get_queryset(self):
        user = self.request.user
        return Request.objects.filter(
            Q(sender=user) | Q(receiver=user),
            is_active=True,
            status="pending"
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RequestInfoSerializer
        return RequestSerializer

    def create(self, request, *args, **kwargs):

        data = request.data
        # try:
        #     receiver = Profile.objects.get(id = data["receiver"])
        # except Exception as e:
        #     raise ValueError(str(e))

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)