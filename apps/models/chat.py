import os
import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import List, Dict, Any, Optional, DefaultDict, OrderedDict
from . import BaseModel
from apps.media_storage import MediaStorage

class Profile(BaseModel):
    user_id = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    is_online = models.BooleanField(default=False, null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} - {self.last_name}"
class Follower(BaseModel):
    follower = models.ForeignKey(Profile, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(Profile, related_name="followers", on_delete=models.CASCADE)
    is_mutual = models.BooleanField(default=False)

    class Meta:
        unique_together = ('follower', 'following')

    def mutual_friends(self):
        return Follower.objects.filter(follower=self.following, following=self.follower)

    def is_mutual_friend(self):
        return self.mutual_friends().exists()
    
    def save(self, *args, **kwargs):
        self.is_mutual_friend()
        super().save(*args, **kwargs)

class Conversation(BaseModel):
    PRIVATE = 'private'
    GROUP = 'group'
    ROOM_TYPE_CHOICES = [
        (PRIVATE, 'Private'),
        (GROUP, 'Group'),
    ]
    name = models.CharField(max_length=255, blank=True, null=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default="private")
    profiles = models.ManyToManyField(Profile, related_name="conversations")
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    message_limit = models.IntegerField(default=0)
    def __str__(self):
        return self.name or f"Room {self.id}"
    
    def profiles_count(self):
        return self.profiles.all().count()

    def more_than(self):
        return self.profiles.count() > 2
    
    def check_limit(self):
        if not self.message_limit >= 1:
            return True
        raise ValidationError("Message limit reached for this conversation.")
        
    def clean(self):
        if self.room_type == 'private' and not self.pk and self.more_than():
            raise ValidationError("A private conversation cannot have more than two participants.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        for profile in self.profiles.all():
            self.settings.get_or_create(profile=profile)

class Message(BaseModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, related_name="replies", null=True, blank=True)
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    forwarded_from = models.ForeignKey("self", on_delete=models.SET_NULL, related_name="forwards", null=True, blank=True)
    is_forwarded = models.BooleanField(default=False)
    file = models.ManyToManyField("apps.Attachments", related_name="messages", null=True, blank=True)
    def __str__(self):
        return f"Message from {self.sender} in Room {self.conversation.id}"

    def get_content(self) -> Dict[str, str]:
        """
            args:
                self
            Returns:
                Dict[str, str]: {content, }.
        """
        return {
            "content": self.content,

        }
    def receiver(self):
        if not self.conversation_id:
            raise ValidationError("Message must have a conversation to determine the receiver.")
        
        participants = self.conversation.profiles.all()
        if len(participants) != 2:
            raise ValidationError("This message can only be sent in a conversation with two participants.")
        
        receiver = participants.exclude(id=self.sender.id).first()
        return receiver or None


    def can_send(self) -> bool:
        if self.conversation.approved or self.conversation.message_limit == 0:
            return True
        return False
    
    def is_conversation_blocked(self):
        settings: ConversationSettings = self.conversation.settings
        op_user_settings = settings.exclude(profile=self.sender).first()
        current_user_settings = settings.filter(profile=self.sender).first()

        if op_user_settings.is_blocked:
            raise ValidationError("You can't send a message to this user, you are blocked")
        
        if current_user_settings.is_blocked:
            raise ValidationError("You can't send a message to this user, you blocked this conversation.")
        


    def clean(self):
        if not self.can_send():
            raise ValidationError("You can't send a message to this user yet.")
        self.check_request_status()

    def check_request_status(self):
        receiver = self.receiver()
        if not receiver:
            raise ValidationError("Receiver not found.")

        existing_request = Request.objects.filter(
            models.Q(sender=self.sender, receiver=receiver) |
            models.Q(sender=receiver, receiver=self.sender)
        ).first()
        if existing_request and existing_request.status == 'blocked':
            raise ValidationError("You cannot send a message due to a blocked request.")


    def save(self, *args, **kwargs):
        self.clean()
        self.is_conversation_blocked()
        super().save(*args, **kwargs)

        if self.conversation.message_limit == 0:
            self.conversation.message_limit += 1
            self.conversation.save()
class Reaction(BaseModel):
    reaction = models.CharField(max_length=255)

class MessageReact(BaseModel):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="message_reaction")
    reacted_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="profile_reactions")
    reaction = models.ForeignKey(Reaction, on_delete=models.CASCADE, related_name="reactions")
    def __str__(self):
        return f"{self.reacted_by} - {self.reaction.reaction} on Message {self.message.id}"

    
class ConversationSettings(BaseModel):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="conversation_settings")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="settings")
    is_muted = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_trashed = models.BooleanField(default=False)
    last_muted_at = models.DateTimeField(null=True, blank=True)
    last_blocked_at = models.DateTimeField(null=True, blank=True)
    last_trashed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('profile', 'conversation')

    def __str__(self):
        return f"{self.profile.first_name} - {self.conversation}"
    

    def save(self, *args, **kwargs):

        if self.is_muted and not self.last_muted_at:
            self.last_muted_at = timezone.now()
        elif not self.is_muted:
            self.last_muted_at = None

        if self.is_blocked and not self.last_blocked_at:
            self.last_blocked_at = timezone.now()
        elif not self.is_blocked:
            self.last_blocked_at = None

        if self.is_trashed and not self.last_trashed_at:
            self.last_trashed_at = timezone.now()
        elif not self.is_trashed:
            self.last_trashed_at = None

        super().save(*args, **kwargs)

class Request(BaseModel):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="sent_requests")
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="received_requests")
    status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('blocked', 'Blocked'),
            ('deleted', 'Deleted'),
            ('hidden', 'Hidden'),
        ],
        default='pending'
    )
    class Meta:
        unique_together = ('sender', 'receiver')
    
    def can_send_message(self):
        if self.status == 'pending':
            raise ValidationError("You can't send a message until the recipient accepts your request.")
        return True

class Attachments(BaseModel):
    file = models.FileField(storage=MediaStorage(), upload_to='chat_media/')
    original_name = models.CharField(max_length=255, blank=True, null=True)  
    file_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)  

    def upload_to_dynamic(self, field_name, filename):
        """Generate a dynamic upload path using the specified field name."""
        unique_filename = f"{uuid.uuid4()}_{filename}" 
        return f"{field_name}/{unique_filename}"

    def save(self, *args, **kwargs):
        if self.file:
            field_name = kwargs.pop('field_name', 'attachments')  # Default to 'attachments'
            self.file.name = self.upload_to_dynamic(field_name, self.file.name)  # Set the file name dynamically

            self.original_name = self.file.name  # Store original file name
            self.file_type = os.path.splitext(self.file.name)[1]  # Extract file extension
            self.file_size = self.file.size
        super().save(*args, **kwargs)
