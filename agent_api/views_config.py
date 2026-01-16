from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.utils import timezone
from .models import Agent
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample
from .views import AgentBaseView # Reusing helper to get agent
from .serializers import DailyConfigSerializer, MonthlyConfigSerializer



class DailyConfigView(AgentBaseView):
    """
    Get or Set Daily Monitoring Configuration.
    """
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
        
        # Return specific daily config or default if not set
        # Return specific daily config or empty
        return Response(agent.daily_config or {})

    @extend_schema(
        request=DailyConfigSerializer,
        responses={200: None}
    )
    def post(self, request):
        agents = self.get_agents(request)
        if not agents:
            return Response({"error": "Unauthorized or No Agents Found"}, status=status.HTTP_404_NOT_FOUND)

        # Metadata is at root (handled by get_agents), config is in 'data' dictionary
        new_config = request.data.get('data', {}).copy()
        
        # Handle 'days' from root level overrides
        if 'days' in request.data:
            try:
                days = int(request.data['days'])
                new_config['capture_interval_seconds'] = days * 86400
            except (ValueError, TypeError):
                pass 

        # Merge or overwrite daily config
        for agent in agents:
            agent.daily_config = new_config
            agent.save()

        return Response({"status": "updated", "config": new_config, "count": len(agents)})

    @extend_schema(
        request=DailyConfigSerializer,
        responses={200: None}
    )
    def patch(self, request):
        agents = self.get_agents(request)
        if not agents:
            return Response({"error": "Unauthorized or No Agents Found"}, status=status.HTTP_404_NOT_FOUND)

        updates = request.data.copy()
        
        # Handle 'days' conversion
        if 'days' in updates:
            try:
                days = int(updates.pop('days'))
                updates['capture_interval_seconds'] = days * 86400
            except (ValueError, TypeError):
                pass

        final_config = {}
        for agent in agents:
            # Deep merge or shallow merge?
            # User asked to update "anyof the value". 
            # For a JSONField, standard approach is:
            current_config = agent.daily_config or {}
            current_config.update(updates) # Shallow merge of top-level keys
            
            agent.daily_config = current_config
            agent.save()
            final_config = current_config # Just return last one for ref

        return Response({"status": "updated", "config": final_config, "count": len(agents)})


class MonthlyConfigView(AgentBaseView):
    """
    Get or Set Monthly Monitoring Configuration.
    """
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
        
        return Response(agent.monthly_config or {})

    @extend_schema(
        request=MonthlyConfigSerializer,
        responses={200: None}
    )
    def post(self, request):
        agents = self.get_agents(request)
        if not agents:
            return Response({"error": "Unauthorized or No Agents Found"}, status=status.HTTP_404_NOT_FOUND)

        new_config = request.data.get('data', {}).copy()
        
        if 'days' in request.data:
            try:
                days = int(request.data['days'])
                new_config['capture_interval_seconds'] = days * 86400
            except (ValueError, TypeError):
                pass

        for agent in agents:
            agent.monthly_config = new_config
            agent.save()

        return Response({"status": "updated", "config": new_config, "count": len(agents)})

    @extend_schema(
        request=MonthlyConfigSerializer,
        responses={200: None}
    )
    def patch(self, request):
        agents = self.get_agents(request)
        if not agents:
            return Response({"error": "Unauthorized or No Agents Found"}, status=status.HTTP_404_NOT_FOUND)

        updates = request.data.get('data', {}).copy()
        
        if 'days' in request.data:
            try:
                days = int(request.data['days'])
                updates['capture_interval_seconds'] = days * 86400
            except (ValueError, TypeError):
                pass

        final_config = {}
        for agent in agents:
            current_config = agent.monthly_config or {}
            current_config.update(updates)
            
            agent.monthly_config = current_config
            agent.save()
            final_config = current_config

        return Response({"status": "updated", "config": final_config, "count": len(agents)})
