"""
WebSocket Consumer for Real-time Notifications

Usage (JavaScript/Flutter):
1. Connect: ws://localhost:8000/ws/notifications/?token=<jwt_access_token>
2. Listen for messages
3. Receive notifications in JSON format

Notification Types:
- ticket_created
- ticket_opened
- ticket_assigned
- work_started
- work_finished
- ticket_approved
- ticket_rejected
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications
    Each user has their own channel group based on user ID
    """
    
    async def connect(self):
        """
        Called when WebSocket connection is established
        """
        self.user = self.scope['user']
        
        # Reject anonymous users
        if isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Create user-specific group name
        self.user_group_name = f'user_{self.user.id}'
        
        # Join user's notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected successfully as {self.user.username}',
            'user_id': self.user.id
        }))
    
    async def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed
        """
        if hasattr(self, 'user_group_name'):
            # Leave user's notification group
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Called when message is received from WebSocket
        Can be used for ping/pong or other client messages
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
        except json.JSONDecodeError:
            pass
    
    async def send_notification(self, event):
        """
        Called when notification is sent to this consumer's group
        Receives message from channel layer and sends to WebSocket
        """
        # Send notification to WebSocket
        await self.send(text_data=json.dumps(event['data']))
