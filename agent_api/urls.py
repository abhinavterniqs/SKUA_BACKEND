from django.urls import path
from .views import EnrollAgentView, ConfigView, TelemetryView, HeartbeatView

urlpatterns = [
    path('enroll', EnrollAgentView.as_view(), name='agent-enroll'),
    path('config', ConfigView.as_view(), name='agent-config'),
    path('telemetry', TelemetryView.as_view(), name='agent-telemetry'),
    path('heartbeat', HeartbeatView.as_view(), name='agent-heartbeat'),
]
