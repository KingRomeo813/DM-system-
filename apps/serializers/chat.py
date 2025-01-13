import logging
import json
from django.http import HttpRequest

from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from rest_framework import serializers

from .. import models

logger = logging.getLogger(__name__)


# class ProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Profile
#         fields = "__all__"


# class ProfileInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Profile
#         depth = 1
#         fields = "__all__"

# class ConversationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Conversation
#         fields = "__all__"


# class ConversationInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Conversation
#         depth = 1
#         fields = "__all__"


# class MessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Message
#         fields = "__all__"


# class MessageInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Message
#         depth = 1
#         fields = "__all__"


# class FriendsSerializer(serializers.ModelSerializer):
#     profile = ProfileSerializer(read_only=True)
#     class Meta:
#         model = models.Friends
#         fields = "__all__"


# class FriendsInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = models.Friends
        # depth = 1
        # fields = "__all__"
