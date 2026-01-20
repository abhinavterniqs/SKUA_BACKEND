
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone

class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    
    CATEGORY_CHOICES = [
        ('Billable', 'Billable'),
        ('Non-billable', 'Non-billable'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Billable')
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    time_spent = models.IntegerField(default=0)  # Saved accumulated seconds
    
    # Timer persistence fields
    is_running = models.BooleanField(default=False)
    last_started_at = models.DateTimeField(null=True, blank=True)
    
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    
    date_log = models.DateField(default=timezone.now) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"
