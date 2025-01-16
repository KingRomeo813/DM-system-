import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from . import BaseModel


class Profile(BaseModel):
    user_id = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255)
    is_online = models.BooleanField(default=False)
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
    ROOM_TYPE_CHOICES = [
        ('private', 'Private'),
        ('group', 'Group'),
    ]
    name = models.CharField(max_length=255, blank=True, null=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default="private")
    profiles = models.ManyToManyField(Profile, related_name="conversations")
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
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} in Room {self.conversation.id}"


    def receiver(self):
        if not self.conversation_id:
            raise ValidationError("Message must have a conversation to determine the receiver.")
        
        participants = self.conversation.profiles.all()
        if len(participants) != 2:
            raise ValidationError("This message can only be sent in a conversation with two participants.")
        
        receiver = participants.exclude(id=self.sender.id).first()
        return receiver or None


    def can_send(self):
        receiver = self.receiver()
        
        if receiver:
            request = self.sender.sent_requests.filter(receiver=receiver).first()
            if request and request.status == 'accepted':
                return True
            if request and self.conversation.check_limit():
                return True
            if not request:
                raise ValidationError("No request found between the users.")
            if request.status != 'accepted':
                raise ValidationError("You can't send a message until the recipient accepts your request.")
        
        return False
        
    def clean(self):
        if not self.can_send():
            raise ValidationError("You can't send a message to this user yet.")

    def save(self, *args, **kwargs):
        self.clean()
        
        super().save(*args, **kwargs)

        if self.conversation.message_limit == 0:
            self.conversation.message_limit += 1
            self.conversation.save()
            
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
    message = models.ForeignKey("apps.Message", on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to='uploads/')  # Default upload directory

    def upload_to_dynamic(self, field_name, filename):
        """Generate a dynamic upload path using the specified field name."""
        unique_filename = f"{uuid.uuid4()}_{filename}" 
        return f"{field_name}/{unique_filename}"

    def save(self, *args, **kwargs):
        if self.file:
            field_name = kwargs.pop('field_name', 'attachments')  # Default to 'attachments'
            self.file.name = self.upload_to_dynamic(field_name, self.file.name)  # Set the file name dynamically
        super().save(*args, **kwargs)
