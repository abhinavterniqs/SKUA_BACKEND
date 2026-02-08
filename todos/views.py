
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from .models import Task
from .serializers import TaskSerializer, FlatTaskSerializer
import datetime
from django.utils import timezone

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'description']
    pagination_class = None # Disable pagination for all-in-one daily view

    def is_admin(self, user):
        return user.is_staff or (user.role and user.role.name.lower() == 'admin')

    def get_queryset(self):
        # Admin/Staff can see everything, normal users only their own
        if self.is_admin(self.request.user):
            return Task.objects.all()
        return Task.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        # Apply standard filters (status, category, search)
        queryset = self.filter_queryset(self.get_queryset())
        
        # Date filtering
        date_param = request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date_log=date_param)
        
        # User filtering (for admin view)
        user_id = request.query_params.get('user_id')
        if user_id and self.is_admin(request.user):
            queryset = queryset.filter(user_id=user_id)
        elif not self.is_admin(request.user):
            # Force current user if not admin
            queryset = queryset.filter(user=request.user)
            
        # Only return root tasks in list view to avoid duplicates
        queryset = queryset.filter(parent__isnull=True)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def range(self, request):
        """Fetch all tasks in a date range for analytics."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        user_id = request.query_params.get('user_id')
        
        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=400)
            
        queryset = self.get_queryset()
        
        # Filters
        queryset = queryset.filter(date_log__range=[start_date, end_date])
        
        if user_id and user_id != 'all' and self.is_admin(request.user):
            queryset = queryset.filter(user_id=user_id)
        elif not self.is_admin(request.user):
            queryset = queryset.filter(user=request.user)
            
        # For analytics, we usually want all tasks including subtasks in a flat list
        serializer = FlatTaskSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        date_param = request.query_params.get('date')
        user_id = request.query_params.get('user_id')
        
        if not date_param:
            return Response({"error": "Date parameter is required"}, status=400)
        
        queryset = Task.objects.all() if self.is_admin(request.user) else Task.objects.filter(user=request.user)
        
        if user_id and self.is_admin(request.user):
            tasks = queryset.filter(user_id=user_id, date_log=date_param)
        else:
            tasks = queryset.filter(user=request.user, date_log=date_param)
        
        # Calculate totals
        total_time = 0
        billable_time = 0
        now = timezone.now()
        
        for t in tasks:
            if t.status == 'Completed':
                seconds = t.time_spent
                if t.is_running and t.last_started_at:
                    seconds += int((now - t.last_started_at).total_seconds())
                    
                total_time += seconds
                if t.category == 'Billable':
                    billable_time += seconds
        
        leaf_nodes = tasks.filter(subtasks__isnull=True)
        leaf_total = leaf_nodes.count()
        leaf_completed = leaf_nodes.filter(status='Completed').count()
        
        utilization = min(round((total_time / 28800) * 100), 100)
        billable_ratio = 0
        if total_time > 0:
            billable_ratio = round((billable_time / total_time) * 100)
            
        return Response({
            "total_time": total_time,
            "billable_time": billable_time,
            "completed_count": leaf_completed,
            "pending_count": leaf_total - leaf_completed,
            "utilization": utilization,
            "billable_ratio": billable_ratio
        })

