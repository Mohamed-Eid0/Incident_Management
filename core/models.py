from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('CLIENT', 'Client'),
        ('ADMIN', 'Admin'),
        ('SUPPORT', 'Developer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    phone_number = models.CharField(max_length=30, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=30, blank=True, null=True, help_text="Phone number for WhatsApp notifications")
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


# class Project(models.Model):
#     """Client projects for ticket categorization"""
#     name = models.CharField(max_length=200)
#     description = models.TextField(blank=True, null=True)
#     client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects', limit_choices_to={'profile__role': 'CLIENT'})
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     def __str__(self):
#         return f"{self.name} - {self.client.username}"
    
#     class Meta:
#         verbose_name = "Project"
#         verbose_name_plural = "Projects"
#         ordering = ['-created_at']


class Ticket(models.Model):
    PRIORITY_CHOICES = [
        # ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]
    
    CATEGORY_CHOICES = [
        ('BUG', 'Bug'),
        ('PROBLEM', 'Problem'),
        ('SERVICE_DOWN', 'Service Down'),
        ('NEW_FEATURE', 'New Feature Request'),
    ]
    
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('OPENED', 'Opened'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('WAITING_APPROVAL', 'Waiting for Client Approval'),
        ('CLOSED', 'Closed'),
    ]
    
    # Basic Information
    project_name = models.CharField(max_length=150 , default='General')
    title = models.CharField(max_length=300)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES, default='PROBLEM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    # Assignment
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets')
    assigned_to = models.ManyToManyField(User, blank=True, related_name='assigned_tickets', limit_choices_to={'profile__role': 'SUPPORT'})
    assigned_team = models.CharField(max_length=100, blank=True, null=True, help_text="Team name if assigned to a team")
    
    # SLA (Service Level Agreement) Fields
    response_due_at = models.DateTimeField(null=True, blank=True, help_text="When admin should respond/open ticket (auto-calculated)")
    resolution_due_at = models.DateTimeField(null=True, blank=True, help_text="Expected resolution time (set by admin)")
    response_breached = models.BooleanField(default=False, help_text="If response SLA was breached")
    resolution_breached = models.BooleanField(default=False, help_text="If resolution SLA was breached")
    
    # Time Tracking
    estimated_resolution_time = models.DateTimeField(null=True, blank=True, help_text="ETA set by admin")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    opened_at = models.DateTimeField(null=True, blank=True, help_text="When admin opened the ticket")
    started_at = models.DateTimeField(null=True, blank=True, help_text="When support started working")
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="When support finished work")
    closed_at = models.DateTimeField(null=True, blank=True, help_text="When client approved and closed")
    
    def get_response_sla_minutes(self):
        """Get response SLA in minutes based on priority"""
        sla_map = {
            'HIGH': 30,      # 30 minutes
            'MEDIUM': 120,   # 2 hours
            'LOW': 1440,     # 24 hours (1 day)
        }
        return sla_map.get(self.priority, 120)  # Default to 2 hours
    
    def calculate_response_due_at(self):
        """Calculate when admin should respond based on priority"""
        from datetime import timedelta
        sla_minutes = self.get_response_sla_minutes()
        return self.created_at + timedelta(minutes=sla_minutes)
    
    def check_sla_breach(self):
        """Check if SLA has been breached"""
        from django.utils import timezone
        now = timezone.now()
        
        # Check response SLA breach (if not yet opened)
        if self.response_due_at and self.status == 'NEW' and now > self.response_due_at:
            self.response_breached = True
        
        # Check resolution SLA breach (if not yet resolved)
        if self.resolution_due_at and self.status not in ['RESOLVED', 'CLOSED'] and now > self.resolution_due_at:
            self.resolution_breached = True
    
    def __str__(self):
        return f"#{self.id} - {self.title} ({self.status})"
    
    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_by']),
            
        ]


class TicketAttachment(models.Model):
    """File attachments for tickets - supports multiple files per ticket"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file_data = models.BinaryField(help_text="Binary file data")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment for Ticket #{self.ticket.id}"
    
    class Meta:
        verbose_name = "Ticket Attachment"
        verbose_name_plural = "Ticket Attachments"
        ordering = ['-uploaded_at']


class TicketHistory(models.Model):
    """Audit trail for ticket status changes"""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_changes')
    status_from = models.CharField(max_length=20, choices=Ticket.STATUS_CHOICES, null=True, blank=True)
    status_to = models.CharField(max_length=20, choices=Ticket.STATUS_CHOICES)
    comment = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Ticket #{self.ticket.id} - {self.status_from} → {self.status_to}"
    
    class Meta:
        verbose_name = "Ticket History"
        verbose_name_plural = "Ticket Histories"
        ordering = ['-timestamp']


class NotificationLog(models.Model):
    """Log of all notifications sent"""
    NOTIFICATION_TYPE_CHOICES = [
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('SYSTEM', 'System Alert'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=15, choices=NOTIFICATION_TYPE_CHOICES, default='EMAIL')
    subject = models.CharField(max_length=300)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Read status tracking (for SYSTEM notifications primarily)
    is_read = models.BooleanField(default=False, help_text="Whether notification has been read by recipient")
    read_at = models.DateTimeField(null=True, blank=True, help_text="When notification was marked as read")
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.username} - {self.status}"
    
    def mark_as_read(self):
        """Mark notification as read with timestamp"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    class Meta:
        verbose_name = "Notification Log"
        verbose_name_plural = "Notification Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['recipient', 'notification_type', '-created_at']),
        ]