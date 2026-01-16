from rest_framework import serializers
from .models import Agent, TelemetryLog

class AgentEnrollmentSerializer(serializers.Serializer):
    secret_key = serializers.CharField(write_only=True)
    system_id = serializers.CharField()
    hostname = serializers.CharField(required=False, allow_blank=True)
    os_info = serializers.CharField(required=False, allow_blank=True)

class TelemetrySerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    system_id = serializers.CharField()

    class Meta:
        model = TelemetryLog
        fields = ['user_id', 'system_id', 'data', 'timestamp']

class HeartbeatSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    system_id = serializers.CharField()

class DailyConfigSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False, help_text="Required for POST updates to identify target user")
    system_id = serializers.CharField(required=False, help_text="Required for POST updates to identify target system")
    days = serializers.IntegerField(required=False, help_text="Optional. If provided, overrides capture_interval_seconds in data")
    data = serializers.DictField(help_text="The actual configuration object")

class MonthlyConfigSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    system_id = serializers.CharField(required=False)
    days = serializers.IntegerField(required=False, help_text="Optional. If provided, overrides capture_interval_seconds in data")
    data = serializers.DictField(help_text="The actual configuration object")

class TelemetryUploadSerializer(serializers.Serializer):
    """
    Serializer for Daily/Monthly telemetry upload.
    Explicitly requires user_id and system_id.
    """
    user_id = serializers.IntegerField()
    system_id = serializers.CharField()
    timestamp = serializers.DateTimeField(required=False)
    data = serializers.DictField()
