# consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import Message, Interest
from asgiref.sync import sync_to_async
from django.db.models import Q

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        user = self.scope['user']
        room_name_parts = self.room_name.split('_')
        receiver_id = room_name_parts[1] if str(user.id) == room_name_parts[0] else room_name_parts[0]
        receiver = await sync_to_async(User.objects.get)(id=receiver_id)

        await self.save_message(user, receiver, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': user.username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender
        }))

    # @sync_to_async
    # def save_message(self, sender, receiver, message):
    #     interest = Interest.objects.get(
    #         Q(sender=sender, receiver=receiver) |
    #         Q(sender=receiver, receiver=sender)
    #     )
    #     Message.objects.create(interest=interest, sender=sender, receiver=receiver, content=message)
