from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.utils import timezone
from .models import Agent
from .models_activity import DailyActivity, MonthlyActivity
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from .views import AgentBaseView
from datetime import datetime
from .serializers import TelemetryUploadSerializer

class DailyTelemetryView(AgentBaseView):
    """
    Receives Daily Telemetry Data.
    Updates a single DailyActivity row per day for the agent.
    """
    @extend_schema(request=TelemetryUploadSerializer, responses={201: None})
    def post(self, request):
        try:
            agent = self.get_agent(request)
            if not agent:
                return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data.get('data', {})
            # timestamp = request.data.get('timestamp') # Not strictly needed for the 'date' field if we use server time or passed date
            
            # Determine date. Either from payload or server today.
            # Prefer payload 'timestamp' if available to handle offline sync correctly
            ts_str = request.data.get('timestamp') or datetime.now().isoformat()
            try:
                # Flexible parsing
                if 'T' in ts_str:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(ts_str)
                record_date = dt.date()
            except ValueError:
                record_date = timezone.now().date()

            # Create a new record for each interval
            DailyActivity.objects.create(
                agent=agent,
                date=record_date,
                timestamp=dt if 'dt' in locals() else timezone.now(),
                data=data
            )
            
            agent.last_seen = timezone.now()
            agent.save()

            return Response({"status": "received", "date": str(record_date)}, status=status.HTTP_200_OK)
        except Exception as e:
            import traceback
            return Response({"error": str(e), "trace": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MonthlyTelemetryView(AgentBaseView):
    """
    Receives Monthly Telemetry Data.
    Creates a new MonthlyActivity record.
    """
    @extend_schema(request=TelemetryUploadSerializer, responses={201: None})
    def post(self, request):
        try:
            agent = self.get_agent(request)
            if not agent:
                return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
            
            data = request.data.get('data', {})
            ts_str = request.data.get('timestamp') or datetime.now().isoformat()
            
            try:
                if 'T' in ts_str:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(ts_str)
                record_date = dt.date()
            except ValueError:
                record_date = timezone.now().date()

            MonthlyActivity.objects.create(
                agent=agent,
                date=record_date,
                data=data
            )

            agent.last_seen = timezone.now()
            agent.save()

            return Response({"status": "received", "date": str(record_date)}, status=status.HTTP_201_CREATED)
        except Exception as e:
            import traceback
            return Response({"error": str(e), "trace": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
