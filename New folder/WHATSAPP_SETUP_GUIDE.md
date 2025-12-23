# WhatsApp Integration Setup Guide

## 🎯 Overview

Your Incident Management System now supports **WhatsApp notifications** for all ticket status changes:
- ✅ New ticket created
- ✅ Ticket opened by admin
- ✅ Developer assigned
- ✅ Work started
- ✅ Work finished
- ✅ Ticket closed
- ✅ Ticket rejected

---

## 📋 Prerequisites

### 1. **Twilio Account Setup**

1. **Create Twilio Account:**
   - Go to https://www.twilio.com/try-twilio
   - Sign up for a free account
   - Verify your email and phone number

2. **Get Credentials:**
   - Dashboard → Account Info
   - Copy **Account SID**
   - Copy **Auth Token**

3. **Get WhatsApp-Enabled Number:**

   **Option A: Twilio Sandbox (for Testing - FREE)**
   - Console → Messaging → Try it out → Send a WhatsApp message
   - Scan QR code or send "join <code>" to +1 415 523 8886
   - Use `whatsapp:+14155238886` as your FROM number

   **Option B: Production Number (for Live - Paid)**
   - Console → Phone Numbers → Buy a Number
   - Enable WhatsApp capability
   - Complete WhatsApp Business Profile
   - Submit for approval (can take 1-2 weeks)

---

## 🔧 Installation Steps

### Step 1: Install Twilio Package

```bash
# In your virtual environment
cd Management
pip install twilio
```

### Step 2: Update `requirements.txt`

```bash
# Add to requirements.txt
echo twilio>=8.10.0 >> requirements.txt
```

### Step 3: Configure Django Settings

Add to `Incident/settings.py`:

```python
# WhatsApp Configuration via Twilio
TWILIO_ACCOUNT_SID = 'your_account_sid_here'  # Get from Twilio Dashboard
TWILIO_AUTH_TOKEN = 'your_auth_token_here'    # Get from Twilio Dashboard
TWILIO_WHATSAPP_FROM = 'whatsapp:+14155238886'  # Twilio Sandbox number

# For production:
# TWILIO_WHATSAPP_FROM = 'whatsapp:+1234567890'  # Your purchased number
```

**Security Best Practice:** Use environment variables:

```python
# settings.py
from decouple import config

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default=None)
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default=None)
TWILIO_WHATSAPP_FROM = config('TWILIO_WHATSAPP_FROM', default='whatsapp:+14155238886')
```

Create `.env` file:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
```

### Step 4: Add WhatsApp Numbers to User Profiles

In Django Admin Panel:

1. **Go to:** Admin Panel → Users → Select User
2. **Edit User Profile section**
3. **Add WhatsApp number** in format: `+1234567890` (with country code)
4. **Save**

Example formats:
- US: `+12025551234`
- Egypt: `+201234567890`
- UK: `+447700123456`

---

## 📱 Twilio Sandbox Setup (for Testing)

### Connect Your Phone to Sandbox:

1. **Get your sandbox code:**
   - Twilio Console → Messaging → Try it out
   - You'll see a code like: `join create-beside`

2. **Send WhatsApp message to Twilio:**
   - Open WhatsApp on your phone
   - Send message to: **+1 415 523 8886**
   - Message content: `join create-beside` (use your actual code)

3. **Confirmation:**
   - You'll receive: "Joined create-beside"
   - Your number is now connected!

4. **Test it:**
   - Create a ticket in your system
   - You should receive WhatsApp notification

**Important:** Sandbox connection expires after 3 days of inactivity. Re-join by sending the code again.

---

## 🧪 Testing WhatsApp Notifications

### Test 1: New Ticket Creation

```bash
# As CLIENT via Postman
POST http://localhost:8000/api/tickets/
Authorization: Bearer <client_token>
{
    "title": "WhatsApp Test Ticket",
    "description": "Testing WhatsApp notification",
    "priority": "HIGH",
    "category": "BUG",
    "project_name": "Test Project"
}
```

**Expected:**
- Admin with WhatsApp number receives message
- Console shows: `📱 WhatsApp sent to admin_user: SMxxxxxxxxxx`

### Test 2: Open Ticket (Admin)

```bash
POST http://localhost:8000/api/tickets/1/open_ticket/
Authorization: Bearer <admin_token>
{
    "admin_notes": "Testing WhatsApp"
}
```

**Expected:**
- Client receives WhatsApp: "✅ Your Ticket Has Been Opened"

### Test 3: Assign Developer

```bash
POST http://localhost:8000/api/tickets/1/assign/
Authorization: Bearer <admin_token>
{
    "assigned_to": 4
}
```

**Expected:**
- Developer receives WhatsApp: "🔧 New Task Assigned"

---

## 🔍 Troubleshooting

### Issue 1: "Twilio not installed" Warning

```
⚠️ WARNING: Twilio not installed. Run 'pip install twilio'
```

**Solution:**
```bash
pip install twilio
python manage.py runserver  # Restart server
```

---

### Issue 2: "TWILIO_ACCOUNT_SID not configured"

```
⚠️ WARNING: TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not configured
```

**Solution:**
- Add credentials to `settings.py`
- Restart Django server

---

### Issue 3: "User has no WhatsApp number"

```
⚠️ User john_dev has no WhatsApp number configured
```

**Solution:**
- Go to Admin Panel → Users → john_dev
- Add WhatsApp number in format: `+1234567890`
- Save user profile

---

### Issue 4: "Unable to create record: Permission denied"

```
❌ WhatsApp send failed: Unable to create record: Permission denied
```

**Causes:**
1. **Recipient not connected to sandbox**
   - Solution: Recipient must send "join <code>" to Twilio

2. **Invalid phone number format**
   - Solution: Use format `+1234567890` (country code + number, no spaces)

3. **Auth token incorrect**
   - Solution: Verify credentials in Twilio Dashboard

---

### Issue 5: WhatsApp Not Sending (No Errors)

**Check:**
1. Is Twilio installed? `pip list | grep twilio`
2. Are credentials set? Check `settings.py`
3. Does user have WhatsApp number? Check admin panel
4. Is recipient connected to sandbox? Check Twilio console

---

## 📊 Monitoring WhatsApp Messages

### View in Twilio Console:

1. Go to: Console → Messaging → Logs
2. Filter by: WhatsApp
3. See all sent messages with status

### View in Django Admin:

1. Go to: Admin Panel → Notification logs
2. Filter by: Notification type = WhatsApp
3. See status (SENT or FAILED)

### Check via API:

```bash
GET http://localhost:8000/api/notifications/
Authorization: Bearer <token>

# Filter by WhatsApp
GET http://localhost:8000/api/notifications/?notification_type=WHATSAPP
```

---

## 💰 Cost Considerations

### Twilio Sandbox (Testing):
- **FREE** ✅
- Limited to sandbox-connected numbers
- Can't use in production
- Message format includes "Sent from your Twilio trial account"

### Twilio Production:
- **WhatsApp Message Cost:** ~$0.005 per message (varies by country)
- **Phone Number Cost:** ~$1/month
- **Free Trial Credits:** $15 credit for new accounts

**Monthly Cost Estimate:**
- 1000 messages/month: ~$5 + $1 (number) = **$6/month**
- 5000 messages/month: ~$25 + $1 = **$26/month**

---

## 🚀 Going to Production

### Step 1: Get Production WhatsApp Number

1. **Buy Twilio Number:**
   - Console → Phone Numbers → Buy a Number
   - Select number with SMS + WhatsApp capability

2. **Create WhatsApp Business Profile:**
   - Messaging → Senders → WhatsApp senders
   - Fill in business details
   - Upload profile picture
   - Add business description

3. **Submit for Approval:**
   - Review → Submit for approval
   - Wait 1-2 weeks for approval

### Step 2: Update Settings

```python
# settings.py
TWILIO_WHATSAPP_FROM = 'whatsapp:+1234567890'  # Your approved number
```

### Step 3: Update Templates (Optional)

Twilio requires pre-approved message templates for production. You can:
- Use Content API for templates
- Or keep simple text messages (usually approved)

### Step 4: Test Before Launch

- Send test messages to team members
- Verify all notification types work
- Check message delivery time
- Verify links work in messages

---

## 📝 Message Format

### Current Format:

**Admin - New Ticket:**
```
🎫 *New Ticket Created*

*Client:* John Doe
*Title:* Login page not working
*Project:* Web Portal
*Priority:* HIGH
*Category:* BUG

*Description:*
Users cannot login to the portal...

Please review and assign this ticket as soon as possible.

_Incident Management System_
```

**Client - Ticket Opened:**
```
✅ *Your Ticket Has Been Opened*

Hello John Doe,

Your ticket has been acknowledged and opened by our support team.

*Ticket:* Login page not working
*Project:* Web Portal
*Status:* Opened

We are reviewing your issue and will assign it to a developer shortly.

_Support Team_
```

### Customization:

Edit messages in `core/whatsapp_service.py`:

```python
def notify_client_ticket_opened_whatsapp(ticket):
    message = f"""✅ *Your Custom Message*

Hello {ticket.created_by.get_full_name()},

Your custom content here...
    """
    send_whatsapp_message(ticket, ticket.created_by, message)
```

---

## 🔐 Security Best Practices

1. **Never commit credentials:**
   ```bash
   # .gitignore
   .env
   ```

2. **Use environment variables:**
   ```python
   TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
   ```

3. **Rotate tokens periodically:**
   - Every 90 days, generate new auth token
   - Update in settings

4. **Validate phone numbers:**
   ```python
   # Add to UserProfile model
   def clean(self):
       if self.whatsapp_number and not self.whatsapp_number.startswith('+'):
           raise ValidationError('WhatsApp number must include country code')
   ```

5. **Rate limiting:**
   - Twilio has default rate limits
   - Monitor usage in console

---

## 📈 Analytics

### Track in Django Admin:

```python
# Get WhatsApp stats
from core.models import NotificationLog

total_sent = NotificationLog.objects.filter(
    notification_type='WHATSAPP',
    status='SENT'
).count()

failed = NotificationLog.objects.filter(
    notification_type='WHATSAPP',
    status='FAILED'
).count()

print(f"WhatsApp messages: {total_sent} sent, {failed} failed")
```

---

## 🆘 Support

### Twilio Support:
- Documentation: https://www.twilio.com/docs/whatsapp
- Support: https://support.twilio.com
- Community: https://www.twilio.com/community

### Django Settings:
- File: `Incident/settings.py`
- Service: `core/whatsapp_service.py`
- Signals: `core/signals.py`

---

## ✅ Setup Checklist

- [ ] Twilio account created
- [ ] Account SID and Auth Token obtained
- [ ] `pip install twilio` executed
- [ ] Credentials added to settings.py
- [ ] Sandbox number configured (testing)
- [ ] Phone connected to sandbox (send "join <code>")
- [ ] WhatsApp numbers added to user profiles
- [ ] Server restarted
- [ ] Test ticket created
- [ ] WhatsApp message received
- [ ] Notification logs checked
- [ ] All workflow stages tested

---

**Document Version:** 1.0  
**Last Updated:** December 23, 2025  
**Status:** Ready for Testing
