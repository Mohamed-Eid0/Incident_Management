# Real-Time WebSocket Notifications Setup Guide

## Overview
The Incident Management System now includes real-time notifications using WebSockets with Django Channels, Daphne (ASGI server), and Redis.

---

## Prerequisites

### 1. Install Redis
**Windows:**
- Download from: https://github.com/tporadowski/redis/releases
- Install and run Redis server
- Default port: 6379

**Linux/Mac:**
```bash
sudo apt-get install redis-server
redis-server
```

### 2. Install Python Packages
```bash
pip install -r requirements.txt
```

Packages installed:
- `channels>=4.0.0` - WebSocket support
- `daphne>=4.0.0` - ASGI server
- `channels-redis>=4.1.0` - Redis channel layer
- `redis>=5.0.0` - Redis client

---

## Configuration

### 1. Settings (Already Configured)
File: `Incident/settings.py`

```python
INSTALLED_APPS = [
    ...
    'daphne',  # Must be first
    'channels',
    ...
]

ASGI_APPLICATION = 'Incident.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### 2. ASGI Configuration (Already Configured)
File: `Incident/asgi.py`

Handles both HTTP and WebSocket protocols with JWT authentication.

---

## Running the Server

### Development Mode
```bash
# Start Redis server (in separate terminal)
redis-server

# Run Django with Daphne (ASGI)
daphne -b 0.0.0.0 -p 8000 Incident.asgi:application

# Alternative: Use manage.py
python manage.py runserver
```

### Check if Redis is Running
```bash
redis-cli ping
# Should return: PONG
```

---

## WebSocket Connection

### Endpoint
```
ws://localhost:8000/ws/notifications/?token=<jwt_access_token>
```

### Authentication
- Token is passed as query parameter
- Uses JWT access token from login endpoint
- Connection rejected if token is invalid or missing

---

## Client Implementation Examples

### 1. JavaScript/HTML
```html
<!DOCTYPE html>
<html>
<head>
    <title>Real-time Notifications</title>
</head>
<body>
    <h1>Notifications</h1>
    <div id="notifications"></div>

    <script>
        // Get JWT token from login
        const accessToken = 'your_jwt_access_token_here';
        
        // Connect to WebSocket
        const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${accessToken}`);
        
        ws.onopen = function(e) {
            console.log('Connected to notifications');
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('Notification received:', data);
            
            // Display notification
            const notifDiv = document.getElementById('notifications');
            const notifElement = document.createElement('div');
            notifElement.innerHTML = `
                <strong>${data.notification_type}</strong>: ${data.message}
                <br>Ticket ID: ${data.ticket.id}
                <br>Time: ${data.timestamp}
                <hr>
            `;
            notifDiv.prepend(notifElement);
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = function(event) {
            console.log('Disconnected from notifications');
        };
        
        // Keep connection alive (ping every 30 seconds)
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                }));
            }
        }, 30000);
    </script>
</body>
</html>
```

### 2. Flutter (Dart)
```dart
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';

class NotificationService {
  WebSocketChannel? _channel;
  String accessToken;
  
  NotificationService(this.accessToken);
  
  void connect() {
    final wsUrl = 'ws://localhost:8000/ws/notifications/?token=$accessToken';
    
    _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
    
    _channel!.stream.listen(
      (message) {
        final data = jsonDecode(message);
        print('Notification: ${data['message']}');
        
        // Handle different notification types
        switch (data['notification_type']) {
          case 'ticket_created':
            _handleTicketCreated(data);
            break;
          case 'ticket_assigned':
            _handleTicketAssigned(data);
            break;
          case 'work_started':
            _handleWorkStarted(data);
            break;
          case 'work_finished':
            _handleWorkFinished(data);
            break;
          case 'ticket_approved':
            _handleTicketApproved(data);
            break;
          case 'ticket_rejected':
            _handleTicketRejected(data);
            break;
        }
      },
      onError: (error) {
        print('WebSocket error: $error');
      },
      onDone: () {
        print('WebSocket connection closed');
      },
    );
  }
  
  void _handleTicketCreated(Map<String, dynamic> data) {
    // Show notification to admin
    showNotification(
      title: 'New Ticket',
      body: data['message'],
    );
  }
  
  void _handleTicketAssigned(Map<String, dynamic> data) {
    // Show notification to developer
    showNotification(
      title: 'Ticket Assigned',
      body: data['message'],
    );
  }
  
  void _handleWorkStarted(Map<String, dynamic> data) {
    // Show notification to client
    showNotification(
      title: 'Work Started',
      body: data['message'],
    );
  }
  
  void _handleWorkFinished(Map<String, dynamic> data) {
    // Show notification to client
    showNotification(
      title: 'Work Completed',
      body: data['message'],
    );
  }
  
  void _handleTicketApproved(Map<String, dynamic> data) {
    // Show notification to admin/developer
    showNotification(
      title: 'Ticket Approved',
      body: data['message'],
    );
  }
  
  void _handleTicketRejected(Map<String, dynamic> data) {
    // Show notification to admin/developer
    showNotification(
      title: 'Ticket Rejected',
      body: data['message'],
    );
  }
  
  void showNotification({required String title, required String body}) {
    // Use flutter_local_notifications package
    // Implementation depends on your notification setup
  }
  
  void disconnect() {
    _channel?.sink.close();
  }
  
  // Send ping to keep connection alive
  void sendPing() {
    _channel?.sink.add(jsonEncode({
      'type': 'ping',
      'timestamp': DateTime.now().toIso8601String(),
    }));
  }
}

// Usage
void main() {
  final token = 'your_jwt_access_token';
  final notificationService = NotificationService(token);
  notificationService.connect();
  
  // Keep alive timer
  Timer.periodic(Duration(seconds: 30), (timer) {
    notificationService.sendPing();
  });
}
```

### 3. Python Client
```python
import websocket
import json
import threading
import time

class NotificationClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.ws = None
        
    def on_message(self, ws, message):
        data = json.loads(message)
        print(f"Notification: {data['message']}")
        print(f"Type: {data['notification_type']}")
        print(f"Ticket: {data['ticket']}")
        print("-" * 50)
        
    def on_error(self, ws, error):
        print(f"Error: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")
        
    def on_open(self, ws):
        print("Connected to notifications")
        
        # Start ping thread
        def send_ping():
            while True:
                time.sleep(30)
                try:
                    ws.send(json.dumps({
                        'type': 'ping',
                        'timestamp': time.time()
                    }))
                except:
                    break
        
        ping_thread = threading.Thread(target=send_ping)
        ping_thread.daemon = True
        ping_thread.start()
    
    def connect(self):
        ws_url = f"ws://localhost:8000/ws/notifications/?token={self.access_token}"
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        self.ws.run_forever()

# Usage
if __name__ == "__main__":
    token = "your_jwt_access_token"
    client = NotificationClient(token)
    client.connect()
```

---

## Notification Types

### 1. ticket_created
**Sent to:** All admins  
**Trigger:** When client creates a new ticket  
**Payload:**
```json
{
  "notification_type": "ticket_created",
  "message": "New High priority ticket created: Homepage not loading",
  "ticket": {
    "id": 1,
    "title": "Homepage not loading",
    "priority": "HIGH",
    "priority_display": "High",
    "category": "BUG",
    "status": "NEW",
    "created_by": "John Client",
    "project_name": "Website Redesign",
    "created_at": "2025-12-23T10:00:00Z"
  },
  "timestamp": "2025-12-23T10:00:00Z"
}
```

### 2. ticket_opened
**Sent to:** Ticket creator (client)  
**Trigger:** When admin opens/acknowledges ticket  
**Payload:**
```json
{
  "notification_type": "ticket_opened",
  "message": "Your ticket 'Homepage not loading' has been opened and acknowledged by admin",
  "ticket": {
    "id": 1,
    "title": "Homepage not loading",
    "status": "OPENED",
    "status_display": "Opened",
    "opened_at": "2025-12-23T10:05:00Z"
  },
  "timestamp": "2025-12-23T10:05:00Z"
}
```

### 3. ticket_assigned
**Sent to:** Assigned developer(s)  
**Trigger:** When admin assigns developer(s) to ticket  
**Payload:**
```json
{
  "notification_type": "ticket_assigned",
  "message": "You have been assigned to ticket: Homepage not loading",
  "ticket": {
    "id": 1,
    "title": "Homepage not loading",
    "description": "The homepage returns 500 error",
    "priority": "HIGH",
    "priority_display": "High",
    "category": "BUG",
    "status": "OPENED",
    "assigned_to_names": ["Alice Developer", "Bob Support"],
    "created_by": "John Client",
    "project_name": "Website Redesign",
    "resolution_due_at": "2025-12-24T18:00:00Z"
  },
  "timestamp": "2025-12-23T10:10:00Z"
}
```

### 4. work_started
**Sent to:** Ticket creator (client)  
**Trigger:** When developer starts working (status: IN_PROGRESS)  
**Payload:**
```json
{
  "notification_type": "work_started",
  "message": "Work has started on your ticket: Homepage not loading",
  "ticket": {
    "id": 1,
    "title": "Homepage not loading",
    "status": "IN_PROGRESS",
    "status_display": "In Progress",
    "started_at": "2025-12-23T10:30:00Z"
  },
  "timestamp": "2025-12-23T10:30:00Z"
}
```

### 5. work_finished
**Sent to:** Ticket creator (client)  
**Trigger:** When developer finishes work (status: RESOLVED)  
**Payload:**
```json
{
  "notification_type": "work_finished",
  "message": "Work completed on your ticket 'Homepage not loading'. Please review and approve.",
  "ticket": {
    "id": 1,
    "title": "Homepage not loading",
    "status": "RESOLVED",
    "status_display": "Resolved",
    "resolved_at": "2025-12-23T14:00:00Z"
  },
  "timestamp": "2025-12-23T14:00:00Z"
}
```

### 6. ticket_approved
**Sent to:** All admins + assigned developers  
**Trigger:** When client approves resolved ticket  
**Payload:**
```json
{
  "notification_type": "ticket_approved",
  "message": "Ticket 'Homepage not loading' has been approved and closed by client",
  "ticket": {
    "id": 1,
    "title": "Homepage not loading",
    "status": "CLOSED",
    "status_display": "Closed",
    "closed_at": "2025-12-23T15:00:00Z",
    "created_by": "John Client"
  },
  "timestamp": "2025-12-23T15:00:00Z"
}
```

### 7. ticket_rejected
**Sent to:** All admins + assigned developers  
**Trigger:** When client rejects resolved ticket  
**Payload:**
```json
{
  "notification_type": "ticket_rejected",
  "message": "Ticket 'Homepage not loading' has been rejected by client. Reason: Issue still exists on mobile",
  "ticket": {
    "id": 1,
    "title": "Homepage not loading",
    "status": "IN_PROGRESS",
    "status_display": "In Progress",
    "created_by": "John Client",
    "rejection_comment": "Issue still exists on mobile"
  },
  "timestamp": "2025-12-23T15:00:00Z"
}
```

---

## Testing WebSocket Connection

### 1. Using Browser Console
```javascript
const token = 'your_access_token';
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${token}`);

ws.onopen = () => console.log('Connected');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.onerror = (e) => console.error('Error:', e);
ws.onclose = () => console.log('Closed');
```

### 2. Using Postman
1. Create new WebSocket request
2. URL: `ws://localhost:8000/ws/notifications/?token=<your_token>`
3. Click Connect
4. Watch for incoming messages

### 3. Using wscat (CLI)
```bash
npm install -g wscat
wscat -c "ws://localhost:8000/ws/notifications/?token=YOUR_TOKEN"
```

---

## Troubleshooting

### Connection Refused
- Check if Redis is running: `redis-cli ping`
- Check if Daphne is running on port 8000
- Verify token is valid and not expired

### No Notifications Received
- Check user role matches notification target
- Verify WebSocket connection is open
- Check Django logs for errors

### Token Expired
- Refresh JWT token using `/api/auth/refresh/`
- Reconnect with new access token

### Redis Connection Error
```python
# Check Redis connection
python manage.py shell
>>> from channels.layers import get_channel_layer
>>> channel_layer = get_channel_layer()
>>> from asgiref.sync import async_to_sync
>>> async_to_sync(channel_layer.send)('test_channel', {'type': 'test.message'})
```

---

## Production Deployment

### 1. Use Supervisor for Daphne
```ini
[program:daphne]
command=/path/to/venv/bin/daphne -b 0.0.0.0 -p 8000 Incident.asgi:application
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
```

### 2. Use Nginx as Reverse Proxy
```nginx
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://django;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 3. Use Redis Sentinel for High Availability
```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [
                "sentinel://sentinel1:26379",
                "sentinel://sentinel2:26379",
                "sentinel://sentinel3:26379",
            ],
            "master_name": "mymaster",
        },
    },
}
```

---

## Summary

**Real-time notifications are now active for:**
1. ✅ New ticket created → Admins notified
2. ✅ Ticket opened → Client notified
3. ✅ Ticket assigned → Developer(s) notified
4. ✅ Work started → Client notified
5. ✅ Work finished → Client notified
6. ✅ Ticket approved → Admin & developers notified
7. ✅ Ticket rejected → Admin & developers notified

**Architecture:**
- Django Channels for WebSocket protocol
- Daphne as ASGI server
- Redis as message broker/channel layer
- JWT authentication for WebSocket connections
- User-specific notification channels

**Last Updated:** December 23, 2025
