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
        if request.method in ['POST', 'PUT', 'PATCH']:
            system_id = request.data.get('system_id')
            user_id = request.data.get('user_id')
        else:
            system_id = request.query_params.get('system_id')
            user_id = request.query_params.get('user_id')
        
        if not system_id or not user_id:
            return None
        
        try:
            agent = Agent.objects.get(system_id=system_id, user__id=user_id, is_active=True)
            return agent
        except Agent.DoesNotExist:
            return None

class ConfigView(AgentBaseView):
    @extend_schema(
        parameters=[
            OpenApiParameter("user_id", OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter("system_id", OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=True),
        ],
        responses={200: OpenApiTypes.OBJECT}
    )
    def get(self, request):
        agent = self.get_agent(request)
        if not agent:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(agent.config_override)

class TelemetryView(AgentBaseView):
    @extend_schema(request=TelemetrySerializer, responses={201: None})
    def post(self, request):
        agent = self.get_agent(request)
        if not agent:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        
        raw_data = request.data
        if 'data' not in raw_data:
             return Response({"error": "Missing telemetry data"}, status=status.HTTP_400_BAD_REQUEST)

        # Update last seen
        agent.last_seen = timezone.now()
        agent.save()

        # Create Log
        ts_val = raw_data.get('timestamp')
        if ts_val:
            ts = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
        else:
            ts = timezone.now()

        TelemetryLog.objects.create(
            agent=agent,
            timestamp=ts,
            data=raw_data.get('data')
        )
        
        return Response({"status": "received"}, status=status.HTTP_201_CREATED)

class HeartbeatView(AgentBaseView):
    @extend_schema(request=HeartbeatSerializer, responses={200: None})
    def post(self, request):
        agent = self.get_agent(request)
        if not agent:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
        agent.last_seen = timezone.now()
        agent.save()
        return Response({"status": "ok"})
