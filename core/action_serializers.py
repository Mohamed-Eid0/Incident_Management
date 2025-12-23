"""
Action Serializers for Ticket ViewSet Actions

These serializers provide input validation for ticket action endpoints:
- assign: Validate assignment and SLA fields
- start_work: Validate work start
- finish_work: Validate completion with comments
- approve: Validate approval
- reject: Validate rejection with reason
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta


class TicketAssignmentSerializer(serializers.Serializer):
    """
    Serializer for ticket assignment action
    Validates developer IDs and SLA datetime fields
    """
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
        max_length=20,
        help_text="List of developer user IDs to assign",
        error_messages={
            'min_length': 'At least one developer must be assigned',
            'max_length': 'Cannot assign more than 20 developers to one ticket'
        }
    )
    
    resolution_due_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Expected resolution deadline (ISO 8601 format)",
        error_messages={
            'invalid': 'Invalid datetime format. Use ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS'
        }
    )
    
    estimated_resolution_time = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text="Estimated completion time (ISO 8601 format)",
        error_messages={
            'invalid': 'Invalid datetime format. Use ISO 8601 format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS'
        }
    )
    
    def validate_assigned_to(self, value):
        """Ensure all IDs are unique"""
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate user IDs are not allowed")
        return value
    
    def validate_resolution_due_at(self, value):
        """Ensure resolution_due_at is in the future and reasonable"""
        if value is None:
            return value
        
        now = timezone.now()
        
        # Must be in the future
        if value <= now:
            raise serializers.ValidationError(
                "Resolution due date must be in the future"
            )
        
        # Reasonable limit: not more than 1 year in future
        max_future = now + timedelta(days=365)
        if value > max_future:
            raise serializers.ValidationError(
                "Resolution due date cannot be more than 1 year in the future"
            )
        
        # Reasonable minimum: at least 30 minutes from now
        min_future = now + timedelta(minutes=30)
        if value < min_future:
            raise serializers.ValidationError(
                "Resolution due date must be at least 30 minutes in the future"
            )
        
        return value
    
    def validate_estimated_resolution_time(self, value):
        """Validate estimated resolution time"""
        if value is None:
            return value
        
        now = timezone.now()
        
        # Must be in the future
        if value <= now:
            raise serializers.ValidationError(
                "Estimated resolution time must be in the future"
            )
        
        # Reasonable limit: not more than 1 year in future
        max_future = now + timedelta(days=365)
        if value > max_future:
            raise serializers.ValidationError(
                "Estimated time cannot be more than 1 year in the future"
            )
        
        # Reasonable minimum: at least 15 minutes from now
        min_future = now + timedelta(minutes=15)
        if value < min_future:
            raise serializers.ValidationError(
                "Estimated time must be at least 15 minutes in the future"
            )
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        resolution = data.get('resolution_due_at')
        estimated = data.get('estimated_resolution_time')
        
        # Estimated should be before or equal to resolution deadline
        if resolution and estimated and estimated > resolution:
            raise serializers.ValidationError({
                'estimated_resolution_time': 'Estimated resolution time should not be after the resolution due date'
            })
        
        return data


class TicketFinishWorkSerializer(serializers.Serializer):
    """
    Serializer for finish_work action
    Validates optional completion comment
    """
    comment = serializers.CharField(
        max_length=2000,
        required=False,
        allow_blank=True,
        default='Work completed',
        help_text="Optional comment about work completion"
    )
    
    def validate_comment(self, value):
        """Ensure comment is not too short if provided"""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Comment must be at least 5 characters if provided"
            )
        return value.strip() if value else 'Work completed'


class TicketRejectSerializer(serializers.Serializer):
    """
    Serializer for reject action
    Validates rejection reason (required)
    """
    comment = serializers.CharField(
        max_length=2000,
        required=True,
        allow_blank=False,
        help_text="Reason for rejection (required)"
    )
    
    def validate_comment(self, value):
        """Ensure rejection reason is meaningful"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Rejection reason must be at least 10 characters"
            )
        return value.strip()


class TicketCommentSerializer(serializers.Serializer):
    """
    Serializer for add_comment action
    Validates comment text
    """
    comment = serializers.CharField(
        max_length=2000,
        required=True,
        allow_blank=False,
        help_text="Comment text"
    )
    
    def validate_comment(self, value):
        """Ensure comment is meaningful"""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Comment must be at least 3 characters"
            )
        return value.strip()
