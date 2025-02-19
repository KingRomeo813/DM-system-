import logging
import json
from django.http import HttpRequest

from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.db.models import Count
from rest_framework import serializers

from .. import models

log = logging.getLogger(__name__)


class AttachmentSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(write_only=True, required=False, default='Attachment')  

    class Meta:
        model = models.Attachments
        fields = [
                'id',
                'file', 
                'field_name', 
                "original_name",
                "file_type",
                "file_size"
                ]  
    def create(self, validated_data):
        field_name = validated_data.pop('field_name', None)

        attachment = models.Attachments(**validated_data)

        attachment.save(field_name=field_name)

        return attachment
    
class AttachmentInfoSerializer(serializers.ModelSerializer):
    field_name = serializers.CharField(write_only=True, required=False, default='Attachment')  

    class Meta:
        model = models.Attachments
        fields = [
                'id',
                'file', 
                'field_name', 
                "original_name",
                "file_type",
                "file_size"
                ]  
        depth = 1

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
    settings = serializers.SerializerMethodField()
    requests = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()

    def get_unread_messages(self, obj):
        if obj.messages.filter(is_active=True).exists():
            return obj.messages.count()
        return 0
    
    def get_requests(self, obj):
        request = self.context.get("request")
        if not request or not request.user:
            return None

        user_profile = request.user
        other_profiles = obj.profiles.exclude(id=user_profile.id)
        sent_requests = models.Request.objects.filter(sender=user_profile, receiver__in=other_profiles)
        received_requests = models.Request.objects.filter(sender__in=other_profiles, receiver=user_profile)
        all_requests = sent_requests | received_requests
        return RequestSerializer(all_requests, many=True).data

    def get_last_message(self, obj):
        if obj.messages.filter(is_active=True).exists():
            return MessageSerializer(
                obj.messages.filter(is_active=True).order_by("-created_at").first()
            ).data
        return []
    def get_settings(self, obj):
        request = self.context.get("request")
        if request and request.user:
            return ConversationSettingsSerializer(
                obj.settings.exclude(profile=request.user),
                many=True
            ).data
        return ConversationSettingsSerializer(obj.settings, many=True).data
    class Meta:
        model = models.Conversation
        fields = ["id","name", "approved", "room_type", "profiles", "created_at", "message_limit", "settings", "requests", "last_message", "unread_messages"]
class MessageInfoForLastMessageSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer()
    conversation = ConversationSerializer()
    file = AttachmentInfoSerializer(many=True)
    reaction_summary = serializers.SerializerMethodField()
    def get_reaction_summary(self, obj):
        """Counts reactions per message and returns the list"""

        reactions = obj.message_reaction.values("reaction__reaction").annotate(count=Count("id")).order_by("-count")
        return [{"reaction": r["reaction__reaction"], "count": r["count"]} for r in reactions]
    class Meta:
        model = models.Message
        depth = 1
        fields = "__all__"

class ConversationInfoSerializer(serializers.ModelSerializer):
    settings = serializers.SerializerMethodField()
    requests = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_messages = serializers.SerializerMethodField()

    def get_unread_messages(self, obj):
        if obj.messages.filter(is_active=True).exists():
            return obj.messages.count()
        return 0
    
    def get_last_message(self, obj):
        if obj.messages.filter(is_active=True).exists():
            return MessageInfoForLastMessageSerializer(
                obj.messages.filter(is_active=True).order_by("-created_at").first()
            ).data
        return []
    
    def get_requests(self, obj):
        request = self.context.get("request")
        other_profile = obj.profiles.exclude(id=request.user.id).first()

        sent_requests = models.Request.objects.filter(sender = request.user, receiver = other_profile)
        received_requests = models.Request.objects.filter(sender = other_profile, receiver = request.user)
        all_requests = sent_requests | received_requests
        if request and request.user:
            return RequestSerializer(all_requests, many=True).data
        
    def get_settings(self, obj):
        request = self.context.get("request")

        if request and request.user:
            return ConversationSettingsInfoSerializer(
                obj.settings.exclude(profile=request.user),  # Filter settings here
                many=True
            ).data
        return ConversationSettingsInfoSerializer(obj.settings, many=True).data
    
    class Meta:
        model = models.Conversation
        depth = 1
        fields = ["id","name", "approved", "room_type", "profiles", "created_at", "message_limit", "settings", "requests", "last_message", "unread_messages"]

class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Follower
        fields = "__all__"


class FollowerInfoSerializer(serializers.ModelSerializer):
    follower = ProfileInfoSerializer()
    following = ProfileInfoSerializer()
    class Meta:
        model = models.Follower
        depth = 1
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    # sender = ProfileSerializer()
    # conversation = ConversationSerializer()
    reaction_summary = serializers.SerializerMethodField()
    def get_reaction_summary(self, obj):
        """Counts reactions per message and returns the list"""

        reactions = obj.message_reaction.values("reaction__reaction").annotate(count=Count("id")).order_by("-count")
        return [{"reaction": r["reaction__reaction"], "count": r["count"]} for r in reactions]

    class Meta:
        model = models.Message
        fields = "__all__"


class MessageInfoSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer()
    conversation = ConversationSerializer()
    file = AttachmentInfoSerializer(many=True)
    reaction_summary = serializers.SerializerMethodField()
    def get_reaction_summary(self, obj):
        """Counts reactions per message and returns the list"""

        reactions = obj.message_reaction.values("reaction__reaction").annotate(count=Count("id")).order_by("-count")
        return [{"reaction": r["reaction__reaction"], "count": r["count"]} for r in reactions]
    class Meta:
        model = models.Message
        depth = 1
        fields = "__all__"


class MessageReactSerializer(serializers.ModelSerializer):
    # sender = ProfileSerializer()
    # conversation = ConversationSerializer()
    # reaction_summary = serializers.SerializerMethodField()
    class Meta:
        model = models.MessageReact
        fields = ["id", "created_at", "updated_at", "is_active", "message", "reacted_by", "reaction"]
    # def get_reaction_summary(self, obj):
    #     """Counts reactions per message and returns the list"""
    #     reactions = models.MessageReact.objects.filter(message=obj.message) \
    #         .values("reaction__reaction") \
    #         .annotate(count=Count("id")) \
    #         .order_by("-count")  # Order by most used reactions

    #     return [{"reaction": r["reaction__reaction"], "count": r["count"]} for r in reactions]

class MessageReactInfoSerializer(serializers.ModelSerializer):
    # reaction_summary = serializers.SerializerMethodField()
    class Meta:
        model = models.MessageReact
        depth = 1
        fields = ["id", "created_at", "updated_at", "is_active", "message", "reacted_by", "reaction"]
    # def get_reaction_summary(self, obj):
    #     """Counts reactions per message and returns the list"""
    #     reactions = models.MessageReact.objects.filter(message=obj.message) \
    #         .values("reaction__reaction") \
    #         .annotate(count=Count("id")) \
    #         .order_by("-count")  # Order by most used reactions

    #     return [{"reaction": r["reaction__reaction"], "count": r["count"]} for r in reactions]
class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Request
        fields = "__all__"


class RequestInfoSerializer(serializers.ModelSerializer):
    # sender = ProfileSerializer(read_only=True)
    # receiver = ProfileSerializer(read_only=True)
    class Meta:
        model = models.Request
        depth = 1
        fields = "__all__"
