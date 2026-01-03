from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role, Department
from users.models import User

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom user data to response
        user = self.user
        
        # Helper to safely get profile pic url
        profile_pic_url = None
        if user.profile_pic:
            request = self.context.get('request')
            if request:
                profile_pic_url = request.build_absolute_uri(user.profile_pic.url)
            else:
                 profile_pic_url = user.profile_pic.url

        user_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "mobile": user.mobile,
            "role": user.role.name if user.role else None,
            "is_active": user.is_active,
            "profile_pic_url": profile_pic_url
        }
        
        data['user'] = user_data
        
        # Requirement says response: { "access": ..., "user": ... }
        # Default `data` has 'refresh' and 'access'. 
        # Requirement ONLY asks for "access" in example. But standard is usually both.
        # User output requirement: "Response { access: JWT, user: ... }"
        # I will keep refresh if standard, but structure it.
        # However, to STRICTLY match requirement example:
        # {
        #   "access": "JWT_TOKEN",
        #   "user": { ... }
        # }
        # We might want to remove refresh or keep it. I'll keep it for utility unless strictly forbidden.
        # The prompt says: "Refresh token support ready". So we should return it?
        # Maybe typically /api/token/refresh/ is used to get new access.
        # The LOGIN response example ONLY shows "access". I will follow the example strictly for the main keys.
        
        return {
            "access": data['access'],
            "refresh": data['refresh'], # Included for "Refresh token support ready" implicit need to have it initially.
            "user": user_data
        }
