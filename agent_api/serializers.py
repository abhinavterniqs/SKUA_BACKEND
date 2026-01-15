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
