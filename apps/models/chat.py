import uuid
from django.db import models
from django.core.exceptions import ValidationError
from . import BaseModel


class Profile(BaseModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    # profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} - {self.last_name}"
class Follower(models.Model):
    follower = models.ForeignKey(Profile, related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey(Profile, related_name="followers", on_delete=models.CASCADE)
    is_mutual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

class Conversation(models.Model):
    ROOM_TYPE_CHOICES = [
        ('private', 'Private'),
        ('group', 'Group'),
    ]
    name = models.CharField(max_length=255, blank=True, null=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPE_CHOICES, default="private")
    profiles = models.ManyToManyField(Profile, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Room {self.id}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="messages")
    content = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} in Room {self.conversation.id}"

class MessageSettings(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="profile")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="conversation")
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
class Request(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')



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
