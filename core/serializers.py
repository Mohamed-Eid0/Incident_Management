from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Ticket, TicketAttachment, TicketHistory, NotificationLog



class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with profile information"""
    role = serializers.CharField(source='profile.role', read_only=True)
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    whatsapp_number = serializers.CharField(source='profile.whatsapp_number', read_only=True)
    department = serializers.CharField(source='profile.department', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'whatsapp_number', 'department']
        read_only_fields = ['id', 'username', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'whatsapp_number', 'department', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# ProjectSerializer removed - Project model is commented out
# class ProjectSerializer(serializers.ModelSerializer):
#     """Serializer for Project model"""
#     client_name = serializers.CharField(source='client.get_full_name', read_only=True)
#     client_email = serializers.EmailField(source='client.email', read_only=True)
#     ticket_count = serializers.SerializerMethodField()
#     
#     class Meta:
#         model = Project
#         fields = ['id', 'name', 'description', 'client', 'client_name', 'client_email', 'is_active', 'ticket_count', 'created_at', 'updated_at']
#         read_only_fields = ['id', 'created_at', 'updated_at']
#     
#     def get_ticket_count(self, obj):
#         return obj.tickets.count()


class TicketAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for TicketAttachment model with base64 encoded file data"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_data = serializers.SerializerMethodField()
    
    class Meta:
        model = TicketAttachment
        fields = ['id', 'ticket', 'file_data', 'uploaded_by', 'uploaded_by_name', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
    
    def get_file_data(self, obj):
        """Return file data as base64 encoded string"""
        import base64
        if obj.file_data:
            return base64.b64encode(obj.file_data).decode('utf-8')
        return None


class TicketHistorySerializer(serializers.ModelSerializer):
    """Serializer for TicketHistory model"""
    changed_by_name = serializers.SerializerMethodField()
    status_from_display = serializers.CharField(source='get_status_from_display', read_only=True)
    status_to_display = serializers.CharField(source='get_status_to_display', read_only=True)
    
    class Meta:
        model = TicketHistory
        fields = ['id', 'ticket', 'changed_by', 'changed_by_name', 'status_from', 'status_from_display', 'status_to', 'status_to_display', 'comment', 'timestamp']
        read_only_fields = ['id', 'timestamp']
    
    def get_changed_by_name(self, obj):
        """Get full name or username as fallback"""
        if obj.changed_by:
            full_name = obj.changed_by.get_full_name()
            return full_name if full_name else obj.changed_by.username
        return "System"


class TicketSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for Ticket model"""
    # Read-only display fields
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_names = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Nested relationships
    attachments = TicketAttachmentSerializer(many=True, read_only=True)
    history = TicketHistorySerializer(many=True, read_only=True)
    
    # SLA computed fields
    response_sla_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'project_name', 'title', 'description',
            'priority', 'priority_display', 'category', 'category_display',
            'status', 'status_display',
            'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_names', 'assigned_team',
            'response_due_at', 'resolution_due_at', 'response_breached', 'resolution_breached',
            'response_sla_minutes', 'estimated_resolution_time',
            'created_at', 'updated_at', 'opened_at', 'started_at', 'resolved_at', 'closed_at',
            'attachments', 'history'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'opened_at', 'started_at', 
                           'resolved_at', 'closed_at', 'response_breached', 
                           'resolution_breached', 'status', 'assigned_to']
    
    def get_assigned_to_names(self, obj):
        """Get names of all assigned developers"""
        return [user.get_full_name() or user.username for user in obj.assigned_to.all()]
    
    def get_response_sla_minutes(self, obj):
        """Get the response SLA in minutes for this ticket"""
        return obj.get_response_sla_minutes()
    
    def validate_status(self, value):
        """Validate status transitions"""
        if self.instance:
            current_status = self.instance.status
            valid_transitions = {
                'NEW': ['OPENED'],
                'OPENED': ['IN_PROGRESS'],
                'IN_PROGRESS': ['RESOLVED'],
                'RESOLVED': ['WAITING_APPROVAL'],
                'WAITING_APPROVAL': ['CLOSED', 'IN_PROGRESS'],  # Can reopen if client rejects
                'CLOSED': [],  # Cannot change from closed
            }
            
            if current_status in valid_transitions and value not in valid_transitions[current_status]:
                raise serializers.ValidationError(
                    f"Invalid status transition from {current_status} to {value}"
                )
        
        return value


class TicketListSerializer(serializers.ModelSerializer):
    """Minimal serializer for ticket lists - excludes attachments and history for performance"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_names = serializers.SerializerMethodField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'project_name', 'title', 'description',
            'priority', 'priority_display', 'category', 'category_display',
            'status', 'status_display',
            'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_names', 'assigned_team'
        ]
    
    def get_assigned_to_names(self, obj):
        """Get names of all assigned developers"""
        return [user.get_full_name() or user.username for user in obj.assigned_to.all()]


class TicketAdminSerializer(TicketSerializer):
    """Admin-specific serializer with full SLA editing permissions"""
    
    class Meta(TicketSerializer.Meta):
        # Admins can edit SLA fields that are read-only for clients
        # But status and assigned_to should ONLY be changed via action endpoints
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'opened_at', 'started_at', 
                           'resolved_at', 'closed_at', 'response_breached', 
                           'resolution_breached', 'status', 'assigned_to']
        # response_due_at, resolution_due_at, estimated_resolution_time are now editable


class NotificationLogSerializer(serializers.ModelSerializer):
    """Minimal serializer for NotificationLog model - returns only essential data for security and performance"""
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id', 'ticket',  # Just IDs, no detailed data
            'notification_type', 'notification_type_display',
            'subject',  # Just the subject like "New Ticket Created"
            'created_at',
            'is_read', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_read', 'read_at']
