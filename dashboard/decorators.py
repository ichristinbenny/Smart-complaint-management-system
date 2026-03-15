from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def superadmin_required(view_func):
    """
    Decorator for views that checks that the user is logged in and is a superuser.
    """
    def check_user(user):
        if user.is_authenticated and user.is_superuser:
            return True
        raise PermissionDenied
    
    return user_passes_test(check_user)(view_func)
