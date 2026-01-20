
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q
from .models import Task
from .serializers import TaskSerializer
import datetime
from django.utils import timezone

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'description']
    pagination_class = None # Disable pagination for all-in-one daily view

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Date filtering (custom because field name alias)
        date_param = request.query_params.get('date')
        if date_param:
            queryset = queryset.filter(date_log=date_param)
        
        # Only return root tasks in list view to avoid duplicates
        # because the serializer includes the full subtask tree
        queryset = queryset.filter(parent__isnull=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        date_param = request.query_params.get('date')
        if not date_param:
            return Response({"error": "Date parameter is required"}, status=400)
        
        tasks = Task.objects.filter(user=request.user, date_log=date_param)
        
        # Calculate totals
        total_time = 0
        billable_time = 0
        now = timezone.now()
        
        # Iterate to handle running timers dynamically
        for t in tasks:
            # Only count time if task is COMPLETED (as per user request)
            if t.status == 'Completed':
                # Base stored time
                seconds = t.time_spent
                
                # If for some reason a completed task is "running" (shouldn't happen but for safety)
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

