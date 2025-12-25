"""
Notification Service for sending real-time WebSocket notifications

This service sends notifications via WebSocket to specific users or groups
Works alongside email and WhatsApp notifications
"""
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from .models import NotificationLog


def send_websocket_notification(user_ids, notification_type, ticket_data, message, ticket=None):
    """
    Send real-time notification to specific users via WebSocket and save to database
    
    Args:
        user_ids: List of user IDs or single user ID
        notification_type: Type of notification (ticket_created, ticket_opened, etc.)
        ticket_data: Dictionary containing ticket information
        message: Human-readable message
        ticket: Ticket instance (optional, for logging)
    """
    channel_layer = get_channel_layer()
    
    # Ensure user_ids is a list
    if not isinstance(user_ids, list):
        user_ids = [user_ids]
    
    # Send notification to each user
    for user_id in user_ids:
        group_name = f'user_{user_id}'
        
        notification_data = {
            'type': 'send_notification',
            'data': {
                'notification_type': notification_type,
                'message': message,
                'ticket': ticket_data,
                'timestamp': ticket_data.get('updated_at') or ticket_data.get('created_at')
            }
        }
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            notification_data
        )
        
        # Save SYSTEM notification to database
        try:
            recipient = User.objects.get(id=user_id)
            NotificationLog.objects.create(
                ticket=ticket,
                recipient=recipient,
                notification_type='SYSTEM',
                subject=f'{notification_type.replace("_", " ").title()}',
                message=message,
                status='SENT'
            )
            print(f"✅ SYSTEM notification saved for user {user_id}")
        except Exception as e:
            print(f"❌ Failed to save SYSTEM notification for user {user_id}: {e}")


def notify_admins_new_ticket(ticket):
    """
    Notify all admins when a new ticket is created
    """
    # Get all admin users
    admin_users = User.objects.filter(profile__role='ADMIN')
    admin_ids = list(admin_users.values_list('id', flat=True))
    
    if not admin_ids:
        return
    
    ticket_data = {
        'id': ticket.id,
        'title': ticket.title,
        'priority': ticket.priority,
        'priority_display': ticket.get_priority_display(),
        'category': ticket.category,
        'category_display': ticket.get_category_display(),
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'created_by': ticket.created_by.get_full_name() or ticket.created_by.username,
        'project_name': ticket.project_name,
        'created_at': ticket.created_at.isoformat() if ticket.created_at else None
    }
    
    message = f"New {ticket.get_priority_display()} priority ticket created: {ticket.title}"
    
    send_websocket_notification(
        user_ids=admin_ids,
        notification_type='ticket_created',
        ticket_data=ticket_data,
        message=message,
        ticket=ticket
    )


def notify_client_ticket_opened_ws(ticket):
    """
    Notify client when admin opens their ticket
    """
    ticket_data = {
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'opened_at': ticket.opened_at.isoformat() if ticket.opened_at else None
    }
    
    message = f"Your ticket '{ticket.title}' has been opened and acknowledged by admin"
    
    send_websocket_notification(
        user_ids=ticket.created_by.id,
        notification_type='ticket_opened',
        ticket_data=ticket_data,
        message=message,
        ticket=ticket
    )


def notify_developers_assignment_ws(ticket, developers):
    """
    Notify developers when assigned to a ticket
    
    Args:
        ticket: Ticket instance
        developers: List of User objects (developers)
    """
    developer_ids = [dev.id for dev in developers]
    
    ticket_data = {
        'id': ticket.id,
        'title': ticket.title,
        'description': ticket.description,
        'priority': ticket.priority,
        'priority_display': ticket.get_priority_display(),
        'category': ticket.category,
        'category_display': ticket.get_category_display(),
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'assigned_to_names': [dev.get_full_name() or dev.username for dev in developers],
        'created_by': ticket.created_by.get_full_name() or ticket.created_by.username,
        'project_name': ticket.project_name,
        'resolution_due_at': ticket.resolution_due_at.isoformat() if ticket.resolution_due_at else None
    }
    
    message = f"You have been assigned to ticket: {ticket.title}"
    
    send_websocket_notification(
        user_ids=developer_ids,
        notification_type='ticket_assigned',
        ticket_data=ticket_data,
        message=message,
        ticket=ticket
    )


def notify_client_work_started_ws(ticket):
    """
    Notify client when developer starts working on their ticket
    """
    ticket_data = {
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'started_at': ticket.started_at.isoformat() if ticket.started_at else None
    }
    
    message = f"Work has started on your ticket: {ticket.title}"
    
    send_websocket_notification(
        user_ids=ticket.created_by.id,
        notification_type='work_started',
        ticket_data=ticket_data,
        message=message,
        ticket=ticket
    )


def notify_client_work_finished_ws(ticket):
    """
    Notify client when developer finishes work (awaiting approval)
    """
    ticket_data = {
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'resolved_at': ticket.resolved_at.isoformat() if ticket.resolved_at else None
    }
    
    message = f"Work completed on your ticket '{ticket.title}'. Please review and approve."
    
    send_websocket_notification(
        user_ids=ticket.created_by.id,
        notification_type='work_finished',
        ticket_data=ticket_data,
        message=message,
        ticket=ticket
    )


def notify_ticket_approved_ws(ticket):
    """
    Notify admin and assigned developers when client approves ticket
    """
    # Get all admins
    admin_users = User.objects.filter(profile__role='ADMIN')
    admin_ids = list(admin_users.values_list('id', flat=True))
    
    # Get assigned developers
    developer_ids = list(ticket.assigned_to.values_list('id', flat=True))
    
    # Combine recipients
    recipient_ids = list(set(admin_ids + developer_ids))
    
    if not recipient_ids:
        return
    
    ticket_data = {
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'closed_at': ticket.closed_at.isoformat() if ticket.closed_at else None,
        'created_by': ticket.created_by.get_full_name() or ticket.created_by.username
    }
    
    message = f"Ticket '{ticket.title}' has been approved and closed by client"
    
    send_websocket_notification(
        user_ids=recipient_ids,
        notification_type='ticket_approved',
        ticket_data=ticket_data,
        message=message,
        ticket=ticket
    )


def notify_ticket_rejected_ws(ticket, comment):
    """
    Notify admin and assigned developers when client rejects ticket
    """
    # Get all admins
    admin_users = User.objects.filter(profile__role='ADMIN')
    admin_ids = list(admin_users.values_list('id', flat=True))
    
    # Get assigned developers
    developer_ids = list(ticket.assigned_to.values_list('id', flat=True))
    
    # Combine recipients
    recipient_ids = list(set(admin_ids + developer_ids))
    
    if not recipient_ids:
        return
    
    ticket_data = {
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'status_display': ticket.get_status_display(),
        'created_by': ticket.created_by.get_full_name() or ticket.created_by.username,
        'rejection_comment': comment
    }
    
    message = f"Ticket '{ticket.title}' has been rejected by client. Reason: {comment}"
    
    send_websocket_notification(
        user_ids=recipient_ids,
        notification_type='ticket_rejected',
        ticket_data=ticket_data,
        message=message,
        ticket=ticket
    )
