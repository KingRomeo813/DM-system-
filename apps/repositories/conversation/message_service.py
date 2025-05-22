from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from apps.models.chat import Message, Conversation, Request


def validate_and_create_message(data, user):
    conversation_id = data.get("conversation")
    if not conversation_id:
        raise ValidationError("Conversation ID is required.")

    conversation = get_object_or_404(Conversation, id=conversation_id)

    # Determine receiver from conversation
    receiver = next((profile for profile in conversation.profiles.all() if profile != user), None)
    if not receiver:
        raise ValidationError("Receiver not found in this conversation.")

    # Get existing request
    request_qs = Request.objects.filter(
        Q(sender=user, receiver=receiver) | Q(sender=receiver, receiver=user)
    ).order_by("-created_at")
    if request_qs.exists():
        relationship = request_qs.first()

        if relationship.status == "blocked":
            # breakpoint()
            raise PermissionDenied("You are blocked from sending messages to this user.")

        elif relationship.status == "pending":
            already_sent = Message.objects.filter(sender=user, conversation=conversation).exists()
            if already_sent:
                raise PermissionDenied("You can only send one message while the request is pending.")

        elif relationship.status == "hidden":
            already_sent = Message.objects.filter(sender=user, conversation=conversation).exists()
            if already_sent:
                raise PermissionDenied("Message request is already sent!")

    # Passed validation
    return conversation, receiver
