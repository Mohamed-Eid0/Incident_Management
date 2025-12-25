# Incident Management System - API Documentation

**Base URL:** `http://localhost:8000/api/`

**Authentication:** JWT Bearer Token (pass in `Authorization` header as `Bearer <access_token>`)

---

## Table of Contents

1. [Authentication APIs](#authentication-apis)
2. [Admin APIs](#admin-apis)
3. [Developer APIs](#developer-apis)
4. [Client APIs](#client-apis)
5. [Common APIs (All Roles)](#common-apis-all-roles)

---

## Authentication APIs

### 1. Login
**Endpoint:** `POST /api/auth/login/`  
**Permission:** Public (No authentication required)  
**Description:** Authenticate user and get JWT tokens

**Request Body:**
```json
{
  "username": "admin_user",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin_user",
    "email": "admin@company.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "ADMIN",
    "phone_number": "+1234567890",
    "whatsapp_number": "+1234567890",
    "department": "IT Management"
  }
}
```

**Note:** Access token expires in 2 hours, refresh token expires in 2 days

---

### 2. Refresh Token
**Endpoint:** `POST /api/auth/refresh/`  
**Permission:** Public  
**Description:** Get new access token using refresh token

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Admin APIs

### 1. List All Tickets
**Endpoint:** `GET /api/tickets/`  
**Permission:** Admin, Developer (sees assigned only), Client (sees created only)  
**Description:** Get list of all tickets based on role

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "project_name": "Website Redesign",
    "title": "Homepage not loading",
    "description": "The homepage returns 500 error",
    "priority": "HIGH",
    "priority_display": "High",
    "category": "BUG",
    "category_display": "Bug",
    "status": "IN_PROGRESS",
    "status_display": "In Progress",
    "created_by": 5,
    "created_by_name": "John Client",
    "assigned_to": [2, 3],
    "assigned_to_names": ["Alice Developer", "Bob Support"],
    "assigned_team": "Backend Team",
    "response_due_at": "2025-12-23T10:30:00Z",
    "resolution_due_at": "2025-12-24T18:00:00Z",
    "response_breached": false,
    "resolution_breached": false,
    "response_sla_minutes": 30,
    "estimated_resolution_time": "2025-12-24T15:00:00Z",
    "created_at": "2025-12-23T10:00:00Z",
    "updated_at": "2025-12-23T11:00:00Z",
    "opened_at": "2025-12-23T10:05:00Z",
    "started_at": "2025-12-23T10:30:00Z",
    "resolved_at": null,
    "closed_at": null,
    "attachments": [],
    "history": []
  }
]
```

---

### 2. Get Ticket Details
**Endpoint:** `GET /api/tickets/{id}/`  
**Permission:** Admin (all), Developer (assigned only), Client (created only)  
**Description:** Get detailed ticket information including attachments and history

**Response (200 OK):**
```json
{
  "id": 1,
  "project_name": "Website Redesign",
  "title": "Homepage not loading",
  "description": "The homepage returns 500 error when accessing /",
  "priority": "HIGH",
  "priority_display": "High",
  "category": "BUG",
  "category_display": "Bug",
  "status": "IN_PROGRESS",
  "status_display": "In Progress",
  "created_by": 5,
  "created_by_name": "John Client",
  "assigned_to": [2, 3],
  "assigned_to_names": ["Alice Developer", "Bob Support"],
  "assigned_team": "Backend Team",
  "response_due_at": "2025-12-23T10:30:00Z",
  "resolution_due_at": "2025-12-24T18:00:00Z",
  "response_breached": false,
  "resolution_breached": false,
  "response_sla_minutes": 30,
  "estimated_resolution_time": "2025-12-24T15:00:00Z",
  "created_at": "2025-12-23T10:00:00Z",
  "updated_at": "2025-12-23T11:00:00Z",
  "opened_at": "2025-12-23T10:05:00Z",
  "started_at": "2025-12-23T10:30:00Z",
  "resolved_at": null,
  "closed_at": null,
  "attachments": [
    {
      "id": 1,
      "ticket": 1,
      "file_data": "base64_encoded_file_data",
      "uploaded_by": 5,
      "uploaded_by_name": "John Client",
      "uploaded_at": "2025-12-23T10:01:00Z"
    }
  ],
  "history": [
    {
      "id": 1,
      "ticket": 1,
      "changed_by": 1,
      "changed_by_name": "Admin User",
      "status_from": "NEW",
      "status_from_display": "New",
      "status_to": "OPENED",
      "status_to_display": "Opened",
      "comment": "Ticket opened by admin",
      "timestamp": "2025-12-23T10:05:00Z"
    },
    {
      "id": 2,
      "ticket": 1,
      "changed_by": 2,
      "changed_by_name": "Alice Developer",
      "status_from": "OPENED",
      "status_from_display": "Opened",
      "status_to": "IN_PROGRESS",
      "status_to_display": "In Progress",
      "comment": "Work started on ticket",
      "timestamp": "2025-12-23T10:30:00Z"
    }
  ]
}
```

---

### 3. Assign Developers to Ticket
**Endpoint:** `POST /api/tickets/{id}/assign/`  
**Permission:** Admin only  
**Description:** Assign one or more developers to a ticket

**Request Body:**
```json
{
  "assigned_to": [2, 3, 8],
  "resolution_due_at": "2025-12-24T18:00:00Z",
  "estimated_resolution_time": "2025-12-24T15:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "assigned_to": [2, 3, 8],
  "assigned_to_names": ["Alice Developer", "Bob Support", "Charlie Dev"],
  "resolution_due_at": "2025-12-24T18:00:00Z",
  "estimated_resolution_time": "2025-12-24T15:00:00Z",
  ...
}
```

---

### 4. Set SLA for Ticket
**Endpoint:** `POST /api/tickets/{id}/set_sla/`  
**Permission:** Admin only  
**Description:** Set or update SLA times for ticket

**Request Body:**
```json
{
  "response_due_at": "2025-12-23T10:30:00Z",
  "resolution_due_at": "2025-12-25T10:00:00Z"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "response_due_at": "2025-12-23T10:30:00Z",
  "resolution_due_at": "2025-12-25T10:00:00Z",
  ...
}
```

---

### 5. Open Ticket (Acknowledge)
**Endpoint:** `POST /api/tickets/{id}/open_ticket/`  
**Permission:** Admin only  
**Description:** Change ticket status from NEW to OPENED

**Request Body:** (Empty)

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "OPENED",
  "opened_at": "2025-12-23T10:05:00Z",
  ...
}
```

---

### 6. List All Users
**Endpoint:** `GET /api/users/`  
**Permission:** Admin only  
**Description:** Get list of all users in the system

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "username": "admin_user",
    "email": "admin@company.com",
    "first_name": "Admin",
    "last_name": "User",
    "full_name": "Admin User",
    "role": "ADMIN",
    "phone_number": "+1234567890",
    "whatsapp_number": "+1234567890",
    "department": "IT Management",
    "is_active": true,
    "date_joined": "2025-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "username": "alice_dev",
    "email": "alice@company.com",
    "first_name": "Alice",
    "last_name": "Developer",
    "full_name": "Alice Developer",
    "role": "SUPPORT",
    "phone_number": "+1234567891",
    "whatsapp_number": "+1234567891",
    "department": "Technical Support",
    "is_active": true,
    "date_joined": "2025-01-02T00:00:00Z"
  }
]
```

---

### 7. Get Developers List
**Endpoint:** `GET /api/users/by_role/?role=SUPPORT`  
**Permission:** Admin only  
**Description:** Get list of all developers (SUPPORT role)

**Response (200 OK):**
```json
[
  {
    "id": 2,
    "username": "alice_dev",
    "email": "alice@company.com",
    "first_name": "Alice",
    "last_name": "Developer",
    "full_name": "Alice Developer",
    "role": "SUPPORT",
    "phone_number": "+1234567891",
    "whatsapp_number": "+1234567891",
    "department": "Technical Support",
    "is_active": true,
    "date_joined": "2025-01-02T00:00:00Z"
  }
]
```

**Note:** Can also filter by `role=CLIENT` or `role=ADMIN`

---

### 8. Create New User
**Endpoint:** `POST /api/users/`  
**Permission:** Admin only  
**Description:** Create a new user account with profile

**Request Body:**
```json
{
  "username": "new_developer",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "email": "newdev@company.com",
  "first_name": "New",
  "last_name": "Developer",
  "role": "SUPPORT",
  "phone_number": "+1234567892",
  "whatsapp_number": "+1234567892",
  "department": "Technical Support"
}
```

**Response (201 Created):**
```json
{
  "id": 10,
  "username": "new_developer",
  "email": "newdev@company.com",
  "first_name": "New",
  "last_name": "Developer",
  "full_name": "New Developer",
  "role": "SUPPORT",
  "phone_number": "+1234567892",
  "whatsapp_number": "+1234567892",
  "department": "Technical Support",
  "is_active": true,
  "date_joined": "2025-12-23T12:00:00Z"
}
```

---

### 9. Update User
**Endpoint:** `PATCH /api/users/{id}/`  
**Permission:** Admin only  
**Description:** Update user information

**Request Body:**
```json
{
  "email": "updated@company.com",
  "role": "ADMIN",
  "department": "IT Management",
  "password": "NewPassword123!"
}
```

**Response (200 OK):**
```json
{
  "id": 10,
  "username": "new_developer",
  "email": "updated@company.com",
  "first_name": "New",
  "last_name": "Developer",
  "full_name": "New Developer",
  "role": "ADMIN",
  "phone_number": "+1234567892",
  "whatsapp_number": "+1234567892",
  "department": "IT Management",
  "is_active": true,
  "date_joined": "2025-12-23T12:00:00Z"
}
```

---

### 10. Deactivate User
**Endpoint:** `POST /api/users/{id}/deactivate/`  
**Permission:** Admin only  
**Description:** Deactivate a user account (cannot deactivate yourself)

**Request Body:** (Empty)

**Response (200 OK):**
```json
{
  "message": "User new_developer deactivated successfully"
}
```

---

### 11. Activate User
**Endpoint:** `POST /api/users/{id}/activate/`  
**Permission:** Admin only  
**Description:** Activate a deactivated user account

**Request Body:** (Empty)

**Response (200 OK):**
```json
{
  "message": "User new_developer activated successfully"
}
```

---

## Developer APIs

### 1. List Assigned Tickets
**Endpoint:** `GET /api/tickets/`  
**Permission:** Developer  
**Description:** Get list of tickets assigned to the developer

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Homepage not loading",
    "status": "IN_PROGRESS",
    "priority": "HIGH",
    "assigned_to": [2, 3],
    "assigned_to_names": ["Alice Developer", "Bob Support"],
    ...
  }
]
```

---

### 2. Get Assigned Ticket Details
**Endpoint:** `GET /api/tickets/{id}/`  
**Permission:** Developer (only assigned tickets)  
**Description:** Get full details of an assigned ticket including attachments

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Homepage not loading",
  "description": "The homepage returns 500 error",
  "attachments": [
    {
      "id": 1,
      "file_data": "base64_encoded_file",
      "uploaded_by_name": "John Client",
      "uploaded_at": "2025-12-23T10:01:00Z"
    }
  ],
  ...
}
```

---

### 3. Start Work on Ticket
**Endpoint:** `POST /api/tickets/{id}/start_work/`  
**Permission:** Developer (assigned), Admin  
**Description:** Change ticket status to IN_PROGRESS

**Request Body:** (Empty)

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "IN_PROGRESS",
  "started_at": "2025-12-23T10:30:00Z",
  ...
}
```

---

### 4. Finish Work on Ticket
**Endpoint:** `POST /api/tickets/{id}/finish_work/`  
**Permission:** Developer (assigned), Admin  
**Description:** Mark work as complete, change status to RESOLVED

**Request Body:**
```json
{
  "comment": "Fixed the database connection issue causing 500 error"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "RESOLVED",
  "resolved_at": "2025-12-23T14:00:00Z",
  ...
}
```

---

## Client APIs

### 1. List My Tickets
**Endpoint:** `GET /api/tickets/`  
**Permission:** Client  
**Description:** Get list of all tickets created by the client

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "Homepage not loading",
    "status": "IN_PROGRESS",
    "priority": "HIGH",
    "created_by": 5,
    "created_by_name": "John Client",
    "assigned_to_names": ["Alice Developer", "Bob Support"],
    ...
  }
]
```

---

### 2. Get My Ticket Details
**Endpoint:** `GET /api/tickets/{id}/`  
**Permission:** Client (own tickets only)  
**Description:** Get full details of a ticket created by the client

**Response (200 OK):**
```json
{
  "id": 1,
  "title": "Homepage not loading",
  "description": "The homepage returns 500 error",
  "status": "RESOLVED",
  "attachments": [...],
  "history": [...],
  ...
}
```

---

### 3. Create New Ticket
**Endpoint:** `POST /api/tickets/`  
**Permission:** Client  
**Description:** Create a new support ticket

**Request Body:**
```json
{
  "project_name": "Website Redesign",
  "title": "Contact form not sending emails",
  "description": "When submitting the contact form, users don't receive confirmation emails",
  "priority": "MEDIUM",
  "category": "BUG"
}
```

**Response (201 Created):**
```json
{
  "id": 15,
  "project_name": "Website Redesign",
  "title": "Contact form not sending emails",
  "description": "When submitting the contact form, users don't receive confirmation emails",
  "priority": "MEDIUM",
  "priority_display": "Medium",
  "category": "BUG",
  "category_display": "Bug",
  "status": "NEW",
  "status_display": "New",
  "created_by": 5,
  "created_by_name": "John Client",
  "assigned_to": [],
  "assigned_to_names": [],
  "response_due_at": "2025-12-23T12:00:00Z",
  "created_at": "2025-12-23T10:00:00Z",
  ...
}
```

**Valid Values:**
- `priority`: HIGH, MEDIUM, LOW
- `category`: BUG, PROBLEM, SERVICE_DOWN, NEW_FEATURE

---

### 4. Add Attachment to Ticket
**Endpoint:** `POST /api/tickets/{id}/add_attachment/`  
**Permission:** Client (own tickets), Developer (assigned tickets), Admin  
**Description:** Upload a file attachment to a ticket

**Request Body (multipart/form-data):**
```json
{
  "file_data": "<base64_encoded_file_content>"
}
```

**Response (200 OK):**
```json
{
  "message": "Attachment added successfully",
  "attachment": {
    "id": 5,
    "ticket": 15,
    "uploaded_by": 5,
    "uploaded_by_name": "John Client",
    "uploaded_at": "2025-12-23T10:05:00Z"
  }
}
```

---

### 5. Approve Resolved Ticket
**Endpoint:** `POST /api/tickets/{id}/approve/`  
**Permission:** Client (own tickets only)  
**Description:** Approve the resolution and close the ticket

**Request Body:**
```json
{
  "comment": "Works perfectly now, thank you!"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "CLOSED",
  "closed_at": "2025-12-23T15:00:00Z",
  ...
}
```

---

### 6. Reject Resolved Ticket
**Endpoint:** `POST /api/tickets/{id}/reject/`  
**Permission:** Client (own tickets only)  
**Description:** Reject the resolution, reopen ticket for more work

**Request Body:**
```json
{
  "comment": "The issue still persists when using mobile browser"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "IN_PROGRESS",
  ...
}
```

---

## Common APIs (All Roles)

### 1. View Own Profile
**Endpoint:** `GET /api/profiles/`  
**Permission:** Authenticated user  
**Description:** Get own profile information (admins see all profiles)

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "username": "john_client",
    "email": "john@client.com",
    "first_name": "John",
    "last_name": "Client",
    "role": "CLIENT",
    "phone_number": "+1234567890",
    "whatsapp_number": "+1234567890",
    "department": "Marketing",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-12-23T10:00:00Z"
  }
]
```

---

### 2. Update Own Profile
**Endpoint:** `PATCH /api/profile/update/`  
**Permission:** Authenticated user  
**Description:** Update own first name, last name, and password

**Request Body:**
```json
{
  "first_name": "Jonathan",
  "last_name": "ClientUpdated",
  "password": "NewSecurePass123!",
  "password_confirm": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "first_name": "Jonathan",
  "last_name": "ClientUpdated"
}
```

**Note:** Password is optional. If updating password, both `password` and `password_confirm` are required and must match.

---

### 3. Add Comment to Ticket
**Endpoint:** `POST /api/tickets/{id}/add_comment/`  
**Permission:** Authenticated user (with access to ticket)  
**Description:** Add a comment/note to ticket history

**Request Body:**
```json
{
  "comment": "Client has provided additional information via phone call"
}
```

**Response (200 OK):**
```json
{
  "message": "Comment added successfully"
}
```

---

## Ticket Status Workflow

```
NEW → OPENED → IN_PROGRESS → RESOLVED → WAITING_APPROVAL → CLOSED
                      ↑                                      ↓
                      └──────────────────────────────────────┘
                                  (if rejected)
```

**Status Descriptions:**
- **NEW**: Ticket just created by client
- **OPENED**: Admin acknowledged ticket
- **IN_PROGRESS**: Developer started working
- **RESOLVED**: Developer finished work
- **WAITING_APPROVAL**: Waiting for client approval
- **CLOSED**: Client approved and ticket closed

---

## SLA (Service Level Agreement)

**Response SLA** (Auto-calculated based on priority):
- **HIGH**: 30 minutes
- **MEDIUM**: 2 hours (120 minutes)
- **LOW**: 24 hours (1440 minutes)

**Resolution SLA**: Set manually by admin via `/api/tickets/{id}/set_sla/`

---

## Error Responses

**400 Bad Request:**
```json
{
  "error": "assigned_to is required (array of user IDs)"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden:**
```json
{
  "error": "You are not assigned to this ticket"
}
```

**404 Not Found:**
```json
{
  "error": "Support user not found"
}
```

---

## Notification System

The system sends notifications via:
1. **Email** - Using SMTP (Gmail)
2. **WhatsApp** - Using WhatsApp Cloud API (Meta Business)
3. **WebSocket** - Real-time in-app notifications

**Notification Triggers:**
- New ticket created → Admin receives email + WhatsApp + WebSocket
- Ticket opened → Client receives email + WhatsApp + WebSocket
- Ticket assigned → Developer(s) receive email + WhatsApp + WebSocket
- Work started → Client receives email + WhatsApp + WebSocket
- Work finished → Client and Admin receive email + WhatsApp + WebSocket
- Ticket approved/rejected → Developer and Admin receive WhatsApp + WebSocket

**Notification Storage:**
- All notifications are stored in the database (`NotificationLog` table)
- Notifications persist indefinitely and can be retrieved via API
- Read/unread tracking with timestamps

---

## Notification APIs

### 1. Get All Notifications
**Endpoint:** `GET /api/notifications/`  
**Permission:** Authenticated user (sees own), Admin (sees all)  
**Description:** Get paginated list of notifications with filtering

**Returns minimal data for performance and security** - only ID, subject, type, and read status.
For full notification details (including message), use the detail endpoint.

**Query Parameters:**
- `is_read` - Filter by read status (`true` or `false`)
- `notification_type` - Filter by type (`EMAIL`, `WHATSAPP`, `SYSTEM`)
- `ticket` - Filter by ticket ID
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 20)

**Example Request:**
```
GET /api/notifications/?is_read=false&notification_type=SYSTEM&pagee=1
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 45,
  "next": "http://localhost:8000/api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 123,
      "ticket": 5,
      "notification_type": "SYSTEM",
      "notification_type_display": "System Alert",
      "subject": "New Ticket Created",
      "created_at": "2025-12-24T10:30:00Z",
      "is_read": false,
      "read_at": null
    },
    {
      "id": 124,
      "ticket": 7,
      "notification_type": "EMAIL",
      "notification_type_display": "Email",
      "subject": "Ticket Assigned",
      "created_at": "2025-12-24T11:15:00Z",
      "is_read": true,
      "read_at": "2025-12-24T11:20:00Z"
    }
  ]
}
```

**Note:** List endpoint returns minimal data (no message, recipient name, ticket title etc.) for better performance and security.

---

### 2. Get Unread Notifications
**Endpoint:** `GET /api/notifications/unread/`  
**Permission:** Authenticated user  
**Description:** Get all unread notifications for current user (paginated)

**Returns minimal data** - same format as list endpoint.

**Example Request:**
```
GET /api/notifications/unread/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 123,
      "ticket": 5,
      "notification_type": "SYSTEM",
      "notification_type_display": "System Alert",
      "subject": "New Ticket Created",
      "created_at": "2025-12-24T10:30:00Z",
      "is_read": false,
      "read_at": null
    }
  ]
}
```

---

### 3. Get Unread Count
**Endpoint:** `GET /api/notifications/unread_count/`  
**Permission:** Authenticated user  
**Description:** Get count of unread notifications with breakdown by type

**Example Request:**
```
GET /api/notifications/unread_count/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
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

---

### 4. Mark Notification as Read
**Endpoint:** `POST /api/notifications/{id}/mark_as_read/`  
**Permission:** Authenticated user (own notifications), Admin (all)  
**Description:** Mark a single notification as read

**Example Request:**
```
POST /api/notifications/123/mark_as_read/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Notification marked as read",
  "notification": {
    "id": 123,
    "ticket": 5,
    "notification_type": "SYSTEM",
    "notification_type_display": "System Alert",
    "subject": "New Ticket Created",
    "created_at": "2025-12-24T10:30:00Z",
    "is_read": true,
    "read_at": "2025-12-24T14:25:30Z"
  }
}
```

---

### 5. Mark All Notifications as Read
**Endpoint:** `POST /api/notifications/mark_all_as_read/`  
**Permission:** Authenticated user  
**Description:** Mark all unread notifications as read for current user

**Query Parameters (Optional):**
- `notification_type` - Only mark specific type as read (`EMAIL`, `WHATSAPP`, `SYSTEM`)
- `ticket` - Only mark notifications for specific ticket as read

**Example Request 1 - Mark all as read:**
```
POST /api/notifications/mark_all_as_read/
Authorization: Bearer <access_token>
```

**Example Request 2 - Mark only SYSTEM notifications as read:**
```
POST /api/notifications/mark_all_as_read/?notification_type=SYSTEM
Authorization: Bearer <access_token>
```

**Example Request 3 - Mark only ticket #5 notifications as read:**
```
POST /api/notifications/mark_all_as_read/?ticket=5
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "5 notification(s) marked as read",
  "count": 5
}
```

---

## WebSocket Notifications

### Connection
**WebSocket URL:** `ws://localhost:8000/ws/notifications/?token=<jwt_access_token>`

**Protocol:** WebSocket (RFC 6455)

### Message Types

#### 1. Connection Established
Sent immediately after successful connection:
```json
{
  "type": "connection_established",
  "message": "Connected successfully as john_admin",
  "user_id": 1
}
```

#### 2. Real-Time Notification
Sent when a notification event occurs:
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

#### 3. Ping/Pong (Heartbeat)
Client sends ping to keep connection alive:
```json
{
  "type": "ping",
  "timestamp": 1735038600000
}
```

Server responds with pong:
```json
{
  "type": "pong",
  "timestamp": 1735038600000
}
```

### WebSocket Notification Types

| Notification Type | Trigger | Recipients |
|------------------|---------|------------|
| `ticket_created` | New ticket created | All Admins |
| `ticket_opened` | Admin opens ticket | Ticket Creator (Client) |
| `ticket_assigned` | Ticket assigned to developers | Assigned Developers |
| `work_started` | Developer starts work | Ticket Creator (Client) |
| `work_finished` | Developer finishes work | Ticket Creator (Client) |
| `ticket_approved` | Client approves work | Admins + Assigned Developers |
| `ticket_rejected` | Client rejects work | Admins + Assigned Developers |

### JavaScript Example
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/notifications/?token=' + accessToken);

// Handle connection
ws.onopen = () => {
  console.log('Connected to notification service');
};

// Receive notifications
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'connection_established') {
    console.log('Connected as user:', data.user_id);
  } else if (data.notification_type) {
    // Show notification to user
    showNotification(data.message, data.ticket);
  }
};

// Send heartbeat every 30 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'ping',
      timestamp: Date.now()
    }));
  }
}, 30000);
```

---

## Summary of All Endpoints

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/api/auth/login/` | Public | User login |
| POST | `/api/auth/refresh/` | Public | Refresh access token |
| GET | `/api/tickets/` | All | List tickets (filtered by role) |
| POST | `/api/tickets/` | Client | Create new ticket |
| GET | `/api/tickets/{id}/` | All | Get ticket details |
| POST | `/api/tickets/{id}/assign/` | Admin | Assign developers |
| POST | `/api/tickets/{id}/set_sla/` | Admin | Set SLA times |
| POST | `/api/tickets/{id}/open_ticket/` | Admin | Open ticket |
| POST | `/api/tickets/{id}/start_work/` | Developer, Admin | Start work |
| POST | `/api/tickets/{id}/finish_work/` | Developer, Admin | Finish work |
| POST | `/api/tickets/{id}/approve/` | Client | Approve resolution |
| POST | `/api/tickets/{id}/reject/` | Client | Reject resolution |
| POST | `/api/tickets/{id}/add_attachment/` | All | Add file attachment |
| GET | `/api/tickets/{id}/get_attachments/` | All | Get ticket attachments (base64) |
| DELETE | `/api/tickets/{id}/delete_attachment/{attachment_id}/` | All | Delete attachment (with restrictions) |
| POST | `/api/tickets/{id}/add_comment/` | All | Add comment |
| GET | `/api/users/` | Admin | List all users |
| POST | `/api/users/` | Admin | Create new user |
| GET | `/api/users/{id}/` | Admin | Get user details |
| PATCH | `/api/users/{id}/` | Admin | Update user |
| DELETE | `/api/users/{id}/` | Admin | Delete user |
| POST | `/api/users/{id}/activate/` | Admin | Activate user |
| POST | `/api/users/{id}/deactivate/` | Admin | Deactivate user |
| GET | `/api/users/by_role/?role=SUPPORT` | Admin | List users by role |
| GET | `/api/profiles/` | All | View own profile |
| PATCH | `/api/profile/update/` | All | Update own profile |
| GET | `/api/notifications/` | All | List all notifications (filtered) |
| GET | `/api/notifications/unread/` | All | Get unread notifications |
| GET | `/api/notifications/unread_count/` | All | Get unread count |
| POST | `/api/notifications/{id}/mark_as_read/` | All | Mark notification as read |
| POST | `/api/notifications/mark_all_as_read/` | All | Mark all as read |
| WS | `ws://host/ws/notifications/?token=<jwt>` | All | WebSocket real-time notifications |

---

**Total Endpoints:** 34 (29 REST + 5 Notification APIs)  
**Last Updated:** December 25, 2025

---

## New Endpoints

### 1. Get Ticket Attachments
**Endpoint:** `GET /api/tickets/{id}/get_attachments/`  
**Permission:** All users with access to the ticket  
**Description:** Get all attachments for a ticket in base64 format

**Access Control:**
- Admins: Can access attachments for all tickets
- Developers: Can access attachments for tickets assigned to them
- Clients: Can access attachments for their own tickets

**Response (200 OK):**
```json
{
  "ticket_id": 16,
  "ticket_title": "Contact form not sending emails",
  "attachments_count": 2,
  "attachments": [
    {
      "id": 1,
      "ticket": 16,
      "file_data": "iVBORw0KGgoAAAANSUhEUgAA...",
      "uploaded_by": 6,
      "uploaded_by_name": "Mohamed hassan",
      "uploaded_at": "2025-12-25 10:30:00"
    },
    {
      "id": 2,
      "ticket": 16,
      "file_data": "JVBERi0xLjQKJeLjz9MKMyAw...",
      "uploaded_by": 2,
      "uploaded_by_name": "admin_user2",
      "uploaded_at": "2025-12-25 11:15:00"
    }
  ]
}
```

**Note:** `file_data` is base64 encoded. Decode it on frontend to display/download files.

---

### 2. Delete Attachment
**Endpoint:** `DELETE /api/tickets/{id}/delete_attachment/{attachment_id}/`  
**Permission:** Role-based with restrictions  
**Description:** Delete a ticket attachment

**Deletion Rules:**
- **Client**: Can ONLY delete their own attachments
- **Developer**: Can ONLY delete their own attachments
- **Admin**: Can delete attachments uploaded by admins or developers (NOT by clients)

**Example Request:**
```
DELETE /api/tickets/16/delete_attachment/5/
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Attachment deleted successfully",
  "attachment_id": 5
}
```

**Response (403 Forbidden - Admin trying to delete client attachment):**
```json
{
  "error": "Admins cannot delete attachments uploaded by clients"
}
```

**Response (403 Forbidden - User trying to delete others' attachment):**
```json
{
  "error": "You can only delete attachments you uploaded"
}
```

---

## Updated Response Formats

### Create Ticket (Optimized Response)
**Endpoint:** `POST /api/tickets/`

**New Response (201 Created):**
```json
{
  "id": 17,
  "project_name": "new Ticking managemt5135",
  "priority_display": "Medium",
  "category_display": "Bug",
  "status_display": "New",
  "created_by": 6,
  "created_by_name": "Mohamed hassan",
  "response_due_at": "2025-12-25 16:33:23",
  "response_sla_minutes": 120
}
```

---

### List Tickets (Minimal Response)
**Endpoint:** `GET /api/tickets/`

**New Response:** No attachments or history (only essential fields for performance)

---

### Ticket Action Responses (All Optimized)

**Open Ticket:**
```json
{
  "message": "Ticket opened successfully",
  "id": 16,
  "title": "Contact form not sending emails",
  "status_display": "Opened"
}
```

**Assign Developers:**
```json
{
  "message": "Developers assigned successfully",
  "id": 16,
  "title": "Contact form not sending emails",
  "assigned_to_names": "developer1, developer2"
}
```

**Start Work:**
```json
{
  "message": "Status updated successfully",
  "id": 16,
  "project_name": "Ticking managemt5135",
  "status_display": "In Progress",
  "estimated_resolution_time": "2025-12-26T10:00:00Z"
}
```

**Finish Work:**
```json
{
  "message": "Status updated successfully",
  "id": 16,
  "project_name": "Ticking managemt5135",
  "status_display": "Resolved"
}
```

**Approve/Reject:**
```json
{
  "message": "Status updated to Closed",
  "id": 16,
  "project_name": "Ticking managemt5135",
  "status_display": "Closed"
}
```

**Upload Attachment:**
```json
{
  "message": "Attachment uploaded to ticket #16 successfully",
  "ticket_id": 16,
  "attachment_id": 5
}
```

---

## Permission Changes

### Ticket Creation
- ✅ **Clients**: Can create tickets
- ✅ **Admins**: Can create tickets
- ❌ **Developers**: CANNOT create tickets

### Approve/Reject Actions
- ✅ **Ticket creator** (Client or Admin who created it) can approve/reject
- ❌ Other admins cannot approve/reject tickets they didn't create

---

**Total Endpoints:** 34 (29 REST + 5 Notification APIs)  
**Last Updated:** December 25, 2025
