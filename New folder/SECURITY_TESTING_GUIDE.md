# Security Testing Guide - Incident Management System

## 🔒 Security Fixes Applied

### ✅ Fix #1: Status Field Protection
- **Status:** IMPLEMENTED
- **Change:** Added `'status'` and `'assigned_to'` to `read_only_fields` in both `TicketSerializer` and `TicketAdminSerializer`
- **Result:** Users cannot change status via PUT/PATCH requests

### ✅ Fix #2: Update/Delete Permission Control
- **Status:** IMPLEMENTED
- **Change:** Added `get_permissions()` method to restrict update/partial_update/destroy to admins only
- **Result:** Only ADMIN role can use standard REST update/delete endpoints

### ✅ Fix #3: Block Status Changes in Updates
- **Status:** IMPLEMENTED
- **Change:** Overridden `update()` and `partial_update()` methods to explicitly reject status/assignment changes
- **Result:** Even if data is sent, it's rejected with clear error message

### ✅ Fix #4: Correct History Tracking
- **Status:** IMPLEMENTED
- **Change:** Renamed signal from `create_ticket_history` to `send_ticket_notifications` and removed automatic history creation
- **Result:** Only views create history entries with the correct `request.user`

---

## 🧪 Security Test Cases

### Test Suite 1: Status Protection Tests

#### Test 1.1: Client Cannot Change Status via PATCH
```bash
# Login as CLIENT
POST http://localhost:8000/api/auth/login/
{
    "username": "client_user",
    "password": "password"
}

# Try to change status
PATCH http://localhost:8000/api/tickets/1/
Authorization: Bearer <client_token>
{
    "status": "CLOSED"
}

Expected Result:
❌ Status 400 Bad Request
Response: {
    "error": "Status cannot be changed directly. Use action endpoints..."
}
```

#### Test 1.2: Client Cannot Change Status via PUT
```bash
# Get current ticket data first
GET http://localhost:8000/api/tickets/1/

# Try full update with changed status
PUT http://localhost:8000/api/tickets/1/
Authorization: Bearer <client_token>
{
    "title": "Ticket Title",
    "description": "Description",
    "priority": "HIGH",
    "category": "BUG",
    "project_name": "Project",
    "status": "RESOLVED"  # Try to change status
}

Expected Result:
❌ Status 400 Bad Request
Response: {
    "error": "Status cannot be changed directly. Use action endpoints..."
}
```

#### Test 1.3: Admin Also Cannot Change Status via PATCH
```bash
# Login as ADMIN
POST http://localhost:8000/api/auth/login/
{
    "username": "admin_user",
    "password": "password"
}

# Try to change status
PATCH http://localhost:8000/api/tickets/1/
Authorization: Bearer <admin_token>
{
    "status": "CLOSED"
}

Expected Result:
❌ Status 400 Bad Request
Response: {
    "error": "Status cannot be changed directly. Use action endpoints..."
}
```

---

### Test Suite 2: Assignment Protection Tests

#### Test 2.1: Client Cannot Assign Developers
```bash
# As CLIENT
PATCH http://localhost:8000/api/tickets/1/
Authorization: Bearer <client_token>
{
    "assigned_to": 4
}

Expected Result:
❌ Status 400 Bad Request
Response: {
    "error": "Assignment cannot be changed directly. Use assign action endpoint."
}
```

#### Test 2.2: Only Assign Action Works
```bash
# As ADMIN
POST http://localhost:8000/api/tickets/1/assign/
Authorization: Bearer <admin_token>
{
    "assigned_to": 4,
    "resolution_due_at": "2025-12-25T10:00:00Z",
    "estimated_resolution_time": "2025-12-25T09:00:00Z"
}

Expected Result:
✅ Status 200 OK
- Ticket assigned successfully
- History created with admin_user as changed_by
- Email sent to developer
```

---

### Test Suite 3: Permission-Based Access Tests

#### Test 3.1: Client Cannot Update Tickets via Standard Endpoint
```bash
# As CLIENT
PATCH http://localhost:8000/api/tickets/1/
Authorization: Bearer <client_token>
{
    "description": "Updated description"
}

Expected Result:
❌ Status 403 Forbidden
Response: {
    "detail": "You do not have permission to perform this action."
}
```

#### Test 3.2: Client Cannot Delete Tickets
```bash
# As CLIENT
DELETE http://localhost:8000/api/tickets/1/
Authorization: Bearer <client_token>

Expected Result:
❌ Status 403 Forbidden
Response: {
    "detail": "You do not have permission to perform this action."
}
```

#### Test 3.3: Admin Can Update SLA Fields
```bash
# As ADMIN
PATCH http://localhost:8000/api/tickets/1/
Authorization: Bearer <admin_token>
{
    "response_due_at": "2025-12-23T15:00:00Z",
    "resolution_due_at": "2025-12-24T10:00:00Z",
    "estimated_resolution_time": "2025-12-24T08:00:00Z"
}

Expected Result:
✅ Status 200 OK
- SLA fields updated successfully
- Status and assigned_to remain unchanged
```

---

### Test Suite 4: Workflow Enforcement Tests

#### Test 4.1: Only Admin Can Open Tickets
```bash
# As CLIENT - Try to open
POST http://localhost:8000/api/tickets/1/open_ticket/
Authorization: Bearer <client_token>

Expected Result:
❌ Status 403 Forbidden

# As ADMIN - Open ticket
POST http://localhost:8000/api/tickets/1/open_ticket/
Authorization: Bearer <admin_token>
{
    "admin_notes": "Reviewed and approved"
}

Expected Result:
✅ Status 200 OK
- Status changed to OPENED
- History shows admin_user as changed_by
```

#### Test 4.2: Only Assigned Developer Can Start Work
```bash
# As unassigned developer
POST http://localhost:8000/api/tickets/1/start_work/
Authorization: Bearer <wrong_developer_token>

Expected Result:
❌ Status 403 Forbidden
Response: {
    "error": "You are not assigned to this ticket"
}

# As assigned developer
POST http://localhost:8000/api/tickets/1/start_work/
Authorization: Bearer <assigned_developer_token>

Expected Result:
✅ Status 200 OK
- Status changed to IN_PROGRESS
- History shows developer as changed_by
```

#### Test 4.3: Only Ticket Creator Can Approve
```bash
# As different client
POST http://localhost:8000/api/tickets/1/approve/
Authorization: Bearer <different_client_token>

Expected Result:
❌ Status 403 Forbidden
Response: {
    "error": "Only ticket creator can approve"
}

# As ticket creator
POST http://localhost:8000/api/tickets/1/approve/
Authorization: Bearer <creator_token>

Expected Result:
✅ Status 200 OK
- Status changed to CLOSED
- History shows creator as changed_by
```

---

### Test Suite 5: History Accuracy Tests

#### Test 5.1: Verify History Shows Correct User
```bash
# After admin opens ticket
GET http://localhost:8000/api/tickets/1/
Authorization: Bearer <any_authorized_token>

# Check history array in response
Expected Result:
{
    "history": [
        {
            "changed_by": 2,  # Admin user ID
            "changed_by_name": "Admin User",
            "status_from": "NEW",
            "status_to": "OPENED",
            "comment": "Ticket opened by admin",
            "timestamp": "2025-12-23T..."
        }
    ]
}

# NOT showing client user who created the ticket
```

#### Test 5.2: Verify Assignment History
```bash
# After admin assigns developer
GET http://localhost:8000/api/tickets/1/

Expected Result:
{
    "history": [
        ...,
        {
            "changed_by": 2,  # Admin user ID
            "changed_by_name": "Admin User",
            "status_from": "OPENED",
            "status_to": "OPENED",
            "comment": "Ticket assigned to John Developer",
            "timestamp": "2025-12-23T..."
        }
    ]
}
```

---

### Test Suite 6: Read-Only Field Tests

#### Test 6.1: Verify Status is Truly Read-Only
```bash
# As ADMIN (who has update permission)
PATCH http://localhost:8000/api/tickets/1/
Authorization: Bearer <admin_token>
{
    "title": "Updated Title",
    "status": "CLOSED",  # Try to sneak in status change
    "description": "Updated description"
}

Expected Result:
❌ Status 400 Bad Request
Response: {
    "error": "Status cannot be changed directly..."
}

# Title and description should NOT be updated either
# Request fails completely
```

#### Test 6.2: Verify Assigned_To is Read-Only
```bash
# As ADMIN
PATCH http://localhost:8000/api/tickets/1/
Authorization: Bearer <admin_token>
{
    "assigned_to": 5,  # Try to change assignment
    "resolution_due_at": "2025-12-25T10:00:00Z"
}

Expected Result:
❌ Status 400 Bad Request
Response: {
    "error": "Assignment cannot be changed directly..."
}
```

---

## 🎯 Testing Checklist

### Pre-Deployment Testing

- [ ] **Test 1.1** - Client PATCH status blocked
- [ ] **Test 1.2** - Client PUT status blocked
- [ ] **Test 1.3** - Admin PATCH status blocked
- [ ] **Test 2.1** - Client assignment blocked
- [ ] **Test 2.2** - Assign action works correctly
- [ ] **Test 3.1** - Client update blocked
- [ ] **Test 3.2** - Client delete blocked
- [ ] **Test 3.3** - Admin SLA update works
- [ ] **Test 4.1** - Open ticket role check works
- [ ] **Test 4.2** - Start work permission check works
- [ ] **Test 4.3** - Approve permission check works
- [ ] **Test 5.1** - History shows correct user
- [ ] **Test 5.2** - Assignment history correct
- [ ] **Test 6.1** - Status truly read-only
- [ ] **Test 6.2** - Assigned_to truly read-only

### Additional Security Tests

- [ ] **CSRF Protection** - Verify CSRF tokens work
- [ ] **SQL Injection** - Try malicious input in fields
- [ ] **XSS Prevention** - Try script tags in description
- [ ] **Authentication** - Unauthenticated requests blocked
- [ ] **Token Expiration** - Expired tokens rejected
- [ ] **Rate Limiting** - Multiple rapid requests handled
- [ ] **File Upload** - Only safe file types accepted
- [ ] **Email Injection** - Malicious email addresses rejected

---

## 🚦 Testing Results Template

### Test Execution Date: ___________
### Tested By: ___________

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| 1.1 | Client PATCH status | ⬜ PASS / ⬜ FAIL | |
| 1.2 | Client PUT status | ⬜ PASS / ⬜ FAIL | |
| 1.3 | Admin PATCH status | ⬜ PASS / ⬜ FAIL | |
| 2.1 | Client assignment | ⬜ PASS / ⬜ FAIL | |
| 2.2 | Assign action | ⬜ PASS / ⬜ FAIL | |
| 3.1 | Client update block | ⬜ PASS / ⬜ FAIL | |
| 3.2 | Client delete block | ⬜ PASS / ⬜ FAIL | |
| 3.3 | Admin SLA update | ⬜ PASS / ⬜ FAIL | |
| 4.1 | Open ticket role | ⬜ PASS / ⬜ FAIL | |
| 4.2 | Start work permission | ⬜ PASS / ⬜ FAIL | |
| 4.3 | Approve permission | ⬜ PASS / ⬜ FAIL | |
| 5.1 | History user accuracy | ⬜ PASS / ⬜ FAIL | |
| 5.2 | Assignment history | ⬜ PASS / ⬜ FAIL | |
| 6.1 | Status read-only | ⬜ PASS / ⬜ FAIL | |
| 6.2 | Assigned_to read-only | ⬜ PASS / ⬜ FAIL | |

**Overall Result:** ⬜ APPROVED FOR PRODUCTION / ⬜ NEEDS FIXES

**Notes:**
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________

---

## 🔄 After Testing - Database Cleanup

If you have incorrect history entries from before the fix, clean them up:

```python
# Run in Django shell
python manage.py shell

from core.models import TicketHistory

# Option 1: Delete all history (start fresh)
TicketHistory.objects.all().delete()

# Option 2: Keep history but fix wrong user attributions
# This is more complex and depends on your specific data
```

---

## 📊 Expected Behavior After Fixes

### ✅ Correct Workflow:

1. **Client creates ticket** → Status: NEW
2. **Admin opens ticket** → Status: OPENED (history shows admin)
3. **Admin assigns developer** → Assigned_to set (history shows admin)
4. **Developer starts work** → Status: IN_PROGRESS (history shows developer)
5. **Developer finishes work** → Status: RESOLVED (history shows developer)
6. **Client approves** → Status: CLOSED (history shows client)

### ❌ Blocked Actions:

- Client trying to change status via PATCH/PUT
- Client trying to assign developers
- Client trying to update/delete tickets
- Unassigned developer trying to start work
- Wrong client trying to approve ticket
- Anyone trying to bypass workflow with direct status changes

---

## 🔍 Monitoring After Deployment

### What to Monitor:

1. **Failed Permission Checks**
   - Look for 403 Forbidden responses
   - Investigate unusual patterns

2. **Blocked Status Changes**
   - Look for 400 Bad Request with status error
   - Identify users trying to bypass workflow

3. **History Accuracy**
   - Spot check random tickets
   - Verify changed_by matches expected user

4. **Audit Logs**
   - Review who performs sensitive actions
   - Track admin operations

### Recommended Logging:

```python
# Add to settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'security.log',
        },
    },
    'loggers': {
        'core.views': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

---

## ✅ Sign-Off

Before deploying to production:

- [ ] All tests passed
- [ ] Security review completed
- [ ] Test database cleaned
- [ ] Production database backed up
- [ ] Monitoring configured
- [ ] Team notified of changes
- [ ] Documentation updated

**Security Officer Approval:** ___________  
**Date:** ___________  
**Deployment Authorization:** ⬜ APPROVED / ⬜ DENIED

---

**Document Version:** 1.0  
**Last Updated:** December 23, 2025  
**Next Review Date:** ___________
