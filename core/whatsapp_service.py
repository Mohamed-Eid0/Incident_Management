"""
WhatsApp Notification Service for Incident Management System

This service handles sending WhatsApp messages for ticket status updates.
Uses WhatsApp Cloud API (Meta Business).

Setup Instructions:
1. pip install requests
2. Create WhatsApp Business Account at https://business.facebook.com
3. Set up WhatsApp Business API at https://developers.facebook.com
4. Get Phone Number ID and Access Token
5. Add to settings.py:
   WHATSAPP_ACCESS_TOKEN = 'your_access_token'
   WHATSAPP_PHONE_NUMBER_ID = 'your_phone_number_id'
   WHATSAPP_API_VERSION = 'v21.0'  # Current version
"""

from django.conf import settings
from django.contrib.auth.models import User
from .models import NotificationLog
import requests
import json


def get_whatsapp_config():
    """Get WhatsApp Cloud API configuration"""
    access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
    phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
    api_version = getattr(settings, 'WHATSAPP_API_VERSION', 'v21.0')
    
    if not access_token or not phone_number_id:
        print("⚠️ WARNING: WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID not configured in settings.py")
        return None
    
    return {
        'access_token': access_token,
        'phone_number_id': phone_number_id,
        'api_version': api_version,
        'url': f'https://graph.facebook.com/{api_version}/{phone_number_id}/messages'
    }


def send_whatsapp_message(ticket, recipient, message):
    """
    Send WhatsApp message using Cloud API and log notification
    
    Args:
        ticket: Ticket instance
        recipient: User instance (must have whatsapp_number in profile)
        message: Message text to send
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    # Check if recipient has WhatsApp number
    if not hasattr(recipient, 'profile') or not recipient.profile.whatsapp_number:
        print(f"⚠️ User {recipient.username} has no WhatsApp number configured")
        return False
    
    # Get WhatsApp configuration
    config = get_whatsapp_config()
    if not config:
        print("⚠️ WhatsApp Cloud API not configured - skipping WhatsApp notification")
        # Log as failed
        NotificationLog.objects.create(
            ticket=ticket,
            recipient=recipient,
            notification_type='WHATSAPP',
            subject='WhatsApp Notification',
            message=message,
            status='FAILED',
            error_message='WhatsApp Cloud API not configured'
        )
        return False
    
    # Format recipient number (remove 'whatsapp:' prefix if present, keep only digits with country code)
    to_number = recipient.profile.whatsapp_number.replace('whatsapp:', '').replace('+', '').replace(' ', '').replace('-', '')
    
    # Prepare API request
    headers = {
        'Authorization': f'Bearer {config["access_token"]}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messaging_product': 'whatsapp',
        'to': to_number,
        'type': 'text',
        'text': {
            'preview_url': False,
            'body': message
        }
    }
    
    try:
        # Send message via WhatsApp Cloud API
        response = requests.post(
            config['url'],
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get('messages'):
            message_id = response_data['messages'][0].get('id', 'unknown')
            print(f"📱 WhatsApp sent to {recipient.username}: {message_id}")
            
            # Log successful notification
            NotificationLog.objects.create(
                ticket=ticket,
                recipient=recipient,
                notification_type='WHATSAPP',
                subject='WhatsApp Notification',
                message=message,
                status='SENT'
            )
            return True
        else:
            error_msg = response_data.get('error', {}).get('message', 'Unknown error')
            print(f"❌ WhatsApp send failed: {error_msg}")
            
            # Log failed notification
            NotificationLog.objects.create(
                ticket=ticket,
                recipient=recipient,
                notification_type='WHATSAPP',
                subject='WhatsApp Notification',
                message=message,
                status='FAILED',
                error_message=f"API Error: {error_msg}"
            )
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ WhatsApp send failed: {str(e)}")
        
        # Log failed notification
        NotificationLog.objects.create(
            ticket=ticket,
            recipient=recipient,
            notification_type='WHATSAPP',
            subject='WhatsApp Notification',
            message=message,
            status='FAILED',
            error_message=str(e)
        )
        return False
    except Exception as e:
        print(f"❌ WhatsApp send failed: {str(e)}")
        
        # Log failed notification
        NotificationLog.objects.create(
            ticket=ticket,
            recipient=recipient,
            notification_type='WHATSAPP',
            subject='WhatsApp Notification',
            message=message,
            status='FAILED',
            error_message=str(e)
        )
        return False


def notify_admin_new_ticket_whatsapp(ticket):
    """
    Notify admin via WhatsApp when a new ticket is created by client
    """
    # Get all admins with WhatsApp numbers
    admins = User.objects.filter(profile__role='ADMIN').exclude(profile__whatsapp_number__isnull=True).exclude(profile__whatsapp_number='')
    
    if not admins.exists():
        print(f"⚠️ No admin users with WhatsApp numbers found for ticket #{ticket.id}")
        return
    
    print(f"📱 Sending WhatsApp to {admins.count()} admin(s) for ticket #{ticket.id}")
    
    # Create message
    message = f"""🎫 *New Ticket Created*

*Client:* {ticket.created_by.get_full_name() or ticket.created_by.username}
*Title:* {ticket.title}
*Project:* {ticket.project_name}
*Priority:* {ticket.get_priority_display()}
*Category:* {ticket.get_category_display()}

*Description:*
{ticket.description[:200]}{'...' if len(ticket.description) > 200 else ''}

Please review and assign this ticket as soon as possible.

_Incident Management System_
    """
    
    for admin in admins:
        send_whatsapp_message(ticket, admin, message)


def notify_client_ticket_opened_whatsapp(ticket):
    """
    Notify client via WhatsApp when admin opens their ticket
    """
    if not hasattr(ticket.created_by, 'profile') or not ticket.created_by.profile.whatsapp_number:
        return
    
    message = f"""✅ *Your Ticket Has Been Opened*

Hello {ticket.created_by.get_full_name() or ticket.created_by.username},

Your ticket has been acknowledged and opened by our support team.

*Ticket:* {ticket.title}
*Project:* {ticket.project_name}
*Status:* Opened

We are reviewing your issue and will assign it to a developer shortly.

_Support Team_
    """
    
    send_whatsapp_message(ticket, ticket.created_by, message)


def notify_developer_assignment_whatsapp(ticket, developers):
    """
    Notify developer(s) via WhatsApp when assigned to a ticket
    """
    for developer in developers:
        if not hasattr(developer, 'profile') or not developer.profile.whatsapp_number:
            continue
        
        message = f"""🔧 *New Task Assigned*

Hello {developer.get_full_name() or developer.username},

You have been assigned to a new ticket:

*Title:* {ticket.title}
*Project:* {ticket.project_name}
*Priority:* {ticket.get_priority_display()}
*Category:* {ticket.get_category_display()}
*SLA Resolution:* {ticket.resolution_due_at.strftime('%Y-%m-%d %H:%M') if ticket.resolution_due_at else 'Not set'}

*Description:*
{ticket.description[:200]}{'...' if len(ticket.description) > 200 else ''}

Please start working on this ticket as soon as possible.

_Incident Management System_
        """
        
        send_whatsapp_message(ticket, developer, message)


def notify_client_work_started_whatsapp(ticket):
    """
    Notify client via WhatsApp when developer starts working on their ticket
    """
    if not hasattr(ticket.created_by, 'profile') or not ticket.created_by.profile.whatsapp_number:
        return
    
    message = f"""🚀 *Work Started on Your Ticket*

Hello {ticket.created_by.get_full_name() or ticket.created_by.username},

Good news! A developer has started working on your ticket.

*Ticket:* {ticket.title}
*Project:* {ticket.project_name}
*Assigned To:* {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}
*Status:* In Progress

We will notify you once the work is completed.

_Support Team_
    """
    
    send_whatsapp_message(ticket, ticket.created_by, message)


def notify_client_work_finished_whatsapp(ticket):
    """
    Notify client via WhatsApp when developer finishes work and awaits approval
    """
    if not hasattr(ticket.created_by, 'profile') or not ticket.created_by.profile.whatsapp_number:
        return
    
    message = f"""✅ *Your Ticket Has Been Resolved*

Hello {ticket.created_by.get_full_name() or ticket.created_by.username},

Your ticket has been resolved and is now waiting for your approval.

*Ticket:* {ticket.title}
*Project:* {ticket.project_name}
*Resolved By:* {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Support Team'}

Please review the resolution and approve if the issue is fixed. If the issue is not resolved, you can reject and request additional work.

_Support Team_
    """
    
    send_whatsapp_message(ticket, ticket.created_by, message)


def notify_admin_work_finished_whatsapp(ticket):
    """
    Notify admin via WhatsApp when developer finishes work
    """
    admins = User.objects.filter(profile__role='ADMIN').exclude(profile__whatsapp_number__isnull=True).exclude(profile__whatsapp_number='')
    
    message = f"""⏳ *Ticket Resolved - Awaiting Client Approval*

A ticket has been marked as resolved and is awaiting client approval:

*Ticket:* {ticket.title}
*Project:* {ticket.project_name}
*Client:* {ticket.created_by.get_full_name() or ticket.created_by.username}
*Resolved By:* {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}
*Status:* Waiting for Approval

_Incident Management System_
    """
    
    for admin in admins:
        send_whatsapp_message(ticket, admin, message)


def notify_ticket_closed_whatsapp(ticket):
    """
    Notify relevant parties via WhatsApp when ticket is closed
    """
    # Notify admin
    admins = User.objects.filter(profile__role='ADMIN').exclude(profile__whatsapp_number__isnull=True).exclude(profile__whatsapp_number='')
    
    admin_message = f"""✅ *Ticket Closed*

A ticket has been closed by the client:

*Ticket:* {ticket.title}
*Project:* {ticket.project_name}
*Client:* {ticket.created_by.get_full_name() or ticket.created_by.username}
*Resolved By:* {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}

The client has approved the resolution.

_Incident Management System_
    """
    
    for admin in admins:
        send_whatsapp_message(ticket, admin, admin_message)
    
    # Notify developer
    if ticket.assigned_to and hasattr(ticket.assigned_to, 'profile') and ticket.assigned_to.profile.whatsapp_number:
        dev_message = f"""🎉 *Ticket Closed - Great Job!*

Hello {ticket.assigned_to.get_full_name() or ticket.assigned_to.username},

The ticket you worked on has been closed and approved by the client:

*Ticket:* {ticket.title}
*Project:* {ticket.project_name}
*Client:* {ticket.created_by.get_full_name() or ticket.created_by.username}

Great work!

_Incident Management System_
        """
        
        send_whatsapp_message(ticket, ticket.assigned_to, dev_message)


def notify_ticket_rejected_whatsapp(ticket, rejection_reason):
    """
    Notify developer via WhatsApp when client rejects the resolution
    """
    if not ticket.assigned_to:
        return
    
    if not hasattr(ticket.assigned_to, 'profile') or not ticket.assigned_to.profile.whatsapp_number:
        return
    
    message = f"""🔄 *Ticket Rejected - More Work Needed*

Hello {ticket.assigned_to.get_full_name() or ticket.assigned_to.username},

The client has rejected the resolution for this ticket:

*Ticket:* {ticket.title}
*Project:* {ticket.project_name}
*Client:* {ticket.created_by.get_full_name() or ticket.created_by.username}

*Rejection Reason:*
{rejection_reason}

Please review the feedback and continue working on the ticket.

_Incident Management System_
    """
    
    send_whatsapp_message(ticket, ticket.assigned_to, message)
