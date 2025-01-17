
import json
import logging
import urllib.parse
import datetime
from django.utils.dateformat import format
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from channels.layers import get_channel_layer

from channels.db import database_sync_to_async
from apps.models import Profile, Message
from apps.repositories import ProfileRepo

log = logging.getLogger("app")

class SocketConsumer(AsyncWebsocketConsumer):
    async def token_parser(self):
        raw_query = self.scope["query_string"]
        decoded_query = raw_query.decode("utf-8")
        query_params = urllib.parse.parse_qs(decoded_query)
        token = query_params.get("token", [None])[0]
        return token

    async def update_status(self, status):
        self.user.is_online = status
        self.user.last_seen = datetime.datetime.now() if not status else None
        await database_sync_to_async(self.user.save)()
            
    @database_sync_to_async
    def get_user_by_id(self, id: str):
        user = Profile.objects.get(id=id)
        user = None
        return user

    @database_sync_to_async
    def authenticate_user(self, token):
        repo = ProfileRepo(token)
        self.user = repo.verify_user_by_token()
        self.scope["user"] = self.user
        return self.user

    @database_sync_to_async
    def chat_messages_seen(self, data):
        Message.objects.filter(id__in=data["message_ids"]).update(read_status=True)

    async def connect(self):
        await self.accept()
        token = await self.token_parser()

        try:
            await self.authenticate_user(token)
        except Exception as e:
            log.error(str(e))
            await self.close()
            return


        self.chat_group = f"chat_{str(self.user.id)}"
        self.room_group_name = f"chat_{str(self.user.id)}"
        self.notification_group = f"notification_{str(self.user.id)}"
        self.activity_group = "activity"
        await self.channel_layer.group_add(self.chat_group, self.channel_name)
        await self.channel_layer.group_add(self.notification_group, self.channel_name)
        await self.channel_layer.group_add(self.activity_group, self.channel_name)
        await self.update_status(True)
    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            print("=="*100)
            print(text_data) 
            text_data_json = json.loads(text_data)

            await self.channel_layer.group_send(
                self.room_group_name,
                text_data_json
            )

    async def parser(self, event):
        await self.send(text_data=json.dumps({
            'data': event['message']
        }))
        
    async def seen(self, event):

        await self.send(text_data=json.dumps(
            event
        ))
    async def receive_typing(self, event): 

        await self.send(text_data=json.dumps({
            "type": "typing",
            'message': event['message']
        }))
        
    async def typing(self, event):
        op_id = event["op_id"]
        await self.channel_layer.group_send(
            f'chat_{op_id}',
            {
                "type": "receive_typing",
                "message": event['message'],
            }
        )
    
    async def messages_seen(self, event):
        self.chat_messages_seen(event)
        await self.channel_layer.group_send(
            f'chat_{event["receiver"]}',
            {
                'type': 'seen',
                "sender": event["sender"],
                'message': event['message_ids']
            }
        )

    async def disconnect(self, close_code):
        # await self.update_status(False)
        print("OKAy")
        await self.channel_layer.group_send(
            'activity',
            {
                'type': 'online_users',
            }
        )