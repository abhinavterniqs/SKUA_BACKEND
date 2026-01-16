from django.db import models
from django.utils import timezone
from .models import Agent

class DailyActivity(models.Model):
    """
    Stores accumulated/latest daily data for an agent.
    One row per Agent per Date.
    """
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='daily_activities')
    date = models.DateField(default=timezone.now) # Business date
    timestamp = models.DateTimeField(default=timezone.now) # Exact time of capture
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Stores the aggregated daily data
    # Structure based on user_activity, application_usage, etc.
    data = models.JSONField(default=dict)

    class Meta:
        # unique_together removed to allow multiple entries per day
        indexes = [
            models.Index(fields=['agent', 'date']),
            models.Index(fields=['agent', 'timestamp']),
        ]
        verbose_name_plural = "Daily Activities"

    def __str__(self):
        return f"Daily Activity - {self.agent.hostname} ({self.timestamp})"

class MonthlyActivity(models.Model):
    """
    Stores monthly snapshots for an agent.
    One row per Agent per Month (usually created on the 1st or when the report runs).
    """
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='monthly_activities')
    date = models.DateField(default=timezone.now) # Effectively the month identifier
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Stores the snapshot data (hardware, software, security, os)
    data = models.JSONField(default=dict)

    class Meta:
        # We might want multiple snapshots per month if config changes, 
        # but usually report is once a month. For now, let's just index it.
        indexes = [
            models.Index(fields=['agent', 'date']),
        ]
        verbose_name_plural = "Monthly Activities"

    def __str__(self):
        return f"Monthly Snapshot - {self.agent.hostname} ({self.date.strftime('%Y-%m')})"
