from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import NotificationLog


def send_notification_email(ticket, recipient, subject, message, html_message=None, notification_type='EMAIL'):
    """
    Send email and log notification
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
            html_message=html_message,  # HTML version of email
        )
        
        # Log successful notification
        NotificationLog.objects.create(
            ticket=ticket,
            recipient=recipient,
            notification_type=notification_type,
            subject=subject,
            message=message,
            status='SENT'
        )
        return True
    except Exception as e:
        # Log failed notification
        NotificationLog.objects.create(
            ticket=ticket,
            recipient=recipient,
            notification_type=notification_type,
            subject=subject,
            message=message,
            status='FAILED',
            error_message=str(e)
        )
        return False


def notify_admin_new_ticket(ticket):
    """
    Notify admin when a new ticket is created by client
    """
    # Get all admins
    admins = User.objects.filter(profile__role='ADMIN')
    
    if not admins.exists():
        print(f"⚠️ WARNING: No admin users found! Cannot send email notification for ticket #{ticket.id}")
        return
    
    print(f"📧 Sending email to {admins.count()} admin(s) for ticket #{ticket.id}")
    
    subject = f"New Ticket Created - {ticket.title}"
    ticket_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}/admin/core/ticket/{ticket.id}/change/"
    
    # Plain text version
    message = f"""
Hello Admin,

A new ticket has been created:

Client: {ticket.created_by.get_full_name() or ticket.created_by.username}
Project Name: {ticket.project_name}
Priority: {ticket.get_priority_display()}
Category: {ticket.get_category_display()}

Problem Description:
{ticket.description}

Please review and assign this ticket as soon as possible.

Best regards,
Incident Management System
    """
    
    # HTML version with clickable link
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2c3e50;">New Ticket Created</h2>
            <p>Hello Admin,</p>
            <p>A new ticket has been created:</p>
            <table style="margin: 20px 0; border-collapse: collapse;">
                <tr><td style="padding: 5px 10px; font-weight: bold;">Client:</td><td style="padding: 5px 10px;">{ticket.created_by.get_full_name() or ticket.created_by.username}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Project Name:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Priority:</td><td style="padding: 5px 10px;">{ticket.get_priority_display()}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Category:</td><td style="padding: 5px 10px;">{ticket.get_category_display()}</td></tr>
            </table>
            <p><strong>Problem Description:</strong></p>
            <p style="background-color: #f4f4f4; padding: 10px; border-left: 4px solid #3498db;">{ticket.description}</p>
            <p><a href="{ticket_url}" style="display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px;">Click here to view ticket details</a></p>
            <p>Please review and assign this ticket as soon as possible.</p>
            <p style="margin-top: 20px;">Best regards,<br>Incident Management System</p>
        </body>
    </html>
    """
    
    for admin in admins:
        send_notification_email(ticket, admin, subject, message, html_message)


def notify_client_ticket_opened(ticket):
    """
    Notify client when admin opens their ticket
    """
    subject = f"Your Ticket Has Been Opened - {ticket.title}"
    
    # Plain text version
    message = f"""
Hello {ticket.created_by.get_full_name() or ticket.created_by.username},

Your ticket has been acknowledged and opened by our support team.

Ticket: {ticket.title}
Project: {ticket.project_name}
Status: Opened

We are reviewing your issue and will assign it to a developer shortly.

Best regards,
Support Team
    """
    
    # HTML version
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #27ae60;">Your Ticket Has Been Opened</h2>
            <p>Hello {ticket.created_by.get_full_name() or ticket.created_by.username},</p>
            <p>Your ticket has been acknowledged and opened by our support team.</p>
            <table style="margin: 20px 0;">
                <tr><td style="padding: 5px 10px; font-weight: bold;">Ticket:</td><td style="padding: 5px 10px;">{ticket.title}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Project:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Status:</td><td style="padding: 5px 10px;"><span style="color: #27ae60; font-weight: bold;">Opened</span></td></tr>
            </table>
            <p>We are reviewing your issue and will assign it to a developer shortly.</p>
            <p style="margin-top: 20px;">Best regards,<br>Support Team</p>
        </body>
    </html>
    """
    
    send_notification_email(ticket, ticket.created_by, subject, message, html_message)


def notify_developer_assignment(ticket, developers):
    """
    Notify developer(s) when assigned to a ticket
    """
    subject = f"New Task Assigned - {ticket.title}"
    ticket_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}/api/tickets/{ticket.id}/"
    
    for developer in developers:
        # Plain text version
        message = f"""
Hello {developer.get_full_name() or developer.username},

You have been assigned to a new ticket:

Project Name: {ticket.project_name}
Priority: {ticket.get_priority_display()}
Category: {ticket.get_category_display()}
SLA Resolution Time: {ticket.resolution_due_at.strftime('%Y-%m-%d %H:%M') if ticket.resolution_due_at else 'Not set'}
Estimated Resolution: {ticket.estimated_resolution_time.strftime('%Y-%m-%d %H:%M') if ticket.estimated_resolution_time else 'Not set'}

Problem Description:
{ticket.description}

Please start working on this ticket as soon as possible.

Best regards,
Incident Management System
        """
        
        # HTML version with clickable link
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #e67e22;">New Task Assigned</h2>
                <p>Hello {developer.get_full_name() or developer.username},</p>
                <p>You have been assigned to a new ticket:</p>
                <table style="margin: 20px 0;">
                    <tr><td style="padding: 5px 10px; font-weight: bold;">Project Name:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                    <tr><td style="padding: 5px 10px; font-weight: bold;">Priority:</td><td style="padding: 5px 10px;">{ticket.get_priority_display()}</td></tr>
                    <tr><td style="padding: 5px 10px; font-weight: bold;">Category:</td><td style="padding: 5px 10px;">{ticket.get_category_display()}</td></tr>
                    <tr><td style="padding: 5px 10px; font-weight: bold;">SLA Resolution Time:</td><td style="padding: 5px 10px;">{ticket.resolution_due_at.strftime('%Y-%m-%d %H:%M') if ticket.resolution_due_at else 'Not set'}</td></tr>
                    <tr><td style="padding: 5px 10px; font-weight: bold;">Estimated Resolution:</td><td style="padding: 5px 10px;">{ticket.estimated_resolution_time.strftime('%Y-%m-%d %H:%M') if ticket.estimated_resolution_time else 'Not set'}</td></tr>
                </table>
                <p><strong>Problem Description:</strong></p>
                <p style="background-color: #f4f4f4; padding: 10px; border-left: 4px solid #e67e22;">{ticket.description}</p>
                <p><a href="{ticket_url}" style="display: inline-block; padding: 10px 20px; background-color: #e67e22; color: white; text-decoration: none; border-radius: 5px;">Click here to view ticket details</a></p>
                <p>Please start working on this ticket as soon as possible.</p>
                <p style="margin-top: 20px;">Best regards,<br>Incident Management System</p>
            </body>
        </html>
        """
        
        send_notification_email(ticket, developer, subject, message, html_message)


def notify_client_work_started(ticket):
    """
    Notify client when developer starts working on their ticket
    """
    subject = f"Work Started on Your Ticket - {ticket.title}"
    
    # Plain text version
    message = f"""
Hello {ticket.created_by.get_full_name() or ticket.created_by.username},

Good news! A developer has started working on your ticket.

Ticket: {ticket.title}
Project: {ticket.project_name}
Assigned To: {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}
Status: In Progress

We will notify you once the work is completed.

Best regards,
Support Team
    """
    
    # HTML version
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #3498db;">Work Started on Your Ticket</h2>
            <p>Hello {ticket.created_by.get_full_name() or ticket.created_by.username},</p>
            <p><strong>Good news!</strong> A developer has started working on your ticket.</p>
            <table style="margin: 20px 0;">
                <tr><td style="padding: 5px 10px; font-weight: bold;">Ticket:</td><td style="padding: 5px 10px;">{ticket.title}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Project:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Assigned To:</td><td style="padding: 5px 10px;">{ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Status:</td><td style="padding: 5px 10px;"><span style="color: #3498db; font-weight: bold;">In Progress</span></td></tr>
            </table>
            <p>We will notify you once the work is completed.</p>
            <p style="margin-top: 20px;">Best regards,<br>Support Team</p>
        </body>
    </html>
    """
    
    send_notification_email(ticket, ticket.created_by, subject, message, html_message)


def notify_client_work_finished(ticket):
    """
    Notify client when developer finishes work and awaits approval
    """
    subject = "Your Ticket Has Been Resolved - Awaiting Approval"
    ticket_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}/api/tickets/{ticket.id}/"
    
    # Plain text version
    message = f"""
Hello {ticket.created_by.get_full_name() or ticket.created_by.username},

Your ticket has been resolved and is now waiting for your approval.

Ticket: {ticket.title}
Project: {ticket.project_name}
Resolved By: {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Support Team'}

If the issue is not resolved, you can reject and request additional work.

Best regards,
Support Team
    """
    
    # HTML version with clickable link
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #27ae60;">Your Ticket Has Been Resolved</h2>
            <p>Hello {ticket.created_by.get_full_name() or ticket.created_by.username},</p>
            <p>Your ticket has been resolved and is now waiting for your approval.</p>
            <table style="margin: 20px 0;">
                <tr><td style="padding: 5px 10px; font-weight: bold;">Ticket:</td><td style="padding: 5px 10px;">{ticket.title}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Project:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Resolved By:</td><td style="padding: 5px 10px;">{ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Support Team'}</td></tr>
            </table>
            <p><a href="{ticket_url}" style="display: inline-block; padding: 10px 20px; background-color: #27ae60; color: white; text-decoration: none; border-radius: 5px;">Click here to review and approve</a></p>
            <p>If the issue is not resolved, you can reject and request additional work.</p>
            <p style="margin-top: 20px;">Best regards,<br>Support Team</p>
        </body>
    </html>
    """
    
    send_notification_email(ticket, ticket.created_by, subject, message, html_message)


def notify_admin_work_finished(ticket):
    """
    Notify admin when developer finishes work
    """
    admins = User.objects.filter(profile__role='ADMIN')
    
    subject = f"Ticket Resolved - Awaiting Client Approval - {ticket.title}"
    ticket_url = f"{settings.FRONTEND_URL or 'http://localhost:8000'}/admin/core/ticket/{ticket.id}/change/"
    
    # Plain text version
    message = f"""
Hello Admin,

A ticket has been marked as resolved and is awaiting client approval:

Ticket: {ticket.title}
Project: {ticket.project_name}
Client: {ticket.created_by.get_full_name() or ticket.created_by.username}
Resolved By: {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}
Status: Waiting for Approval

Best regards,
Incident Management System
    """
    
    # HTML version with clickable link
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #9b59b6;">Ticket Resolved - Awaiting Client Approval</h2>
            <p>Hello Admin,</p>
            <p>A ticket has been marked as resolved and is awaiting client approval:</p>
            <table style="margin: 20px 0;">
                <tr><td style="padding: 5px 10px; font-weight: bold;">Ticket:</td><td style="padding: 5px 10px;">{ticket.title}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Project:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Client:</td><td style="padding: 5px 10px;">{ticket.created_by.get_full_name() or ticket.created_by.username}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Resolved By:</td><td style="padding: 5px 10px;">{ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Status:</td><td style="padding: 5px 10px;"><span style="color: #9b59b6; font-weight: bold;">Waiting for Approval</span></td></tr>
            </table>
            <p><a href="{ticket_url}" style="display: inline-block; padding: 10px 20px; background-color: #9b59b6; color: white; text-decoration: none; border-radius: 5px;">Click here to view ticket</a></p>
            <p style="margin-top: 20px;">Best regards,<br>Incident Management System</p>
        </body>
    </html>
    """
    
    for admin in admins:
        send_notification_email(ticket, admin, subject, message, html_message)


def notify_ticket_closed(ticket):
    """
    Notify relevant parties when ticket is closed
    """
    # Notify admin
    admins = User.objects.filter(profile__role='ADMIN')
    
    subject = f"Ticket Closed - {ticket.title}"
    
    # Admin plain text version
    admin_message = f"""
Hello Admin,

A ticket has been closed by the client:

Ticket: {ticket.title}
Project: {ticket.project_name}
Client: {ticket.created_by.get_full_name() or ticket.created_by.username}
Resolved By: {ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}

The client has approved the resolution.

Best regards,
Incident Management System
    """
    
    # Admin HTML version
    admin_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2ecc71;">Ticket Closed Successfully</h2>
            <p>Hello Admin,</p>
            <p>A ticket has been closed by the client:</p>
            <table style="margin: 20px 0;">
                <tr><td style="padding: 5px 10px; font-weight: bold;">Ticket:</td><td style="padding: 5px 10px;">{ticket.title}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Project:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Client:</td><td style="padding: 5px 10px;">{ticket.created_by.get_full_name() or ticket.created_by.username}</td></tr>
                <tr><td style="padding: 5px 10px; font-weight: bold;">Resolved By:</td><td style="padding: 5px 10px;">{ticket.assigned_to.get_full_name() or ticket.assigned_to.username if ticket.assigned_to else 'Team'}</td></tr>
            </table>
            <p style="color: #2ecc71; font-weight: bold;">✓ The client has approved the resolution.</p>
            <p style="margin-top: 20px;">Best regards,<br>Incident Management System</p>
        </body>
    </html>
    """
    
    for admin in admins:
        send_notification_email(ticket, admin, subject, admin_message, admin_html)
    
    # Notify developer
    if ticket.assigned_to:
        # Developer plain text version
        dev_message = f"""
Hello {ticket.assigned_to.get_full_name() or ticket.assigned_to.username},

The ticket you worked on has been closed and approved by the client:

Ticket: {ticket.title}
Project: {ticket.project_name}
Client: {ticket.created_by.get_full_name() or ticket.created_by.username}

Great work!

Best regards,
Incident Management System
        """
        
        # Developer HTML version
        dev_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2ecc71;">Ticket Closed - Great Job! 🎉</h2>
                <p>Hello {ticket.assigned_to.get_full_name() or ticket.assigned_to.username},</p>
                <p>The ticket you worked on has been closed and approved by the client:</p>
                <table style="margin: 20px 0;">
                    <tr><td style="padding: 5px 10px; font-weight: bold;">Ticket:</td><td style="padding: 5px 10px;">{ticket.title}</td></tr>
                    <tr><td style="padding: 5px 10px; font-weight: bold;">Project:</td><td style="padding: 5px 10px;">{ticket.project_name}</td></tr>
                    <tr><td style="padding: 5px 10px; font-weight: bold;">Client:</td><td style="padding: 5px 10px;">{ticket.created_by.get_full_name() or ticket.created_by.username}</td></tr>
                </table>
                <p style="background-color: #d5f4e6; padding: 15px; border-radius: 5px; color: #27ae60; font-weight: bold; text-align: center;">Great work!</p>
                <p style="margin-top: 20px;">Best regards,<br>Incident Management System</p>
            </body>
        </html>
        """
        
        send_notification_email(ticket, ticket.assigned_to, subject, dev_message, dev_html)
