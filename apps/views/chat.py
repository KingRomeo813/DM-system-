import logging
from django.db.models import Q, Count

from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, permissions, status, filters, generics
from apps.repositories.conversation.message_service import validate_and_create_message
from apps.repositories import ProfileRepo
from apps.celery_tasks import send_messages
from apps.utils import CustomAuthenticated
from apps.models import (Conversation,
                        Follower,
                        Message,
                        ConversationSettings,
                        Profile,
                        Request,
                        MessageReact,
                        Reaction,
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
                            AttachmentSerializer,
                            RequestInfoSerializer,
                            MessageReactSerializer,
                            MessageReactInfoSerializer,
                            AttachmentSerializer,
                            RequestInfoSerializer)

from apps.filters import ConversationFilter
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
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data["sender"] = str(request.user.id)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            try:
                conversation, receiver = validate_and_create_message(data, request.user)
                message = serializer.save()
                send_messages.delay(message_id=message.id, user_id=message.receiver().id)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

        return Response("Message couldn't be sent please try again", status=status.HTTP_400_BAD_REQUEST)
        
class MessageReactViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 'put', 'delete', 'patch', "post"]
    queryset = MessageReact.objects.filter(is_active=True).order_by("-created_at")
    # search_fields = ['id', "conversation__id"]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ['exact'],
        'message__id': ['exact'],
        'reaction': ['exact'],

    }
    def get_queryset(self):
        user = self.request.user
        return MessageReact.objects.filter(
            is_active=True,
        ).order_by("-created_at")

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return MessageReactInfoSerializer
        return MessageReactSerializer

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            if not "reaction" in data:
                return Response("Reaction is required", status=status.HTTP_400_BAD_REQUEST)
            reaction, _ = Reaction.objects.get_or_create(reaction=data["reaction"])
            message = Message.objects.get(id=data["message"])
            react = MessageReact.objects.create(message=message, reaction=reaction, reacted_by=request.user)
            return Response(MessageReactSerializer(react).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
class MessageForwardViewSet(viewsets.ModelViewSet):

    permission_classes = [CustomAuthenticated]
    http_method_names = ["post"]
    queryset = Message.objects.filter(is_active=True).order_by("-created_at")
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ['exact'],
        'conversation__id': ['exact'],
    }
    def create(self, request, *args, **kwargs):
        data = request.data
        conversations = data.get('conversations', None)

        if not conversations:
            return Response("No conversations provided", status=status.HTTP_400_BAD_REQUEST)
        message_id = data.get("message", None)

        message_ids = data.get("messages", None)
        if not message_ids:
            return Response("Message not found", status=status.HTTP_404_NOT_FOUND)
        
        errors = []
        for conversation in Conversation.objects.filter(id__in = conversations):
            for message in Message.objects.filter(id__in = message_ids):
                try:
                    new_message = Message.objects.create(
                        **message.get_content(),
                        sender=request.user,
                        conversation=conversation, 
                        forwarded_from=message,
                        is_forwarded=True
                    )
                    send_messages.delay(message_id=new_message.id, user_id=new_message.receiver().id)
                except Exception as e:
                    errors.append(str(e) + f" {conversation.id}")

        return Response({"success":"Message Forwarded Succesfully",
                         "errors": errors}, status=status.HTTP_201_CREATED)

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
    # filterset_fields = {
    #     'id': ['exact'],
    #     'name': ['exact'],
    #     "profiles": ['exact'],
    #     "message_limit": ['exact'],
    #     'created_at': ['exact'],
    #     'room_type': ['exact'],
    # }
    filterset_class = ConversationFilter

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
    
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        user = request.user
        repo = ProfileRepo(request.token)
        items = [str(request.user.id)]
        
        try:
            if data.get("profiles_user_ids", []):
                op_profiles = repo.profiles_by_ids(ids=data.get("profiles_user_ids", ""))

                profiles = items + [str(i.id) for i in op_profiles]
                data["profiles"] = profiles
        except Exception as e:
            log.error(str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if Conversation.objects.filter(profiles=user).filter(profiles=op_profiles[0]).exists():
            return Response({"error": "A private conversation between these two profiles already exists."}, status=status.HTTP_400_BAD_REQUEST)
        try:

            serializer = self.get_serializer(data=data)
            if serializer.is_valid(raise_exception=True):
                conversation = serializer.save()
                for profile in conversation.profiles.all():
                    conversation.settings.get_or_create(profile=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # return Response("Conversation Couldn't be create please try again", status=status.HTTP_400_BAD_REQUEST)
        

class ConversationUserViewSet(generics.GenericAPIView):
    permission_classes = [CustomAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        if "user_id" not in kwargs:
            return Response({"error": "UserId is required"}, status=status.HTTP_400_BAD_REQUEST)
        repo = ProfileRepo(request.token)
        try:
            op_user = repo.profiles_by_ids(ids=[int(kwargs.get("user_id"))])
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user2 = op_user[0]

        conv = Conversation.objects.filter(profiles=user).filter(profiles=user2)
        if conv.exists():
            conversation = conv.first()
        else:
            conversation = Conversation.objects.create(
                name=f"{user.first_name} - {user2.first_name}",
                room_type=Conversation.PRIVATE,
            )
            conversation.profiles.add(user)
            conversation.profiles.add(user2)
            conversation.save()
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
        
class ConversationSettingsViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 
                         'put', 
                        #  'delete', 
                         'patch' 
                        #  "post"
                         ]
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

class CustomRequestViewSet(generics.GenericAPIView):
    permission_classes = [CustomAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data.copy()
            user = request.user
            repo = ProfileRepo(request.token)

            try:
                op_user = repo.profiles_by_ids(ids=[int(data.get("user_id", None))])
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user2 = op_user[0]
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            print("request4")
            q1 = Request.objects.filter(sender=user).filter(receiver=user2)
            q2 = Request.objects.filter(sender=user2).filter(receiver=user)
            if q1.exists() or q2.exists():
                req = q1 | q2
                print("request3")

                if "status" in data:
                    print("request5")
                    existing_request = req.first()

                    if existing_request.receiver != user and data["status"]=="accepted":
                        return Response({"error": "Sender can't accept the request"}, status=status.HTTP_400_BAD_REQUEST)
                    req.update(status=data["status"])
                    serializer = RequestInfoSerializer(req.first())  # Serialize single object
                    print("request6")
                    return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                obj = Request.objects.create(sender=user, receiver=user2, status="pending")
                serializer = RequestInfoSerializer(obj)

                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class FollowerViewset(viewsets.ModelViewSet):
    permission_classes = [CustomAuthenticated]
    http_method_names = ['get', 
                         'put', 
                         'delete', 
                         'patch', 
                         "post"]
    queryset = Follower.objects.filter(is_active=True).order_by("-created_at")
    search_fields = ['id']
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    filterset_fields = {
        'id': ["exact"], 
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
    
    def create(self, request, *args, **kwargs):

        data = request.data.copy()
        repo = ProfileRepo(request.token)
        data["follower"] = str(request.user.id)
        if data.get("following_user_id", None):
            data["following"] = str(repo.profiles_by_ids(ids=[data["following_user_id"]])[0].id)
        
        try:
            serializer = self.get_serializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                print(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        # "sender__id": ["exact"],
        # "sender__first_name": ["exact"],
        # "sender__last_name": ["exact"],
        # "sender__email": ["exact"],
        # "receiver__id": ["exact"],
        # "receiver__first_name": ["exact"],
        # "receiver__last_name": ["exact"],
        # "receiver__email": ["exact"],
        # "status": ["exact"],
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
        try:
            data = request.data.copy()
            data["sender"] = str(request.user.id)
            repo = ProfileRepo(request.token)
            if data.get("receiver_user_id", None): 
                data["receiver"] = str(repo.profiles_by_ids(ids=[data["receiver_user_id"]])[0].id)
            serializer = self.get_serializer(data=data)
            if serializer.is_valid(raise_exception=True):
                print(serializer)
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, statut=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(str(e))
            raise    


class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachments.objects.all()
    serializer_class = AttachmentSerializer
    http_method_names = ['post']  # Limit to POST for file upload only

    def create(self, request, *args, **kwargs):
        # Create the serializer instance with the request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Validate the data

        # Save the instance using the validated data
        self.perform_create(serializer)

        # Respond with the serialized data
        return Response(serializer.data, status=status.HTTP_201_CREATED)
