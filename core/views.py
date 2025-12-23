from rest_framework import viewsets, permissions, status, generics, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Ticket, TicketHistory, UserProfile, NotificationLog
from .serializers import (
    TicketSerializer, TicketAdminSerializer,
    UserSerializer, UserProfileSerializer,
    NotificationLogSerializer
)
from .auth_serializers import LoginSerializer, UserDetailSerializer
from .user_serializers import UserCreateSerializer, UserUpdateSerializer, UserListSerializer, UpdateOwnProfileSerializer
from .action_serializers import (
    TicketAssignmentSerializer, TicketFinishWorkSerializer,
    TicketRejectSerializer, TicketCommentSerializer
)
from .email_service import (
    notify_admin_new_ticket, notify_client_ticket_opened,
    notify_developer_assignment, notify_client_work_started,
    notify_client_work_finished, notify_admin_work_finished,
    notify_ticket_closed
)


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow admins full access, others read-only"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'


class LoginView(TokenObtainPairView):
    """Custom login view using JWT tokens"""
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserDetailSerializer(user).data
        })


class TicketViewSet(viewsets.ModelViewSet):
    """ViewSet for Ticket CRUD operations with role-based permissions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only admins can use standard update/delete
            return [IsAdminUser()]
        elif self.action == 'create':
            # Only clients can create tickets (or admins)
            return [permissions.IsAuthenticated()]
        else:
            # List, retrieve, custom actions use default permissions
            return [permissions.IsAuthenticated()]
    
    def update(self, request, *args, **kwargs):
        """Override to prevent status/assignment changes via direct update"""
        if 'status' in request.data:
            return Response(
                {'error': 'Status cannot be changed directly. Use action endpoints (open_ticket, start_work, finish_work, approve, reject).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if 'assigned_to' in request.data:
            return Response(
                {'error': 'Assignment cannot be changed directly. Use assign action endpoint.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Override to prevent status/assignment changes via direct update"""
        if 'status' in request.data:
            return Response(
                {'error': 'Status cannot be changed directly. Use action endpoints (open_ticket, start_work, finish_work, approve, reject).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if 'assigned_to' in request.data:
            return Response(
                {'error': 'Assignment cannot be changed directly. Use assign action endpoint.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().partial_update(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter tickets based on user role"""
        user = self.request.user
        
        if hasattr(user, 'profile'):
            if user.profile.role == 'ADMIN':
                # Admins see all tickets
                return Ticket.objects.all().select_related('created_by').prefetch_related('assigned_to', 'attachments', 'history')
            elif user.profile.role == 'SUPPORT':
                # Support sees tickets assigned to them
                return Ticket.objects.filter(assigned_to=user).select_related('created_by').prefetch_related('assigned_to', 'attachments', 'history')
            else:
                # Clients see only their own tickets
                return Ticket.objects.filter(created_by=user).select_related('created_by').prefetch_related('assigned_to', 'attachments', 'history')
        
        return Ticket.objects.none()
    
    def get_serializer_class(self):
        """Use different serializers for admins vs others"""
        if hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'ADMIN':
            return TicketAdminSerializer
        return TicketSerializer
    
    def perform_create(self, serializer):
        """Set the created_by field to the current user and send notification"""
        ticket = serializer.save(created_by=self.request.user)
        
        # Send email notification to admin
        notify_admin_new_ticket(ticket)
        
        # Send WhatsApp notification to admin
        from .whatsapp_service import notify_admin_new_ticket_whatsapp
        notify_admin_new_ticket_whatsapp(ticket)
        
        # Send WebSocket notification to admin
        from .notification_service import notify_admins_new_ticket
        notify_admins_new_ticket(ticket)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def open_ticket(self, request, pk=None):
        """Admin action to open a ticket (acknowledge receipt)"""
        ticket = self.get_object()
        
        if ticket.status != 'NEW':
            return Response({'error': 'Ticket is not in NEW status'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'OPENED'
        ticket.save()
        
        # Create history entry
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            status_from='NEW',
            status_to='OPENED',
            comment='Ticket opened by admin'
        )
        
        # Send email to client
        notify_client_ticket_opened(ticket)
        
        # Send WebSocket notification to client
        from .notification_service import notify_client_ticket_opened_ws
        notify_client_ticket_opened_ws(ticket)
        
        return Response(self.get_serializer(ticket).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def assign(self, request, pk=None):
        """Admin action to assign ticket to support user(s) with validation"""
        ticket = self.get_object()
        
        # Use serializer for input validation
        serializer = TicketAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Auto returns 400 with errors
        
        validated_data = serializer.validated_data
        assigned_to_ids = validated_data['assigned_to']
        
        # Get OLD assignment for comparison (to detect changes)
        old_assigned_ids = set(ticket.assigned_to.values_list('id', flat=True))
        
        # Get all support users with provided IDs
        support_users = User.objects.filter(id__in=assigned_to_ids, profile__role='SUPPORT')
        
        if support_users.count() != len(assigned_to_ids):
            return Response(
                {'error': 'Some user IDs are invalid or not support users'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update SLA fields (now validated by serializer)
        if 'resolution_due_at' in validated_data:
            ticket.resolution_due_at = validated_data['resolution_due_at']
        if 'estimated_resolution_time' in validated_data:
            ticket.estimated_resolution_time = validated_data['estimated_resolution_time']
        
        ticket.save()
        
        # Set assigned developers (ManyToMany)
        ticket.assigned_to.set(support_users)
        
        # Get NEW assignment for comparison
        new_assigned_ids = set(ticket.assigned_to.values_list('id', flat=True))
        
        # Create history entry
        dev_names = ', '.join([u.get_full_name() or u.username for u in support_users])
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            status_from=ticket.status,
            status_to=ticket.status,
            comment=f'Ticket assigned to {dev_names}'
        )
        
        # Only notify if assignment actually changed
        if old_assigned_ids != new_assigned_ids:
            # Get newly assigned developers (difference)
            newly_assigned_ids = new_assigned_ids - old_assigned_ids
            if newly_assigned_ids:
                newly_assigned = User.objects.filter(id__in=newly_assigned_ids)
                
                # Send Email notifications
                notify_developer_assignment(ticket, list(newly_assigned))
                
                # Send WhatsApp notifications
                from .whatsapp_service import notify_developer_assignment_whatsapp
                notify_developer_assignment_whatsapp(ticket, list(newly_assigned))
                
                # Send WebSocket notifications
                from .notification_service import notify_developers_assignment_ws
                notify_developers_assignment_ws(ticket, list(newly_assigned))
        
        return Response(self.get_serializer(ticket).data)
    
    @action(detail=True, methods=['post'])
    def start_work(self, request, pk=None):
        """Developer action to start working on ticket"""
        ticket = self.get_object()
        
        # Check if user is assigned to this ticket or is admin
        if not (hasattr(request.user, 'profile') and 
                (request.user.profile.role == 'ADMIN' or 
                 ticket.assigned_to.filter(id=request.user.id).exists())):
            return Response({'error': 'You are not assigned to this ticket'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status not in ['OPENED', 'IN_PROGRESS']:
            return Response({'error': 'Ticket cannot be started in current status'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = ticket.status
        ticket.status = 'IN_PROGRESS'
        ticket.save()
        
        # Create history entry
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            status_from=old_status,
            status_to='IN_PROGRESS',
            comment='Work started on ticket'
        )
        
        # Send email to client
        notify_client_work_started(ticket)
        
        # Send WebSocket notification to client
        from .notification_service import notify_client_work_started_ws
        notify_client_work_started_ws(ticket)
        
        return Response(self.get_serializer(ticket).data)
    
    @action(detail=True, methods=['post'])
    def finish_work(self, request, pk=None):
        """Developer action to mark work as finished with validation"""
        ticket = self.get_object()
        
        # Check if user is assigned to this ticket or is admin
        if not (hasattr(request.user, 'profile') and 
                (request.user.profile.role == 'ADMIN' or 
                 ticket.assigned_to.filter(id=request.user.id).exists())):
            return Response({'error': 'You are not assigned to this ticket'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status != 'IN_PROGRESS':
            return Response({'error': 'Ticket is not in progress'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate input
        serializer = TicketFinishWorkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comment = serializer.validated_data['comment']
        
        ticket.status = 'RESOLVED'
        ticket.save()
        
        # Create history entry
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            status_from='IN_PROGRESS',
            status_to='RESOLVED',
            comment=comment
        )
        
        # Send emails to client and admin
        notify_client_work_finished(ticket)
        notify_admin_work_finished(ticket)
        
        # Send WebSocket notification to client
        from .notification_service import notify_client_work_finished_ws
        notify_client_work_finished_ws(ticket)
        
        return Response(self.get_serializer(ticket).data)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Client action to approve completed work"""
        ticket = self.get_object()
        
        # Only ticket creator can approve
        if ticket.created_by != request.user:
            return Response({'error': 'Only ticket creator can approve'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status not in ['RESOLVED', 'WAITING_APPROVAL']:
            return Response({'error': 'Ticket is not awaiting approval'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'CLOSED'
        ticket.save()
        
        # Create history entry
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            status_from='RESOLVED',
            status_to='CLOSED',
            comment='Ticket approved and closed by client'
        )
        
        # Send notifications
        notify_ticket_closed(ticket)
        
        # Send WebSocket notification to admins and developers
        from .notification_service import notify_ticket_approved_ws
        notify_ticket_approved_ws(ticket)
        
        return Response(self.get_serializer(ticket).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Client action to reject work and request more changes with validation"""
        ticket = self.get_object()
        
        # Only ticket creator can reject
        if ticket.created_by != request.user:
            return Response({'error': 'Only ticket creator can reject'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status not in ['RESOLVED', 'WAITING_APPROVAL']:
            return Response({'error': 'Ticket is not awaiting approval'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate input - rejection reason is required
        serializer = TicketRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        rejection_reason = serializer.validated_data['comment']
        
        ticket.status = 'IN_PROGRESS'
        ticket.save()
        
        # Create history entry
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            status_from='RESOLVED',
            status_to='IN_PROGRESS',
            comment=f'Rejected: {rejection_reason}'
        )
        
        # Send WhatsApp notification to developer
        from .whatsapp_service import notify_ticket_rejected_whatsapp
        notify_ticket_rejected_whatsapp(ticket, rejection_reason)
        
        # Send WebSocket notification to admins and developers
        from .notification_service import notify_ticket_rejected_ws
        notify_ticket_rejected_ws(ticket, rejection_reason)
        
        return Response(self.get_serializer(ticket).data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def developers(self, request):
        """Get list of all developers for assignment"""
        developers = User.objects.filter(profile__role='SUPPORT').select_related('profile')
        serializer = UserSerializer(developers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """Add a comment/history entry to the ticket with validation"""
        ticket = self.get_object()
        
        # Validate input
        serializer = TicketCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        comment = serializer.validated_data['comment']
        
        TicketHistory.objects.create(
            ticket=ticket,
            changed_by=request.user,
            status_from=ticket.status,
            status_to=ticket.status,
            comment=comment
        )
        
        return Response({'message': 'Comment added successfully'})


class UpdateOwnProfileView(generics.UpdateAPIView):
    """View for users to update their own profile (first_name, last_name, password)"""
    serializer_class = UpdateOwnProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the authenticated user"""
        return self.request.user


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing user profiles"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Admins see all profiles, others see only their own"""
        if hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'ADMIN':
            return UserProfile.objects.all().select_related('user')
        return UserProfile.objects.filter(user=self.request.user)


class UserManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for user management (Admin only)"""
    permission_classes = [IsAdminUser]
    queryset = User.objects.all().select_related('profile')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        else:
            return UserListSerializer
    
    def get_queryset(self):
        """Return all users for admins"""
        return User.objects.all().select_related('profile').order_by('-date_joined')
    
    def create(self, request, *args, **kwargs):
        """Create new user with profile"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return created user data
        response_serializer = UserListSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': f'User {user.username} activated successfully'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user account"""
        user = self.get_object()
        
        # Prevent deactivating yourself
        if user == request.user:
            return Response({'error': 'You cannot deactivate your own account'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = False
        user.save()
        return Response({'message': f'User {user.username} deactivated successfully'})
    
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """Get users filtered by role"""
        role = request.query_params.get('role', None)
        
        if not role:
            return Response({'error': 'role parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if role not in ['CLIENT', 'SUPPORT', 'ADMIN']:
            return Response({'error': 'Invalid role. Must be CLIENT, SUPPORT, or ADMIN'}, status=status.HTTP_400_BAD_REQUEST)
        
        users = User.objects.filter(profile__role=role).select_related('profile')
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)


class NotificationLogViewSet(viewsets.GenericViewSet, 
                             mixins.ListModelMixin):
    """
    ViewSet for viewing and managing notification logs
    
    Provides endpoints for:
    - List all notifications (with filtering) - returns minimal data only
    - Get unread count
    - Mark individual notification as read
    - Mark all notifications as read
    
    Note: No detailed view endpoint - all endpoints return minimal data for security/performance
    """
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Users see their own notifications, admins see all
        Supports filtering by:
        - is_read: true/false
        - notification_type: EMAIL, WHATSAPP, SYSTEM
        - ticket: ticket ID
        """
        base_queryset = NotificationLog.objects.select_related('recipient', 'ticket')
        
        # Role-based filtering
        if hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'ADMIN':
            queryset = base_queryset.all()
        else:
            queryset = base_queryset.filter(recipient=self.request.user)
        
        # Filter by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read_bool = is_read.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_read=is_read_bool)
        
        # Filter by notification type
        notification_type = self.request.query_params.get('notification_type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type.upper())
        
        # Filter by ticket
        ticket_id = self.request.query_params.get('ticket', None)
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread notifications for current user
        
        Response:
        {
            "count": 5,
            "by_type": {
                "EMAIL": 2,
                "WHATSAPP": 1,
                "SYSTEM": 2
            }
        }
        """
        unread_notifications = NotificationLog.objects.filter(
            recipient=request.user,
            is_read=False
        )
        
        total_count = unread_notifications.count()
        
        # Count by type
        from django.db.models import Count
        by_type = dict(
            unread_notifications.values('notification_type')
            .annotate(count=Count('id'))
            .values_list('notification_type', 'count')
        )
        
        return Response({
            'count': total_count,
            'by_type': by_type
        })
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """
        Mark a single notification as read
        
        Returns the updated notification
        """
        notification = self.get_object()
        
        # Ensure user owns this notification (non-admins)
        if notification.recipient != request.user:
            if not (hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN'):
                return Response(
                    {'error': 'You can only mark your own notifications as read'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        notification.mark_as_read()
        
        serializer = self.get_serializer(notification)
        return Response({
            'message': 'Notification marked as read',
            'notification': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """
        Mark all notifications as read for current user
        
        Optional query parameters:
        - notification_type: Only mark specific type as read (EMAIL, WHATSAPP, SYSTEM)
        - ticket: Only mark notifications for specific ticket as read
        
        Returns count of notifications marked as read
        """
        queryset = NotificationLog.objects.filter(
            recipient=request.user,
            is_read=False
        )
        
        # Optional filtering
        notification_type = request.query_params.get('notification_type', None)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type.upper())
        
        ticket_id = request.query_params.get('ticket', None)
        if ticket_id:
            queryset = queryset.filter(ticket_id=ticket_id)
        
        # Update all matching notifications
        now = timezone.now()
        count = queryset.update(is_read=True, read_at=now)
        
        return Response({
            'message': f'{count} notification(s) marked as read',
            'count': count
        })
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """
        Get all unread notifications for current user
        
        This is equivalent to ?is_read=false but with a cleaner endpoint
        Returns paginated list of unread notifications
        """
        queryset = self.get_queryset().filter(is_read=False)
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

