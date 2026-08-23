from .models import Membership


def organization_context(request):
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {}

    return {
        'current_organization': getattr(request, 'current_organization', None),
        'current_membership': getattr(request, 'current_membership', None),
        'user_memberships': Membership.objects.filter(
            user=request.user, is_active=True,
        ).select_related('organization'),
    }
