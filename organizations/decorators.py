from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def organization_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.current_organization is None:
            messages.info(request, 'Create or select an organization first.')
            return redirect('organizations:create')
        return view_func(request, *args, **kwargs)

    return wrapper


def permission_required(perm_name):
    def decorator(view_func):
        @wraps(view_func)
        @organization_required
        def wrapper(request, *args, **kwargs):
            role = request.current_membership.role
            if not getattr(role, perm_name, False):
                messages.error(request, "You don't have permission to do that.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def admin_required(view_func):
    @wraps(view_func)
    @organization_required
    def wrapper(request, *args, **kwargs):
        if not request.current_membership.role.is_owner_role:
            messages.error(request, "Only the organization's Admin can do that.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)

    return wrapper
