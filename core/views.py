from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .models import Ticket, TicketHistory, UserProfile, NotificationLog
from .serializers import (
    TicketSerializer, TicketAdminSerializer,
    UserSerializer, UserProfileSerializer,
    NotificationLogSerializer
)
from .auth_serializers import LoginSerializer, UserDetailSerializer
from .user_serializers import UserCreateSerializer, UserUpdateSerializer, UserListSerializer, UpdateOwnProfileSerializer
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
        """Admin action to assign ticket to support user(s)"""
        ticket = self.get_object()
        assigned_to_ids = request.data.get('assigned_to')
        resolution_due_at = request.data.get('resolution_due_at')
        estimated_resolution_time = request.data.get('estimated_resolution_time')
        
        if not assigned_to_ids:
            return Response({'error': 'assigned_to is required (array of user IDs)'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure it's a list
        if not isinstance(assigned_to_ids, list):
            assigned_to_ids = [assigned_to_ids]
        
        try:
            # Get all support users with provided IDs
            support_users = User.objects.filter(id__in=assigned_to_ids, profile__role='SUPPORT')
            
            if not support_users.exists():
                return Response({'error': 'No valid support users found'}, status=status.HTTP_404_NOT_FOUND)
            
            if support_users.count() != len(assigned_to_ids):
                return Response({'error': 'Some user IDs are invalid or not support users'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update SLA fields if provided
            if resolution_due_at:
                from django.utils.dateparse import parse_datetime
                ticket.resolution_due_at = parse_datetime(resolution_due_at)
            if estimated_resolution_time:
                from django.utils.dateparse import parse_datetime
                ticket.estimated_resolution_time = parse_datetime(estimated_resolution_time)
            
            ticket.save()
            
            # Set assigned developers (ManyToMany)
            ticket.assigned_to.set(support_users)
            
            # Create history entry
            dev_names = ', '.join([u.get_full_name() or u.username for u in support_users])
            TicketHistory.objects.create(
                ticket=ticket,
                changed_by=request.user,
                status_from=ticket.status,
                status_to=ticket.status,
                comment=f'Ticket assigned to {dev_names}'
            )
            
            # Send email to developer(s)
            notify_developer_assignment(ticket, list(support_users))
            
            # Send WebSocket notification to developer(s)
            from .notification_service import notify_developers_assignment_ws
            notify_developers_assignment_ws(ticket, list(support_users))
            
            return Response(self.get_serializer(ticket).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
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
        """Developer action to mark work as finished"""
        ticket = self.get_object()
        
        # Check if user is assigned to this ticket or is admin
        if not (hasattr(request.user, 'profile') and 
                (request.user.profile.role == 'ADMIN' or 
                 ticket.assigned_to.filter(id=request.user.id).exists())):
            return Response({'error': 'You are not assigned to this ticket'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status != 'IN_PROGRESS':
            return Response({'error': 'Ticket is not in progress'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'RESOLVED'
        ticket.save()
        
        # Create history entry
        comment = request.data.get('comment', 'Work completed')
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
        """Client action to reject work and request more changes"""
        ticket = self.get_object()
        
        # Only ticket creator can reject
        if ticket.created_by != request.user:
            return Response({'error': 'Only ticket creator can reject'}, status=status.HTTP_403_FORBIDDEN)
        
        if ticket.status not in ['RESOLVED', 'WAITING_APPROVAL']:
            return Response({'error': 'Ticket is not awaiting approval'}, status=status.HTTP_400_BAD_REQUEST)
        
        ticket.status = 'IN_PROGRESS'
        ticket.save()
        
        # Create history entry
        rejection_reason = request.data.get('comment', 'Client rejected the resolution')
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
        """Add a comment/history entry to the ticket"""
        ticket = self.get_object()
        comment = request.data.get('comment', '')
        
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


class NotificationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing notification logs"""
    serializer_class = NotificationLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users see their own notifications, admins see all"""
        if hasattr(self.request.user, 'profile') and self.request.user.profile.role == 'ADMIN':
            return NotificationLog.objects.all().select_related('recipient', 'ticket')
        return NotificationLog.objects.filter(recipient=self.request.user).select_related('recipient', 'ticket')
