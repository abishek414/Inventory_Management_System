"""
Permission-checking decorators for the organizations app.

`CurrentOrganizationMiddleware` (see middleware.py) attaches
`request.current_organization` and `request.current_membership` to every
request for a logged-in user. These decorators build on that to answer:
"is there an organization in play, and is this member allowed to do X?"

The `inventory` app (built in a later piece) will lean on
`permission_required(...)` heavily — e.g.
`@permission_required('can_add_stock')` on the "add stock" view.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def organization_required(view_func):
    """Requires the user to be logged in AND have a current organization selected."""

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.current_organization is None:
            messages.info(request, 'Create or select an organization first.')
            return redirect('organizations:create')
        return view_func(request, *args, **kwargs)

    return wrapper


def permission_required(perm_name):
    """
    Requires a current organization AND that the member's Role has
    `perm_name` set (e.g. 'can_add_stock', 'can_manage_users').
    """

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
