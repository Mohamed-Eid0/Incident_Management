# 🔔 Notification System Guide for Frontend/Flutter Developers

## 📋 Table of Contents
1. [Overview](#overview)
2. [Notification Channels](#notification-channels)
3. [Notification Triggers & Lifecycle](#notification-triggers--lifecycle)
4. [API Endpoints](#api-endpoints)
5. [WebSocket Integration](#websocket-integration)
6. [Frontend Implementation Guide](#frontend-implementation-guide)
7. [Best Practices](#best-practices)

---

## 🎯 Overview

The Incident Management System uses a **triple-channel notification system**:

- **📧 Email** - Permanent record, detailed information
- **📱 WhatsApp** - Mobile alerts (requires phone number setup)
- **🔔 WebSocket** - Real-time in-app notifications

**Key Features:**
- ✅ Real-time delivery via WebSocket
- ✅ Persistent storage in database
- ✅ Read/unread tracking
- ✅ Filtering and pagination
- ✅ Role-based notification targeting

---

## 📢 Notification Channels

### 1. **Email Notifications** 📧
- **Delivery Time:** 1-5 seconds
- **Persistence:** Permanent (user's inbox)
- **Use Case:** Detailed updates, audit trail
- **Requires:** Valid email address

### 2. **WhatsApp Notifications** 📱
- **Delivery Time:** 2-10 seconds
- **Persistence:** User's WhatsApp history
- **Use Case:** Urgent alerts, mobile accessibility
- **Requires:** `whatsapp_number` in user profile

### 3. **WebSocket Notifications** 🔔
- **Delivery Time:** Instant (<100ms)
- **Persistence:** Stored in `NotificationLog` database table
- **Use Case:** Real-time UI updates, badges, popups
- **Requires:** Active WebSocket connection

---

## ⚡ Notification Triggers & Lifecycle

### **Trigger Flow:**

```
User Action → View Endpoint → Notification Service → Multiple Channels
                                                    ├─ Email (async)
                                                    ├─ WhatsApp (async)
                                                    └─ WebSocket (instant)
```

### **Notification Lifecycle:**

1. **Created** - Action occurs (ticket created, assigned, etc.)
2. **Sent** - Notification dispatched to all channels
3. **Stored** - Saved to `NotificationLog` table with `is_read=False`
4. **Delivered** - User receives notification
5. **Read** - User marks as read (updates `is_read=True`, sets `read_at`)
6. **Archived** - Old notifications (optional cleanup)

---

## 🚨 Notification Types & Recipients

| Event | Notification Type | Recipients | Channels |
|-------|------------------|-----------|----------|
| **New Ticket Created** | `ticket_created` | All Admins | Email + WhatsApp + WebSocket |
| **Ticket Opened** | `ticket_opened` | Ticket Creator (Client) | Email + WhatsApp + WebSocket |
| **Ticket Assigned** | `ticket_assigned` | Assigned Developers | Email + WhatsApp + WebSocket |
| **Work Started** | `work_started` | Ticket Creator (Client) | Email + WhatsApp + WebSocket |
| **Work Finished** | `work_finished` | Client + All Admins | Email + WhatsApp + WebSocket |
| **Ticket Approved** | `ticket_approved` | Admins + Assigned Devs | WebSocket + WhatsApp |
| **Ticket Rejected** | `ticket_rejected` | Admins + Assigned Devs | WebSocket + WhatsApp |

---

## 🌐 API Endpoints

### **Base URL:** `http://your-domain.com/api/notifications/`

### 1. **Get All Notifications**

```http
GET /api/notifications/
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `is_read` - Filter by read status (`true` or `false`)
- `notification_type` - Filter by type (`EMAIL`, `WHATSAPP`, `SYSTEM`)
- `ticket` - Filter by ticket ID
- `page` - Pagination (default: 1)
- `page_size` - Results per page (default: 20)

**Response:**
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "ticket": 5,
      "ticket_title": "Homepage not loading",
      "recipient": 1,
      "recipient_name": "John Admin",
      "notification_type": "SYSTEM",
      "notification_type_display": "System Alert",
      "subject": "New Ticket Created",
      "message": "New High priority ticket created: Homepage not loading",
      "status": "SENT",
      "status_display": "Sent",
      "sent_at": "2025-12-24T10:30:00Z",
      "created_at": "2025-12-24T10:30:00Z",
      "is_read": false,
      "read_at": null
    }
  ]
}
```

---

### 2. **Get Unread Notifications**

```http
GET /api/notifications/unread/
Authorization: Bearer <access_token>
```

**Response:** Same as above, but only unread notifications

**Alternative:** Use `GET /api/notifications/?is_read=false`

---

### 3. **Get Unread Count**

```http
GET /api/notifications/unread_count/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "count": 5,
  "by_type": {
    "EMAIL": 2,
    "WHATSAPP": 1,
    "SYSTEM": 2
  }
}
```

**Use Case:** Display badge on notification bell icon

---

### 4. **Mark Single Notification as Read**

```http
POST /api/notifications/{id}/mark_as_read/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Notification marked as read",
  "notification": {
    "id": 123,
    "is_read": true,
    "read_at": "2025-12-24T14:25:30Z",
    ...
  }
}
```

---

### 5. **Mark All Notifications as Read**

```http
POST /api/notifications/mark_all_as_read/
Authorization: Bearer <access_token>
```

**Optional Query Parameters:**
- `notification_type` - Only mark specific type as read
- `ticket` - Only mark notifications for specific ticket

**Response:**
```json
{
  "message": "5 notification(s) marked as read",
  "count": 5
}
```

---

## 🔌 WebSocket Integration

### **WebSocket Connection:**

**URL:** `ws://your-domain.com/ws/notifications/?token=<jwt_access_token>`

**Protocol:** WebSocket (RFC 6455)

---

### **Connection Flow:**

```javascript
// 1. Connect with JWT token
const ws = new WebSocket(`ws://localhost:8000/ws/notifications/?token=${accessToken}`);

// 2. Handle connection
ws.onopen = () => {
  console.log('Connected to notification system');
};

// 3. Receive notifications
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  handleNotification(data);
};

// 4. Handle disconnection
ws.onclose = (event) => {
  console.log('Disconnected:', event.code);
  // Implement reconnection logic
};

// 5. Handle errors
ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

---

### **Message Types:**

#### **A. Connection Established**
```json
{
  "type": "connection_established",
  "message": "Connected successfully as john_admin",
  "user_id": 1
}
```

#### **B. Ticket Notification**
```json
{
  "notification_type": "ticket_created",
  "message": "New High priority ticket created: Homepage not loading",
  "ticket": {
    "id": 5,
    "title": "Homepage not loading",
    "priority": "HIGH",
    "priority_display": "High",
    "category": "BUG",
    "status": "NEW",
    "created_by": "John Client",
    "project_name": "Main Website",
    "created_at": "2025-12-24T10:30:00Z"
  },
  "timestamp": "2025-12-24T10:30:00Z"
}
```

#### **C. Ping/Pong (Heartbeat)**
```javascript
// Send ping to keep connection alive
ws.send(JSON.stringify({
  type: 'ping',
  timestamp: Date.now()
}));

// Receive pong
{
  "type": "pong",
  "timestamp": 1735038600000
}
```

---

### **Notification Availability:**

#### **Storage Duration:**
- **Database:** Indefinite (until manually deleted/archived)
- **WebSocket:** Only during active connection
- **Email:** Permanent in user's inbox
- **WhatsApp:** Permanent in user's chat

#### **Access Pattern:**
```
┌─────────────────────────────────────────────────┐
│  User Action                                    │
│  (e.g., Ticket Created)                         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │  Notifications Sent   │
     └───────┬───────────────┘
             │
   ┌─────────┼─────────┬─────────────┐
   │         │         │             │
   ▼         ▼         ▼             ▼
Email    WhatsApp  WebSocket   Database
(Inbox)   (Chat)   (If online)  (Persistent)
                        │
                        ▼
                 User offline?
                        │
                        ▼
                 Stored in DB
                 Retrieved on login
```

**Key Points:**
- ✅ **Real-time notifications** delivered instantly if user is online
- ✅ **Missed notifications** can be retrieved from database via API
- ✅ **No expiration** - notifications stay until marked as read/deleted
- ✅ **Offline support** - fetch missed notifications on reconnect

---

## 💻 Frontend Implementation Guide

### **React/Vue/Angular Example:**

```javascript
class NotificationService {
  constructor(apiUrl, wsUrl, accessToken) {
    this.apiUrl = apiUrl;
    this.wsUrl = wsUrl;
    this.accessToken = accessToken;
    this.ws = null;
    this.listeners = [];
  }

  // Connect to WebSocket
  connect() {
    this.ws = new WebSocket(`${this.wsUrl}?token=${this.accessToken}`);
    
    this.ws.onopen = () => {
      console.log('✅ Notification service connected');
      this.startHeartbeat();
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'connection_established') {
        console.log('User ID:', data.user_id);
      } else if (data.notification_type) {
        // Real-time notification received
        this.notifyListeners(data);
        this.showNotification(data);
      }
    };
    
    this.ws.onclose = () => {
      console.log('❌ Notification service disconnected');
      // Reconnect after 5 seconds
      setTimeout(() => this.connect(), 5000);
    };
  }

  // Keep connection alive
  startHeartbeat() {
    setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      }
    }, 30000); // Every 30 seconds
  }

  // Subscribe to notifications
  subscribe(callback) {
    this.listeners.push(callback);
  }

  // Notify all listeners
  notifyListeners(notification) {
    this.listeners.forEach(callback => callback(notification));
  }

  // Show browser notification
  showNotification(data) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(data.message, {
        body: data.ticket?.title,
        icon: '/notification-icon.png',
        tag: `ticket-${data.ticket?.id}`
      });
    }
  }

  // Fetch all notifications
  async getNotifications(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${this.apiUrl}/notifications/?${params}`, {
      headers: { 'Authorization': `Bearer ${this.accessToken}` }
    });
    return response.json();
  }

  // Get unread count
  async getUnreadCount() {
    const response = await fetch(`${this.apiUrl}/notifications/unread_count/`, {
      headers: { 'Authorization': `Bearer ${this.accessToken}` }
    });
    return response.json();
  }

  // Mark as read
  async markAsRead(notificationId) {
    const response = await fetch(`${this.apiUrl}/notifications/${notificationId}/mark_as_read/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.accessToken}` }
    });
    return response.json();
  }

  // Mark all as read
  async markAllAsRead() {
    const response = await fetch(`${this.apiUrl}/notifications/mark_all_as_read/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.accessToken}` }
    });
    return response.json();
  }
}

// Usage
const notificationService = new NotificationService(
  'http://localhost:8000/api',
  'ws://localhost:8000/ws/notifications/',
  'your-jwt-token'
);

notificationService.connect();

notificationService.subscribe((notification) => {
  console.log('New notification:', notification);
  // Update UI (e.g., increment badge count)
  updateNotificationBadge();
  showToast(notification.message);
});
```

---

### **Flutter/Dart Example:**

```dart
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class NotificationService {
  final String apiUrl;
  final String wsUrl;
  final String accessToken;
  WebSocketChannel? _channel;
  final _notificationController = StreamController<Map<String, dynamic>>.broadcast();

  NotificationService({
    required this.apiUrl,
    required this.wsUrl,
    required this.accessToken,
  });

  // Connect to WebSocket
  void connect() {
    _channel = WebSocketChannel.connect(
      Uri.parse('$wsUrl?token=$accessToken'),
    );

    _channel!.stream.listen(
      (message) {
        final data = jsonDecode(message);
        
        if (data['type'] == 'connection_established') {
          print('✅ Connected: ${data['message']}');
        } else if (data['notification_type'] != null) {
          // Broadcast to all listeners
          _notificationController.add(data);
          _showLocalNotification(data);
        }
      },
      onError: (error) {
        print('❌ WebSocket error: $error');
        _reconnect();
      },
      onDone: () {
        print('❌ WebSocket closed');
        _reconnect();
      },
    );
  }

  // Reconnect after delay
  void _reconnect() {
    Future.delayed(Duration(seconds: 5), () {
      connect();
    });
  }

  // Send heartbeat ping
  void sendPing() {
    _channel?.sink.add(jsonEncode({
      'type': 'ping',
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    }));
  }

  // Subscribe to notifications
  Stream<Map<String, dynamic>> get notificationStream => _notificationController.stream;

  // Get all notifications
  Future<Map<String, dynamic>> getNotifications({Map<String, String>? filters}) async {
    final queryParams = filters != null ? '?${Uri(queryParameters: filters).query}' : '';
    final response = await http.get(
      Uri.parse('$apiUrl/notifications/$queryParams'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
    return jsonDecode(response.body);
  }

  // Get unread count
  Future<Map<String, dynamic>> getUnreadCount() async {
    final response = await http.get(
      Uri.parse('$apiUrl/notifications/unread_count/'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
    return jsonDecode(response.body);
  }

  // Mark as read
  Future<void> markAsRead(int notificationId) async {
    await http.post(
      Uri.parse('$apiUrl/notifications/$notificationId/mark_as_read/'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
  }

  // Mark all as read
  Future<void> markAllAsRead() async {
    await http.post(
      Uri.parse('$apiUrl/notifications/mark_all_as_read/'),
      headers: {'Authorization': 'Bearer $accessToken'},
    );
  }

  // Show local notification (using flutter_local_notifications)
  void _showLocalNotification(Map<String, dynamic> data) {
    // Implement with flutter_local_notifications package
  }

  void dispose() {
    _channel?.sink.close();
    _notificationController.close();
  }
}

// Usage in Flutter
class NotificationPage extends StatefulWidget {
  @override
  _NotificationPageState createState() => _NotificationPageState();
}

class _NotificationPageState extends State<NotificationPage> {
  final notificationService = NotificationService(
    apiUrl: 'http://localhost:8000/api',
    wsUrl: 'ws://localhost:8000/ws/notifications/',
    accessToken: 'your-jwt-token',
  );

  int unreadCount = 0;

  @override
  void initState() {
    super.initState();
    notificationService.connect();
    
    // Listen to real-time notifications
    notificationService.notificationStream.listen((notification) {
      setState(() {
        unreadCount++;
      });
      // Show snackbar or dialog
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(notification['message'])),
      );
    });
    
    _loadUnreadCount();
  }

  Future<void> _loadUnreadCount() async {
    final result = await notificationService.getUnreadCount();
    setState(() {
      unreadCount = result['count'];
    });
  }

  @override
  void dispose() {
    notificationService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Notifications'),
        actions: [
          Stack(
            children: [
              IconButton(
                icon: Icon(Icons.notifications),
                onPressed: () {
                  // Navigate to notifications page
                },
              ),
              if (unreadCount > 0)
                Positioned(
                  right: 8,
                  top: 8,
                  child: Container(
                    padding: EdgeInsets.all(2),
                    decoration: BoxDecoration(
                      color: Colors.red,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    constraints: BoxConstraints(
                      minWidth: 16,
                      minHeight: 16,
                    ),
                    child: Text(
                      '$unreadCount',
                      style: TextStyle(color: Colors.white, fontSize: 10),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
      // ... rest of UI
    );
  }
}
```

---

## ✅ Best Practices

### **1. Connection Management**
- ✅ Connect on app start/login
- ✅ Reconnect automatically on disconnect
- ✅ Send heartbeat pings every 30 seconds
- ✅ Close connection on logout

### **2. Notification Handling**
- ✅ Show unread count badge on icon
- ✅ Play sound for important notifications (HIGH priority)
- ✅ Group notifications by ticket
- ✅ Mark as read when user views notification

### **3. Performance**
- ✅ Paginate notification list (20-50 per page)
- ✅ Cache unread count locally
- ✅ Lazy load notification details
- ✅ Use virtual scrolling for long lists

### **4. User Experience**
- ✅ Show toast/snackbar for real-time notifications
- ✅ Provide "Mark all as read" button
- ✅ Filter notifications by type/ticket
- ✅ Request browser notification permission

### **5. Error Handling**
- ✅ Gracefully handle WebSocket disconnections
- ✅ Retry failed API requests
- ✅ Show connection status indicator
- ✅ Fallback to polling if WebSocket fails

---

## 🔄 Typical User Flow

```
1. User logs in
   └─> Connect WebSocket with JWT token
   └─> Fetch unread count
   └─> Display badge on notification icon

2. User performs action (e.g., creates ticket)
   └─> Server sends notifications to relevant users
   └─> Recipient receives WebSocket message (if online)
   └─> Notification stored in database

3. User clicks notification icon
   └─> Fetch all notifications (paginated)
   └─> Display in notification panel
   └─> Show unread notifications first

4. User clicks on notification
   └─> Mark as read (API call)
   └─> Navigate to related ticket
   └─> Update unread count badge

5. User clicks "Mark all as read"
   └─> API call to mark_all_as_read
   └─> Clear badge count
   └─> Update UI

6. User logs out
   └─> Close WebSocket connection
   └─> Clear notification cache
```

---

## 🆘 Troubleshooting

### **WebSocket Connection Fails:**
- Check JWT token validity (not expired)
- Verify WebSocket URL (ws:// or wss://)
- Check CORS settings on server
- Ensure Redis is running (backend dependency)

### **Notifications Not Received:**
- Verify user role (notifications are role-specific)
- Check notification filters in API
- Ensure WebSocket connection is active
- Check backend logs for errors

### **High Latency:**
- Check network connection
- Verify Redis performance
- Monitor backend server load
- Consider CDN for WebSocket endpoint

---

## 📚 Additional Resources

- [Django Channels Documentation](https://channels.readthedocs.io/)
- [WebSocket API Reference](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Flutter WebSocket Guide](https://flutter.dev/docs/cookbook/networking/web-sockets)
- [React WebSocket Integration](https://react.dev/)

---

## 📞 Support

For questions or issues, contact the backend team or create an issue in the project repository.

**Happy Coding! 🚀**
