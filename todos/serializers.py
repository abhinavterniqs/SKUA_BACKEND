
from rest_framework import serializers
from .models import Task
from django.utils import timezone

class TaskSerializer(serializers.ModelSerializer):
    subtasks = serializers.SerializerMethodField()
    parentId = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(), 
        source='parent', 
        allow_null=True, 
        required=False
    )
    timeSpent = serializers.IntegerField(source='time_spent', required=False)
    startTime = serializers.TimeField(source='start_time', required=False, allow_null=True, format='%H:%M', input_formats=['%H:%M'])
    endTime = serializers.TimeField(source='end_time', required=False, allow_null=True, format='%H:%M', input_formats=['%H:%M'])
    createdAt = serializers.DateField(source='date_log', required=False)
    
    # New Fields
    isRunning = serializers.BooleanField(source='is_running', required=False)
    lastStartedAt = serializers.DateTimeField(source='last_started_at', required=False, allow_null=True)
    userId = serializers.IntegerField(source='user_id', read_only=True)
    
    isExpanded = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'parentId', 'title', 'description', 'category', 'status',
            'timeSpent', 'startTime', 'endTime', 'createdAt', 'subtasks', 'isExpanded',
            'isRunning', 'lastStartedAt', 'userId'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
        }

    def get_subtasks(self, obj):
        serializer = TaskSerializer(obj.subtasks.all(), many=True, context=self.context)
        return serializer.data

    def get_isExpanded(self, obj):
        return False
    
    def validate_parentId(self, value):
        user = self.context['request'].user
        if value and value.user != user:
            raise serializers.ValidationError("Cannot link to a task that does not belong to you.")
        return value

    def create(self, validated_data):
        parent = validated_data.get('parent')
        if parent:
            # 1. Inherit category from parent
            validated_data['category'] = parent.category
            
            # 2. If parent is completed, mark it as Pending (reopen it)
            if parent.status == 'Completed':
                parent.status = 'Pending'
                parent.save()
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Handle Timer Logic
        new_is_running = validated_data.get('is_running')
        
        if new_is_running is not None:
            # Case 1: Starting the timer
            if new_is_running and not instance.is_running:
                instance.last_started_at = timezone.now()
            
            # Case 2: Stopping the timer
            elif not new_is_running and instance.is_running:
                if instance.last_started_at:
                    delta = (timezone.now() - instance.last_started_at).total_seconds()
                    instance.time_spent += int(delta)
                instance.last_started_at = None
                
        # Handle manual time adjustments (if frontend sends explicit timeSpent)
        # Note: If timer is running, backend logic takes precedence for the delta, 
        # but if user edits time manually while stopped, we accept it.
        # Use 'get' to check presence because 0 is falsy
        if 'time_spent' in validated_data and not instance.is_running:
             instance.time_spent = validated_data['time_spent']

        return super().update(instance, validated_data)

class FlatTaskSerializer(serializers.ModelSerializer):
    userId = serializers.IntegerField(source='user_id', read_only=True)
    parentId = serializers.PrimaryKeyRelatedField(source='parent', read_only=True)
    timeSpent = serializers.IntegerField(source='time_spent', read_only=True)
    startTime = serializers.TimeField(source='start_time', read_only=True, format='%H:%M')
    endTime = serializers.TimeField(source='end_time', read_only=True, format='%H:%M')
    createdAt = serializers.DateField(source='date_log', read_only=True)
    isRunning = serializers.BooleanField(source='is_running', read_only=True)
    lastStartedAt = serializers.DateTimeField(source='last_started_at', read_only=True)
    
    # Return empty subtasks list to satisfy frontend interface without recursion
    subtasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'parentId', 'title', 'description', 'category', 'status',
            'timeSpent', 'startTime', 'endTime', 'createdAt', 'subtasks', 
            'isRunning', 'lastStartedAt', 'userId'
        ]
        
    def get_subtasks(self, obj):
        return []
