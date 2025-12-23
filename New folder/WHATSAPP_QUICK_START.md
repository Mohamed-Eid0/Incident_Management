# WhatsApp Integration - Quick Reference

## ✅ What's Been Added

**New File:** `core/whatsapp_service.py` - All WhatsApp notification functions

**Updated Files:**
- `core/signals.py` - Triggers WhatsApp on status changes
- `core/views.py` - Sends WhatsApp on ticket creation and rejection

---

## 🚀 Quick Setup (3 Steps)

### 1. Install Twilio
```bash
pip install twilio
```

### 2. Add to settings.py
```python
TWILIO_ACCOUNT_SID = 'ACxxxxxxxxxxxxxxxx'  # From Twilio Dashboard
TWILIO_AUTH_TOKEN = 'your_auth_token'      # From Twilio Dashboard
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'  # Sandbox number
```

### 3. Connect Your Phone to Sandbox
- Send WhatsApp to: **+1 415 523 8886**
- Message: `join <your-code>`

---

## 📱 WhatsApp Notifications Sent For:

| Event | Recipient | Message |
|-------|-----------|---------|
| Ticket Created | ADMIN | 🎫 New Ticket Created |
| Ticket Opened | CLIENT | ✅ Your Ticket Has Been Opened |
| Developer Assigned | DEVELOPER | 🔧 New Task Assigned |
| Work Started | CLIENT | 🚀 Work Started on Your Ticket |
| Work Finished | CLIENT + ADMIN | ✅ Your Ticket Has Been Resolved |
| Ticket Closed | ADMIN + DEVELOPER | ✅ Ticket Closed |
| Ticket Rejected | DEVELOPER | 🔄 Ticket Rejected - More Work Needed |

---

## 🧪 Test It

1. **Add WhatsApp number to user profile:**
   - Format: `+1234567890` (with country code)
   - Example: `+201234567890` for Egypt

2. **Create a ticket via API:**
   ```bash
   POST /api/tickets/
   {
       "title": "Test",
       "description": "Testing WhatsApp",
       "priority": "HIGH",
       "category": "BUG",
       "project_name": "Test"
   }
   ```

3. **Check console output:**
   ```
   📱 WhatsApp sent to admin_user: SMxxxxxxxxxx
   ```

---

## 🔍 Troubleshooting

**No WhatsApp sent?**
- ✅ Check Twilio is installed: `pip list | grep twilio`
- ✅ Check credentials in settings.py
- ✅ Check user has WhatsApp number in profile
- ✅ Check recipient connected to sandbox

**Twilio not installed warning?**
```bash
pip install twilio
python manage.py runserver  # Restart
```

**User has no WhatsApp number?**
- Admin Panel → Users → Edit User → Add WhatsApp number

---

## 📊 View Logs

**Django Admin:**
- Admin Panel → Notification logs → Filter by WHATSAPP

**Twilio Console:**
- Console → Messaging → Logs

**API:**
```bash
GET /api/notifications/?notification_type=WHATSAPP
```

---

## 💰 Costs

**Sandbox (Testing):** FREE ✅  
**Production:** ~$0.005 per message + $1/month for number

---

## 📖 Full Documentation

See [WHATSAPP_SETUP_GUIDE.md](WHATSAPP_SETUP_GUIDE.md) for complete setup instructions.
