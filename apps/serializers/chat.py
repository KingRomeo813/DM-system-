import logging
import json
from django.http import HttpRequest

from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from rest_framework import serializers

from .. import models

logger = logging.getLogger(__name__)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        fields = "__all__"


class ProfileInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Profile
        depth = 1
        fields = "__all__"

class ConversationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConversationSettings
        fields = "__all__"


class ConversationSettingsInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConversationSettings
        depth = 1
        fields = "__all__"

class ConversationSerializer(serializers.ModelSerializer):
    settings = ConversationSettingsSerializer(read_only=True, many=True)
    class Meta:
        model = models.Conversation
        fields = ["name", "room_type", "profiles", "created_at", "message_limit", "settings"]


class ConversationInfoSerializer(serializers.ModelSerializer):
    settings = ConversationSettingsSerializer(read_only=True, many=True)
    class Meta:
        model = models.Conversation
        depth = 1
        fields = ["name", "room_type", "profiles", "created_at", "message_limit", "settings"]

class FollowerSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    class Meta:
        model = models.Follower
        fields = "__all__"


class FollowerInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Follower
        depth = 1
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer(read_only=True)
    conversation = ConversationSerializer(read_only=True)
    class Meta:
        model = models.Message
        fields = "__all__"


class MessageInfoSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer(read_only=True)
    conversation = ConversationSerializer(read_only=True)
    class Meta:
        model = models.Message
        depth = 1
        fields = "__all__"

class RequestSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer()
    receiver = ProfileSerializer()
    class Meta:
        depth = 1
        model = models.Request
        fields = "__all__"


class RequestInfoSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer(read_only=True)
    receiver = ProfileSerializer(read_only=True)
    class Meta:
        model = models.Request
        depth = 1
        fields = "__all__"