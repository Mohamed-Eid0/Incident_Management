# WhatsApp Cloud API Setup Guide

## 🎯 Overview

Your system now uses **WhatsApp Cloud API** (Meta's official API) instead of Twilio. This is **FREE for up to 1,000 conversations per month** and provides better integration.

---

## 📋 Prerequisites

- Facebook Business Account
- Meta Developer Account
- WhatsApp Business Account
- Phone number for WhatsApp Business (must not be already on WhatsApp)

---

## 🔧 Step-by-Step Setup

### Step 1: Create Meta Developer Account

1. **Go to:** https://developers.facebook.com
2. **Click:** "Get Started" or "My Apps"
3. **Login** with your Facebook account
4. **Complete registration** if new user

---

### Step 2: Create a Business App

1. **Click:** "Create App"
2. **Select:** "Business" type
3. **App Name:** "Incident Management System" (or your choice)
4. **App Contact Email:** Your email
5. **Business Account:** Select or create one
6. **Click:** "Create App"

---

### Step 3: Add WhatsApp Product

1. **Find WhatsApp** in products list
2. **Click:** "Set up" next to WhatsApp
3. **Select or Create:** Business Portfolio
4. **Click:** "Continue"

---

### Step 4: Get Test Phone Number & Access Token

1. **Go to:** WhatsApp → API Setup
2. **You'll see:**
   - **Temporary Access Token** (expires in 24 hours - for testing)
   - **Phone Number ID** (starts with numbers)
   - **Test Phone Number** (provided by Meta, format: +1...)

3. **Copy these values** - you'll need them!

**Example:**
```
Phone Number ID: 123456789012345
Temporary Access Token: EAAxxxxxxxxxxxxxxxxxxxx
Test Phone Number: +1 555 0100
```

---

### Step 5: Add Recipient Phone Number (Testing)

**Important:** Before you can send messages, you must add recipient numbers:

1. **In API Setup page,** scroll to "To"
2. **Click:** "Manage phone number list"
3. **Click:** "Add phone number"
4. **Enter:** Recipient's phone number (with country code, e.g., +201234567890)
5. **Click:** "Send Code"
6. **Enter:** Verification code received via SMS/WhatsApp
7. **Repeat** for all team members who should receive notifications

**Note:** This limitation only applies to test mode. In production, you can send to any number.

---

### Step 6: Configure Django Settings

Update `Incident/settings.py`:

```python
# WhatsApp Cloud API Configuration
WHATSAPP_ACCESS_TOKEN = 'EAAxxxxxxxxxxxxxxxxxxxx'  # Your Temporary Access Token
WHATSAPP_PHONE_NUMBER_ID = '123456789012345'      # Your Phone Number ID
WHATSAPP_API_VERSION = 'v21.0'                    # Current version (check Meta docs)
```

---

### Step 7: Add WhatsApp Numbers to User Profiles

**In Django Admin Panel:**

1. **Go to:** Admin Panel → Users → Select User
2. **User Profile section → WhatsApp Number**
3. **Add number** in format: `+1234567890` (no spaces, with country code)
   - ✅ Correct: `+201234567890`
   - ❌ Wrong: `01234567890`, `+20 123 456 7890`

**Important:** This number must be added to the "To" list in Meta Developer Console (Step 5)

---

### Step 8: Test the Integration

```bash
# Restart Django server
python manage.py runserver

# Create a ticket via Postman
POST http://localhost:8000/api/tickets/
Authorization: Bearer <your_token>
{
    "title": "Test WhatsApp",
    "description": "Testing WhatsApp Cloud API",
    "priority": "HIGH",
    "category": "BUG",
    "project_name": "Test Project"
}

# Check console output
📱 WhatsApp sent to admin_user: wamid.xxxxxxxx
```

**Check your WhatsApp** - you should receive the notification!

---

## 🔐 Step 9: Get Permanent Access Token (Production)

Temporary tokens expire after 24 hours. For production, create a permanent token:

### Method 1: System User Token (Recommended)

1. **Go to:** Meta Business Suite → Settings
2. **Business Settings → Users → System Users**
3. **Click:** "Add" → Create system user
4. **Name:** "Incident Management API"
5. **Role:** Admin
6. **Click:** "Generate New Token"
7. **Select your app**
8. **Permissions:** Select `whatsapp_business_messaging` and `whatsapp_business_management`
9. **Token Duration:** Never expire (recommended) or 60 days
10. **Click:** "Generate Token"
11. **Copy token** - this is your permanent token!

### Method 2: Long-Lived User Access Token

1. Use **Facebook Access Token Debugger:** https://developers.facebook.com/tools/debug/accesstoken/
2. **Paste** your temporary token
3. **Click:** "Extend Access Token"
4. **Copy** the extended token (valid for 60 days)

**Update settings.py with permanent token:**
```python
WHATSAPP_ACCESS_TOKEN = 'EAAxxxxxxxxxxxxxxxxxxxx'  # Permanent token
```

---

## 📱 Step 10: Get Your Own WhatsApp Number (Production)

The test number is limited. For production, add your own number:

### Requirements:
- Phone number not registered on WhatsApp
- Can receive voice calls or SMS
- Mobile or landline (with voice capability)

### Steps:

1. **Go to:** WhatsApp → API Setup → Phone Numbers
2. **Click:** "Add phone number"
3. **Enter:** Your business phone number
4. **Verify:** via SMS or voice call
5. **Register:** Complete business profile
   - Business name
   - Business category
   - Business description
   - Profile picture
6. **Submit for Review:** (usually approved within 24 hours)
7. **Get Phone Number ID** from the phone numbers list

**Update settings.py:**
```python
WHATSAPP_PHONE_NUMBER_ID = 'your_new_phone_number_id'
```

---

## 🧪 Testing Checklist

- [ ] Meta Developer account created
- [ ] App created and WhatsApp added
- [ ] Phone Number ID and Access Token obtained
- [ ] Test recipient numbers added to "To" list
- [ ] Django settings updated
- [ ] Server restarted
- [ ] WhatsApp numbers added to user profiles
- [ ] Test ticket created
- [ ] WhatsApp message received
- [ ] Message logged in Django admin

---

## 📊 Message Format Examples

### Admin - New Ticket:
```
🎫 *New Ticket Created*

*Client:* John Doe
*Title:* Login page not working
*Project:* Web Portal
*Priority:* HIGH
*Category:* BUG

*Description:*
Users cannot login to the portal...

Please review and assign this ticket.

_Incident Management System_
```

### Client - Ticket Opened:
```
✅ *Your Ticket Has Been Opened*

Hello John Doe,

Your ticket has been acknowledged.

*Ticket:* Login page not working
*Project:* Web Portal
*Status:* Opened

We will assign a developer shortly.

_Support Team_
```

---

## 🔍 Troubleshooting

### Error: "Access token has expired"
**Solution:** Generate a permanent token (Step 9)

### Error: "Recipient phone number not in allowed list"
**Solution:** Add phone number in Meta Developer Console → API Setup → Manage phone number list

### Error: "Invalid phone number format"
**Solution:** 
- Use format: `+1234567890` (country code + number, no spaces)
- Egypt: `+201234567890`
- US: `+12025551234`
- UK: `+447700123456`

### Error: "Phone number is already registered on WhatsApp"
**Solution:** For business number, you must use a number NOT already on personal WhatsApp

### No message sent, but no error:
**Check:**
1. Access Token is correct in settings.py
2. Phone Number ID is correct
3. Recipient number added to "To" list in Meta console
4. User has WhatsApp number in profile (with country code)
5. Server was restarted after configuration

---

## 💰 Pricing

### Free Tier:
- **1,000 conversations per month** FREE
- Conversation = 24-hour window after user message
- Business-initiated messages count as conversations

### Paid Tier:
- After 1,000 conversations
- ~$0.005 - $0.09 per conversation (varies by country)
- See: https://developers.facebook.com/docs/whatsapp/pricing

### What counts as a conversation:
- ✅ User replies within 24 hours → FREE (counts as 1 conversation)
- ✅ Business initiates message → Paid (if no recent conversation)

**For incident management:** Most notifications will be business-initiated, but 1,000/month should be sufficient for small teams.

---

## 🚀 Going to Production

### Checklist:

1. **Get permanent access token** (Step 9)
2. **Add your own phone number** (Step 10)
3. **Verify business** (if sending to unregistered numbers)
4. **Complete business profile**
5. **Enable production environment variables:**
   ```python
   from decouple import config
   
   WHATSAPP_ACCESS_TOKEN = config('WHATSAPP_ACCESS_TOKEN')
   WHATSAPP_PHONE_NUMBER_ID = config('WHATSAPP_PHONE_NUMBER_ID')
   ```
6. **Test thoroughly** with all user roles
7. **Monitor usage** in Meta Business Suite

---

## 📈 Monitoring

### Meta Business Suite Dashboard:

1. **Go to:** https://business.facebook.com
2. **Select:** Your business
3. **WhatsApp Manager → Insights**
4. **View:**
   - Messages sent
   - Delivery rate
   - Conversation count
   - Costs (if applicable)

### Django Admin:

- **Notification Logs → Filter by WhatsApp**
- Check SENT vs FAILED status
- Review error messages

---

## 🔐 Security Best Practices

1. **Never commit tokens to Git:**
   ```bash
   # .gitignore
   .env
   ```

2. **Use environment variables:**
   ```python
   # settings.py
   from decouple import config
   WHATSAPP_ACCESS_TOKEN = config('WHATSAPP_ACCESS_TOKEN')
   ```

3. **Rotate tokens periodically:** Every 90 days

4. **Restrict token permissions:** Only `whatsapp_business_messaging`

5. **Monitor usage:** Check for unusual activity

---

## 📖 Additional Resources

- **WhatsApp Cloud API Docs:** https://developers.facebook.com/docs/whatsapp/cloud-api
- **Getting Started:** https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- **Message Templates:** https://developers.facebook.com/docs/whatsapp/api/messages/message-templates
- **Pricing:** https://developers.facebook.com/docs/whatsapp/pricing
- **Support:** https://developers.facebook.com/support/

---

## 🆘 Common Issues

### Issue: "Unsupported get request"
**Cause:** Phone Number ID is wrong  
**Fix:** Check Phone Number ID in Meta Developer Console → WhatsApp → API Setup

### Issue: "Invalid OAuth access token"
**Cause:** Token expired or incorrect  
**Fix:** Generate new token from Meta Developer Console

### Issue: "Parameter value is not valid"
**Cause:** Phone number format is wrong  
**Fix:** Use format `1234567890` (no + or spaces in API call, but store as `+1234567890` in database)

### Issue: Message sent but not received
**Cause:** Recipient blocked your business number  
**Fix:** Ask recipient to unblock and message your WhatsApp Business number first

---

## ✅ Final Verification

Before going live:

- [ ] Permanent access token configured
- [ ] Own business phone number added
- [ ] All team members' numbers verified
- [ ] Test all notification types:
  - [ ] New ticket created
  - [ ] Ticket opened
  - [ ] Developer assigned
  - [ ] Work started
  - [ ] Work finished
  - [ ] Ticket closed
  - [ ] Ticket rejected
- [ ] Monitoring dashboard configured
- [ ] Error handling tested
- [ ] Logs reviewed

---

**Document Version:** 2.0 - WhatsApp Cloud API  
**Last Updated:** December 23, 2025  
**API Version:** v21.0
