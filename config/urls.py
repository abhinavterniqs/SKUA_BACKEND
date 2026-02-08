from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from adminpanel.views import RoleViewSet, DepartmentViewSet, LocationViewSet, AdminLoginView, AgentViewSet
from users.views import UserViewSet, ForgotPasswordView, VerifyOTPView, ResetPasswordView

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='roles')
router.register(r'departments', DepartmentViewSet, basename='departments')
router.register(r'locations', LocationViewSet, basename='locations')
router.register(r'users', UserViewSet, basename='users')
router.register(r'agents', AgentViewSet, basename='agents')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Router
    path('api/', include(router.urls)),
    
    # Agent API
    path('api/agent/', include('agent_api.urls')),
    
    # Todos API
    path('', include('todos.urls')),
    
    # Auth Endpoint
    path('api/auth/login/', AdminLoginView.as_view(), name='auth_login'),
    path('api/auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('api/auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('api/auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    # Swagger / OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
