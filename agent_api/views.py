from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from .models import Agent, TelemetryLog
from .serializers import AgentEnrollmentSerializer, TelemetrySerializer, HeartbeatSerializer
from users.models import User
import logging
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from datetime import datetime

logger = logging.getLogger(__name__)



class EnrollAgentView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(request=AgentEnrollmentSerializer, responses={200: None})
    def post(self, request):
        serializer = AgentEnrollmentSerializer(data=request.data)
        if serializer.is_valid():
            secret_key = serializer.validated_data['secret_key']
            system_id = serializer.validated_data['system_id']
            hostname = serializer.validated_data.get('hostname', '')
            os_info = serializer.validated_data.get('os_info', '')
            
            # Validate against User.agent_code
            user = User.objects.filter(agent_code=secret_key).first()
            if not user:
                # Fallback: check if it matches a global admin secret
                if secret_key == getattr(settings, 'AGENT_GLOBAL_SECRET', 'SKUA_ADMIN_SECRET'):
                     # TODO: Assign to admin or handle properly. For now, fail if not specific user code
                     return Response({"error": "Invalid enrollment key"}, status=status.HTTP_403_FORBIDDEN)
                else:
                     return Response({"error": "Invalid enrollment key"}, status=status.HTTP_403_FORBIDDEN)

            agent, created = Agent.objects.update_or_create(
                system_id=system_id,
                defaults={
                    'user': user,
                    'hostname': hostname,
                    'os_info': os_info,
                    'is_active': True,
                    'last_seen': timezone.now()
                }
            )
            
            # If created or (optional) even if existing, ensure defaults are set if missing.
            # We only strictly asked to populate defaults, let's do it on creation or if empty.
            # If created or (optional) even if existing, ensure defaults are set if missing.
            # We only strictly asked to populate defaults, let's do it on creation or if empty.
            if created:
                agent.save()
            
            return Response({
                "success": True,
                "user_id": user.id,
                "agent_id": agent.id,
                "message": "Enrolled successfully"
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AgentBaseView(views.APIView):
    """Base view that validates Agent via user_id/system_id params"""
    permission_classes = [permissions.AllowAny] # We use custom param auth

    def get_agent(self, request):
        """Returns specific agent or None"""
        if request.method in ['POST', 'PUT', 'PATCH']:
            system_id = request.data.get('system_id')
            user_id = request.data.get('user_id')
        else:
            system_id = request.query_params.get('system_id')
            user_id = request.query_params.get('user_id')
        
        if not system_id or not user_id:
            return None
        
        try:
            return Agent.objects.get(system_id=system_id, user__id=user_id, is_active=True)
        except Agent.DoesNotExist:
            return None

    def get_agents(self, request):
        """Returns list of agents based on params. Handles bulk user update if system_id missing."""
        if request.method in ['POST', 'PUT', 'PATCH']:
            system_id = request.data.get('system_id')
            user_id = request.data.get('user_id')
        else:
            system_id = request.query_params.get('system_id')
            user_id = request.query_params.get('user_id')

        if not user_id:
            return []

        if system_id:
            try:
                agent = Agent.objects.get(system_id=system_id, user__id=user_id, is_active=True)
                return [agent]
            except Agent.DoesNotExist:
                return []
        else:
            # Bulk update for user
            return list(Agent.objects.filter(user__id=user_id, is_active=True))

# TelemetryView removed as per request

class HeartbeatView(AgentBaseView):
    @extend_schema(request=HeartbeatSerializer, responses={200: None})
    def post(self, request):
        agent = self.get_agent(request)
        if not agent:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        agent.last_seen = timezone.now()
        agent.save()
        return Response({"status": "ok"})
