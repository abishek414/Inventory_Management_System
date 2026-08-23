from .models import Membership


def organization_context(request):
    """
    Makes the current organization/membership (set by
    CurrentOrganizationMiddleware) and the full list of the user's
    memberships available in every template, so the nav bar's
    organization switcher doesn't need every single view to pass them in.
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {}

    return {
        'current_organization': getattr(request, 'current_organization', None),
        'current_membership': getattr(request, 'current_membership', None),
        'user_memberships': Membership.objects.filter(
            user=request.user, is_active=True,
        ).select_related('organization'),
    }
