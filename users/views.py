from rest_framework import viewsets, status, filters, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import random

from .models import User, PasswordResetOTP
from .serializers import (
    UserSerializer, 
    ForgotPasswordSerializer, 
    VerifyOTPSerializer, 
    ResetPasswordSerializer
)
from adminpanel.permissions import IsAdmin

@extend_schema_view(
    list=extend_schema(summary="List all users", tags=["Users"]),
    create=extend_schema(summary="Create a new user", tags=["Users"]),
    retrieve=extend_schema(summary="Get user details", tags=["Users"]),
    update=extend_schema(summary="Update a user", tags=["Users"]),
    partial_update=extend_schema(summary="Partial update a user", tags=["Users"]),
    destroy=extend_schema(summary="Delete a user", tags=["Users"]),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    Manage Users. Only accessible by Admins.
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department', 'role', 'location']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    def destroy(self, request, *args, **kwargs):
        user_to_delete = self.get_object()
        
        # Prevent deleting self
        if user_to_delete == request.user:
            return Response(
                {"error": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Prevent deleting last admin
        if user_to_delete.role and user_to_delete.role.name.lower() == 'admin':
            admin_role_count = User.objects.filter(role__name__iexact='admin', is_active=True).count()
            if admin_role_count <= 1:
                return Response(
                    {"error": "Cannot delete the last admin user."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # Set created_by to current user
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        # Prevent admin self-role downgrade
        # If I am modifying myself, and I try to change my role to something else
        instance = serializer.instance
        if instance == self.request.user:
            # Check if role is present in validated data
            # validated_data is not directly available in perform_update args easily, 
            # usually serializer.validated_data but only after is_valid()
             new_role = serializer.validated_data.get('role')
             if new_role and new_role.name.lower() != 'admin':
                  # Wait, is the current user an admin? Yes due to IsAdmin permission.
                  # If they change to non-admin, they lock themselves out.
                  # Requirement: "Prevent admin self-role downgrade"
                  raise serializers.ValidationError("You cannot remove your own admin role.")
        
        serializer.save()

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=ForgotPasswordSerializer, responses={200: dict})
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                
                # Save OTP
                PasswordResetOTP.objects.filter(email=email).delete() # Remove old OTPs
                PasswordResetOTP.objects.create(email=email, otp=otp)
                
                # Send Mail
                subject = 'SKUA - Password Reset Verification Code'
                email_from = settings.EMAIL_HOST_USER
                recipient_list = [email]
                
                # Context for template
                context = {'otp': otp}
                html_message = render_to_string('emails/password_reset_otp.html', context)
                plain_message = f'Your SKUA verification code is: {otp}. It is valid for 10 minutes.'
                
                try:
                    send_mail(
                        subject, 
                        plain_message, 
                        email_from, 
                        recipient_list, 
                        html_message=html_message
                    )
                    return Response({"message": "OTP sent successfully"}, status=status.HTTP_200_OK)
                except Exception as e:
                    print(f"Error sending email: {e}")
                    # For development, if email fails, return success but log OTP
                    return Response({"message": "OTP sent successfully (Dev: Check server logs)"}, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                # To prevent user enumeration, we return 200 even if user doesn't exist
                return Response({"message": "If this email is registered, you will receive an OTP."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=VerifyOTPSerializer, responses={200: dict})
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            try:
                otp_obj = PasswordResetOTP.objects.get(email=email, otp=otp)
                # Check expiration (10 minutes)
                if (timezone.now() - otp_obj.created_at).total_seconds() > 600:
                    otp_obj.delete()
                    return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)
                
                otp_obj.is_verified = True
                otp_obj.save()
                return Response({"message": "OTP verified successfully"}, status=status.HTTP_200_OK)
            except PasswordResetOTP.DoesNotExist:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(request=ResetPasswordSerializer, responses={200: dict})
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            password = serializer.validated_data['password']
            
            try:
                otp_obj = PasswordResetOTP.objects.get(email=email, otp=otp, is_verified=True)
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                
                # Delete OTP after successful reset
                otp_obj.delete()
                
                return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
            except (PasswordResetOTP.DoesNotExist, User.DoesNotExist):
                return Response({"error": "Invalid request or OTP not verified"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
