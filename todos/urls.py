
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet

router = DefaultRouter()
router.register(r'todos', TaskViewSet, basename='task')

urlpatterns = [
    path('api/', include(router.urls)),
]
