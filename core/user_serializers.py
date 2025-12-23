from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UpdateOwnProfileSerializer(serializers.ModelSerializer):
    """Serializer for users to update their own profile (first_name, last_name, password)"""
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'}, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, data):
        """Validate password match if password is being updated"""
        password = data.get('password')
        password_confirm = data.pop('password_confirm', None)
        
        if password and password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        return data
    
    def update(self, instance, validated_data):
        """Update user instance"""
        password = validated_data.pop('password', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (Admin only)"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    # Profile fields
    role = serializers.ChoiceField(choices=['CLIENT', 'SUPPORT', 'ADMIN'], required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'role', 'phone_number', 'whatsapp_number', 'department'
        ]
    
    def validate(self, data):
        """Validate password match and username uniqueness"""
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Username already exists."})
        
        if data.get('email') and User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        return data
    
    def create(self, validated_data):
        """Create user and profile"""
        # Extract profile data
        role = validated_data.pop('role')
        phone_number = validated_data.pop('phone_number', '')
        whatsapp_number = validated_data.pop('whatsapp_number', '')
        department = validated_data.pop('department', '')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Create profile
        UserProfile.objects.create(
            user=user,
            role=role,
            phone_number=phone_number,
            whatsapp_number=whatsapp_number,
            department=department
        )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users (Admin only)"""
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'}, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})
    
    # Profile fields
    role = serializers.CharField(source='profile.role', required=False)
    phone_number = serializers.CharField(source='profile.phone_number', required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(source='profile.whatsapp_number', required=False, allow_blank=True)
    department = serializers.CharField(source='profile.department', required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'is_active',
            'password', 'password_confirm',
            'role', 'phone_number', 'whatsapp_number', 'department'
        ]
        read_only_fields = ['id', 'username']  # Username cannot be changed
    
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
        """Update user and profile"""
        # Extract profile data if present
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        
        # Update profile fields
        if hasattr(instance, 'profile'):
            for attr, value in profile_data.items():
                setattr(instance.profile, attr, value)
            instance.profile.save()
        
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (Admin only)"""
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
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
