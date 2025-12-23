from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class LoginSerializer(serializers.Serializer):
    """Serializer for user login - returns JWT tokens"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            # Authenticate user
            user = authenticate(username=username, password=password)
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                
                # Check if user has a profile
                if not hasattr(user, 'profile'):
                    raise serializers.ValidationError('User profile not found. Please contact administrator.')
                
                data['user'] = user
            else:
                raise serializers.ValidationError('Unable to log in with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')
        
        return data


class UserDetailSerializer(serializers.ModelSerializer):
    """Serializer for authenticated user details"""
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'}, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    role = serializers.CharField(source='profile.role', read_only=True)
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    whatsapp_number = serializers.CharField(source='profile.whatsapp_number', read_only=True)
    department = serializers.CharField(source='profile.department', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'phone_number', 'whatsapp_number', 'department',
            'is_active', 'date_joined', 'password', 'password_confirm'
        ]
        read_only_fields = ['id', 'username', 'email', 'is_active', 'date_joined']
    
    def validate(self, data):
        """Validate password match if password is being updated"""
        if 'password' in data:
            password_confirm = data.pop('password_confirm', None)
            if not password_confirm:
                raise serializers.ValidationError({"password_confirm": "Password confirmation is required when changing password."})
            if data['password'] != password_confirm:
                raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        elif 'password_confirm' in data:
            data.pop('password_confirm')
        return data
    
    def update(self, instance, validated_data):
        """Update user with optional password change"""
        password = validated_data.pop('password', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
