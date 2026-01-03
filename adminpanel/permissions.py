from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users with 'admin' role or superusers.
    """
    
    def has_permission(self, request, view):
        # Allow access if user is authenticated and has 'admin' role
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Check if active is required (already checked by default Auth usually, but explicit check is good)
        if not request.user.is_active:
            return False

        # Superuser always has access
        if request.user.is_superuser:
            return True
            
        # User must have a role and that role must be 'admin'
        if request.user.role and request.user.role.name.lower() == 'admin':
            return True
            
        return False
