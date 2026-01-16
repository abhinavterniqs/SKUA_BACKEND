from django.urls import path
from .views import EnrollAgentView, HeartbeatView
from .views_config import DailyConfigView, MonthlyConfigView
from .views_telemetry import DailyTelemetryView, MonthlyTelemetryView

urlpatterns = [
    path('enroll', EnrollAgentView.as_view(), name='agent-enroll'),
    # path('config', ... ) Removed
    path('config/daily', DailyConfigView.as_view(), name='agent-config-daily'),
    path('config/monthly', MonthlyConfigView.as_view(), name='agent-config-monthly'),
    # path('telemetry', ... ) Removed
    path('telemetry/daily', DailyTelemetryView.as_view(), name='agent-telemetry-daily'),
    path('telemetry/monthly', MonthlyTelemetryView.as_view(), name='agent-telemetry-monthly'),
    path('heartbeat', HeartbeatView.as_view(), name='agent-heartbeat'),
]
