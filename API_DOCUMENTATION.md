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

**Notification Triggers:**
- New ticket created → Admin receives email + WhatsApp
- Ticket opened → Client receives email + WhatsApp
- Ticket assigned → Developer(s) receive email + WhatsApp
- Work started → Client receives email + WhatsApp
- Work finished → Client and Admin receive email + WhatsApp
- Ticket approved/rejected → Developer and Admin receive email + WhatsApp

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
| GET | `/api/notifications/` | All | View notification logs |

---

**Total Endpoints:** 27  
**Last Updated:** December 23, 2025
