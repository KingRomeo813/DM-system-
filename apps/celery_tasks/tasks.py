import json
import time
import logging
import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from celery import shared_task

from apps.models import Profile, Message
from apps.serializers import MessageSerializer
from services import UserService

log = logging.getLogger(__file__)

def default_converter(self, o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()

@shared_task
def send_messages(message_id: str, user_id: str):
    try:
        message = Message.objects.get(id=str(message_id))
        user = Profile.objects.get(id=str(user_id))

        serializer = MessageSerializer(message)
        serialized_data = json.dumps(serializer.data, default=default_converter)

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'chat_{user.id}',
            {
                'type': 'chat_message',
                'message': serialized_data,
            }
        )
        log.info(f"Message sent to chat group: chat_{user.id}")

    except Message.DoesNotExist:
        log.error(f"Message with ID {message_id} does not exist.")
    except Profile.DoesNotExist:
        log.error(f"User with ID {user_id} does not exist.")
    except Exception as e:
        log.error(f"Error sending real-time chat message: {e}")