from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Ticket


# Signal disabled - UserProfile is created via admin inline or manually
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, raw, **kwargs):
#     """Automatically create UserProfile when a User is created"""
#     # Don't create during fixtures or if already exists
#     if created and not raw:
#         # Use get_or_create to avoid conflicts with admin inline
#         UserProfile.objects.get_or_create(user=instance, defaults={'role': 'CLIENT'})


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    # Ensure profile exists
    if not hasattr(instance, 'profile'):
        UserProfile.objects.get_or_create(user=instance, defaults={'role': 'CLIENT'})


@receiver(pre_save, sender=Ticket)
def track_ticket_status_change(sender, instance, **kwargs):
    """Track status changes and update timestamps"""
    if instance.pk:  # Only for existing tickets
        try:
            old_ticket = Ticket.objects.get(pk=instance.pk)
            
            # Store old status and assignment for use in post_save signal
            instance._old_status = old_ticket.status
            instance._old_assigned_to = old_ticket.assigned_to
            
            # If status changed, update timestamps
            if old_ticket.status != instance.status:
                from django.utils import timezone
                
                # if instance.status == 'NEW' and not instance.created_at:
                #     instance.created_at = timezone.now()
                if instance.status == 'OPENED' and not instance.opened_at:
                    instance.opened_at = timezone.now()
                elif instance.status == 'IN_PROGRESS' and not instance.started_at:
                    instance.started_at = timezone.now()
                elif instance.status == 'RESOLVED' and not instance.resolved_at:
                    instance.resolved_at = timezone.now()
                elif instance.status == 'WAITING_APPROVAL' and not instance.resolved_at:
                    instance.resolved_at = timezone.now()
                elif instance.status == 'CLOSED' and not instance.closed_at:
                    instance.closed_at = timezone.now()
        except Ticket.DoesNotExist:
            pass
    else:
        # For new tickets, mark as NEW and calculate response SLA
        instance._old_status = None
        instance._old_assigned_to = None
    
    # Always calculate response_due_at for new tickets if not set
    if not instance.pk and not instance.response_due_at:
        from datetime import timedelta
        sla_minutes = instance.get_response_sla_minutes()
        # Use timezone.now() since created_at isn't set yet
        from django.utils import timezone
        instance.response_due_at = timezone.now() + timedelta(minutes=sla_minutes)
    
    # Check for SLA breaches before saving
    if instance.pk:  # Only check for existing tickets
        instance.check_sla_breach()


@receiver(post_save, sender=Ticket)
def send_ticket_notifications(sender, instance, created, **kwargs):
    """
    Send email and WhatsApp notifications after ticket STATUS changes
    
    NOTE: Assignment notifications are handled explicitly in views.py
    This signal only handles automatic status change notifications
    History entries are created by views with correct user context
    """
    if not created and instance.pk:
        # Get old status from pre_save signal
        old_status = getattr(instance, '_old_status', None)
        
        # ONLY handle STATUS changes - assignment is handled in views
        if old_status and old_status != instance.status:
            from .email_service import (
                notify_client_ticket_opened, notify_client_work_started,
                notify_client_work_finished, notify_admin_work_finished
            )
            from .whatsapp_service import (
                notify_client_ticket_opened_whatsapp, notify_client_work_started_whatsapp,
                notify_client_work_finished_whatsapp, notify_admin_work_finished_whatsapp,
                notify_ticket_closed_whatsapp
            )
            
            if instance.status == 'OPENED' and old_status == 'NEW':
                # Send email
                notify_client_ticket_opened(instance)
                # Send WhatsApp
                notify_client_ticket_opened_whatsapp(instance)
            elif instance.status == 'IN_PROGRESS' and old_status in ['OPENED', 'WAITING_APPROVAL']:
                # Send email
                notify_client_work_started(instance)
                # Send WhatsApp
                notify_client_work_started_whatsapp(instance)
            elif instance.status == 'RESOLVED' and old_status == 'IN_PROGRESS':
                # Send emails
                notify_client_work_finished(instance)
                notify_admin_work_finished(instance)
                # Send WhatsApp
                notify_client_work_finished_whatsapp(instance)
                notify_admin_work_finished_whatsapp(instance)
            elif instance.status == 'CLOSED':
                # Send WhatsApp for closed ticket
                notify_ticket_closed_whatsapp(instance)
        
        # Clean up temporary attributes
        if hasattr(instance, '_old_status'):
            delattr(instance, '_old_status')
        if hasattr(instance, '_old_assigned_to'):
            delattr(instance, '_old_assigned_to')
