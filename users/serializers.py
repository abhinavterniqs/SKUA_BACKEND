from rest_framework import serializers
from .models import User
from adminpanel.serializers import RoleSerializer, DepartmentSerializer

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'username', 'email', 
            'password', 'mobile', 'profile_pic', 'department', 'role', 
            'is_active', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        password = validated_data.pop('password')
        
        # Handle created_by automatically in ViewSet preferably, but can fallback here if context has request
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def to_representation(self, instance):
        # Optional: Nested representation for Role/Department if needed for "Get All Users"
        # Requirements didn't specify strict nested structure for GET, but it's usually helpful.
        # Leaving as ID for now to match input structure, but could expand.
        ret = super().to_representation(instance)
        return ret
