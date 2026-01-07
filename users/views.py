from rest_framework import viewsets, status, filters, serializers
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import User
from .serializers import UserSerializer
from adminpanel.permissions import IsAdmin

@extend_schema_view(
    list=extend_schema(summary="List all users", tags=["Users"]),
    create=extend_schema(summary="Create a new user", tags=["Users"]),
    retrieve=extend_schema(summary="Get user details", tags=["Users"]),
    update=extend_schema(summary="Update a user", tags=["Users"]),
    partial_update=extend_schema(summary="Partial update a user", tags=["Users"]),
    destroy=extend_schema(summary="Delete a user", tags=["Users"]),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    Manage Users. Only accessible by Admins.
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department', 'role']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def destroy(self, request, *args, **kwargs):
        user_to_delete = self.get_object()
        
        # Prevent deleting self
        if user_to_delete == request.user:
            return Response(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Prevent deleting last admin
        if user_to_delete.role and user_to_delete.role.name.lower() == 'admin':
            admin_role_count = User.objects.filter(role__name__iexact='admin', is_active=True).count()
            if admin_role_count <= 1:
                return Response(
                    {"error": "Cannot delete the last admin user."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # Set created_by to current user
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        # Prevent admin self-role downgrade
        # If I am modifying myself, and I try to change my role to something else
        instance = serializer.instance
        if instance == self.request.user:
            # Check if role is present in validated data
            # validated_data is not directly available in perform_update args easily, 
            # usually serializer.validated_data but only after is_valid()
             new_role = serializer.validated_data.get('role')
             if new_role and new_role.name.lower() != 'admin':
                  # Wait, is the current user an admin? Yes due to IsAdmin permission.
                  # If they change to non-admin, they lock themselves out.
                  # Requirement: "Prevent admin self-role downgrade"
                  raise serializers.ValidationError("You cannot remove your own admin role.")
        
        serializer.save()
