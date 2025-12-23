from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Ticket, TicketAttachment, TicketHistory, NotificationLog



class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    max_num = 1
    min_num = 1
    
    def get_or_create_profile(self, user):
        """Ensure profile exists"""
        profile, created = UserProfile.objects.get_or_create(user=user, defaults={'role': 'CLIENT'})
        return profile


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile inline"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'profile__role')
    
    # Add email to the add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    # Add email to the change form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    def get_role(self, obj):
        return obj.profile.role if hasattr(obj, 'profile') else 'N/A'
    get_role.short_description = 'Role'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# ProjectAdmin removed - Project model is commented out


class TicketAttachmentInline(admin.TabularInline):
    """Inline admin for TicketAttachment"""
    model = TicketAttachment
    extra = 0
    readonly_fields = ('uploaded_by', 'uploaded_at')
    exclude = ('file_data',)  # Exclude BinaryField from admin - use API for uploads


class TicketHistoryInline(admin.TabularInline):
    """Inline admin for TicketHistory"""
    model = TicketHistory
    extra = 0
    readonly_fields = ('changed_by', 'status_from', 'status_to', 'timestamp')
    fields = ('changed_by', 'status_from', 'status_to', 'comment', 'timestamp')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """Admin for Ticket model"""
    list_display = ('id', 'title', 'project_name', 'priority', 'category', 'status', 'created_by', 'get_assigned_developers', 'response_breached', 'resolution_breached', 'created_at')
    list_filter = ('status', 'priority', 'category', 'response_breached', 'resolution_breached', 'created_at')
    search_fields = ('title', 'description', 'project_name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'opened_at', 'started_at', 'resolved_at', 'closed_at', 'response_breached', 'resolution_breached')
    inlines = [TicketAttachmentInline, TicketHistoryInline]
    filter_horizontal = ('assigned_to',)  # Nice widget for ManyToMany
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_name', 'title', 'description', 'priority', 'category', 'status')
        }),
        ('Assignment', {
            'fields': ('created_by', 'assigned_to', 'assigned_team')
        }),
        ('SLA (Service Level Agreement)', {
            'fields': ('response_due_at', 'response_breached', 'resolution_due_at', 'resolution_breached', 'estimated_resolution_time'),
            'description': 'Response SLA is auto-calculated based on priority (High: 30min, Medium: 2hrs, Low: 24hrs) but can be manually adjusted. Set resolution_due_at after reviewing the ticket.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'opened_at', 'started_at', 'resolved_at', 'closed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_assigned_developers(self, obj):
        """Display all assigned developers"""
        return ", ".join([dev.get_full_name() or dev.username for dev in obj.assigned_to.all()]) or "Unassigned"
    get_assigned_developers.short_description = "Assigned To"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by', 'assigned_to')


@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    """Admin for TicketAttachment model"""
    list_display = ('ticket', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('ticket__title',)
    readonly_fields = ('uploaded_at',)


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    """Admin for TicketHistory model"""
    list_display = ('ticket', 'changed_by', 'status_from', 'status_to', 'timestamp')
    list_filter = ('status_from', 'status_to', 'timestamp')
    search_fields = ('ticket__title', 'changed_by__username', 'comment')
    readonly_fields = ('ticket', 'changed_by', 'status_from', 'status_to', 'timestamp')


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    """Admin for NotificationLog model"""
    list_display = ('subject', 'recipient', 'notification_type', 'status', 'sent_at', 'created_at')
    list_filter = ('notification_type', 'status', 'created_at')
    search_fields = ('subject', 'recipient__username', 'message')
    readonly_fields = ('sent_at', 'created_at')
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('ticket', 'recipient', 'notification_type', 'subject', 'message')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'sent_at', 'created_at')
        }),
    )
