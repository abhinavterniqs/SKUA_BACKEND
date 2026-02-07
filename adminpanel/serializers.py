from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Role, Department
from users.models import User
from agent_api.models import Agent
from agent_api.models_activity import DailyActivity, MonthlyActivity

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom user data to response
        user = self.user
        
        # Helper to safely get profile pic url
        profile_pic_url = None
        if user.profile_pic:
            request = self.context.get('request')
            if request:
                profile_pic_url = request.build_absolute_uri(user.profile_pic.url)
            else:
                 profile_pic_url = user.profile_pic.url

        user_data = {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "mobile": user.mobile,
            "role": user.role.name if user.role else None,
            "is_active": user.is_active,
            "department": user.department.name if user.department else None, # Include department name
            "profile_pic_url": profile_pic_url
        }
        
        data['user'] = user_data
        
        return {
            "access": data['access'],
            "refresh": data['refresh'], 
            "user": user_data
        }

class DailyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyActivity
        fields = '__all__'

class MonthlyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyActivity
        fields = '__all__'

class UserMiniSerializer(serializers.ModelSerializer):
    """Minimal user info for Agent listing"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'department', 'role']
        depth = 1 # To get role/dept names if foreign keys

class AgentSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    latest_daily = serializers.SerializerMethodField()
    latest_monthly = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = '__all__'

    def get_is_online(self, obj):
        # Calculate online status based on last_seen and capture interval
        if not obj.last_seen:
            return False
            
        from django.utils import timezone
        now = timezone.now()
        diff = (now - obj.last_seen).total_seconds()
        
        # Get interval from config, default to 60s if missing
        interval = obj.daily_config.get('capture_interval_seconds', 60)
        # Allow grace period (e.g. 3x interval or minimum 60s)
        threshold = max(interval * 3, 60)
        
        return diff < threshold

    def get_latest_daily(self, obj):
        # Get date from query params
        request = self.context.get('request')
        target_date_str = request.query_params.get('date') if request else None
        
        from django.utils import timezone
        import datetime
        
        if target_date_str:
            try:
                target_date = datetime.date.fromisoformat(target_date_str)
            except ValueError:
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()

        # Fetch ALL activities for the date to aggregate
        activities = obj.daily_activities.filter(date=target_date)
        
        if not activities.exists():
            return None
            
        # Aggregate Data
        total_active_time = 0
        total_idle_time = 0
        app_usage_map = {} # name -> { category, time }
        
        # Keep track of latest snapshot for other fields
        latest_record = activities.order_by('-timestamp').first()
        
        for activity in activities:
            data = activity.data or {}
            
            # User Activity
            ua = data.get('user_activity', {})
            total_active_time += ua.get('Active Time', 0)
            total_idle_time += ua.get('Idle Time', 0)
            
            # App Usage
            apps_list = data.get('application_usage', {}).get('Applications', [])
            for app in apps_list:
                name = app.get('Active Application Name')
                if name:
                    if name not in app_usage_map:
                        app_usage_map[name] = {
                            'category': app.get('Application Category', 'Unknown'),
                            'time': 0
                        }
                    app_usage_map[name]['time'] += app.get('Foreground Time', 0)
        
        # Construct Aggregated Object
        aggregated_apps = []
        for name, details in app_usage_map.items():
            aggregated_apps.append({
                "Active Application Name": name,
                "Application Category": details['category'],
                "Foreground Time": details['time']
            })
            
        # Sort apps by time descending
        aggregated_apps.sort(key=lambda x: x['Foreground Time'], reverse=True)
            
        # Base structure on latest record to keep consistent fields like network, hardware etc.
        # But override the aggregated fields
        aggregated_data = latest_record.data.copy() if latest_record.data else {}
        
        aggregated_data['user_activity'] = {
            "Login Time": aggregated_data.get('user_activity', {}).get('Login Time'), # Keep latest or first? Maybe First?
            "Logout Time": aggregated_data.get('user_activity', {}).get('Logout Time'),
            "Active Time": total_active_time, # Aggregated
            "Idle Time": total_idle_time     # Aggregated
        }
        
        if 'application_usage' not in aggregated_data:
            aggregated_data['application_usage'] = {}
            
        aggregated_data['application_usage']['Applications'] = aggregated_apps
        
        # Return as serialized-like dict
        return {
            "id": latest_record.id,
            "agent": obj.id,
            "date": str(target_date),
            "timestamp": latest_record.timestamp,
            "created_at": latest_record.created_at,
            "data": aggregated_data
        }

    def get_latest_monthly(self, obj):
        # Efficiently get latest
        latest = obj.monthly_activities.order_by('-date').first()
        if latest:
            return MonthlyActivitySerializer(latest).data
        return None

class AgentDetailSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    daily_activities = DailyActivitySerializer(many=True, read_only=True)
    monthly_activities = MonthlyActivitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Agent
        fields = '__all__'
