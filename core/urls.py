from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, TicketViewSet, UserProfileViewSet, NotificationLogViewSet, UserManagementViewSet, UpdateOwnProfileView

# Create router for ViewSets
router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'notifications', NotificationLogViewSet, basename='notification')
router.register(r'users', UserManagementViewSet, basename='user')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile update endpoint
    path('profile/update/', UpdateOwnProfileView.as_view(), name='update-own-profile'),
    
    # API endpoints
    path('', include(router.urls)),
]