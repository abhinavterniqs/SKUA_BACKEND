from django.db import models
from django.conf import settings
from django.utils import timezone

class Agent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agents')
    system_id = models.CharField(max_length=255, unique=True)
    hostname = models.CharField(max_length=255, blank=True)
    os_info = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(default=timezone.now)
    
    # Store per-agent configuration overrides here
    # Store per-agent configuration overrides here
    daily_config = models.JSONField(default=dict, blank=True)
    monthly_config = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.hostname} ({self.system_id[:8]})"

class TelemetryLog(models.Model):
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='telemetry_logs')
    timestamp = models.DateTimeField() # Timestamp from the agent payload
    received_at = models.DateTimeField(auto_now_add=True) # When we received it
    
    data = models.JSONField() # The full telemetry payload

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['agent', 'timestamp']),
        ]

    def __str__(self):
        return f"Log {self.agent.hostname} @ {self.timestamp}"
