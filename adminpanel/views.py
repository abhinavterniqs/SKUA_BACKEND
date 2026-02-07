from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Role, Department
from .permissions import IsAdmin
from agent_api.models import Agent
from agent_api.models_activity import DailyActivity, MonthlyActivity
from .serializers import (
    RoleSerializer, DepartmentSerializer, CustomTokenObtainPairSerializer,
    AgentSerializer, AgentDetailSerializer
)

@extend_schema_view(
    post=extend_schema(summary="Admin Login", tags=["Auth"]),
)
class AdminLoginView(TokenObtainPairView):
    """
    Login endpoint for Admins.
    Returns JWT access token and user details.
    """
    serializer_class = CustomTokenObtainPairSerializer

@extend_schema_view(
    list=extend_schema(summary="List all roles", tags=["Roles"]),
    create=extend_schema(summary="Create a new role", tags=["Roles"]),
    retrieve=extend_schema(summary="Get role details", tags=["Roles"]),
    update=extend_schema(summary="Update a role", tags=["Roles"]),
    partial_update=extend_schema(summary="Partial update a role", tags=["Roles"]),
    destroy=extend_schema(summary="Delete a role", tags=["Roles"]),
)
class RoleViewSet(viewsets.ModelViewSet):
    """
    Manage Roles. Only accessible by Admins.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdmin]
    pagination_class = None # Or default? Config default is PageNumberPagination.
    
    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        # Prevent if users assigned
        if role.users.exists(): # 'users' related_name
            return Response(
                {"error": "Cannot delete role because it is assigned to users."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Prevent "admin" and "user" role deletion? 
        if role.name.lower() in ['admin', 'user']:
             return Response(
                {"error": "Cannot delete default system roles."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

@extend_schema_view(
    list=extend_schema(summary="List all departments", tags=["Departments"]),
    create=extend_schema(summary="Create a new department", tags=["Departments"]),
    retrieve=extend_schema(summary="Get department details", tags=["Departments"]),
    update=extend_schema(summary="Update a department", tags=["Departments"]),
    partial_update=extend_schema(summary="Partial update a department", tags=["Departments"]),
    destroy=extend_schema(summary="Delete a department", tags=["Departments"]),
)
class DepartmentViewSet(viewsets.ModelViewSet):
    """
    Manage Departments. Only accessible by Admins.
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdmin]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def destroy(self, request, *args, **kwargs):
        department = self.get_object()
        # Prevent deletion if users are assigned
        if department.users.exists(): # 'users' related_name
             return Response(
                {"error": "Cannot delete department because it has users assigned."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

@extend_schema_view(
    list=extend_schema(summary="List all agents", tags=["Agents"]),
    retrieve=extend_schema(summary="Get agent details inc. activities", tags=["Agents"]),
)
class AgentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly viewset for Agents.
    'list' returns summary.
    'retrieve' returns full details including nested activities.
    """
    queryset = Agent.objects.all().select_related('user', 'user__role', 'user__department')
    serializer_class = AgentSerializer
    permission_classes = [IsAdmin] 
    filter_backends = [filters.SearchFilter]
    search_fields = ['system_id', 'hostname', 'user__username', 'user__email']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AgentDetailSerializer
        return AgentSerializer
