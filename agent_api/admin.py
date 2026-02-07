from django.contrib import admin

# Register your models here.
from .models import Agent, TelemetryLog

admin.site.register(Agent)
admin.site.register(TelemetryLog)