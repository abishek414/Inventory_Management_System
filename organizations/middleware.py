from .models import Membership


class CurrentOrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_membership = None
        request.current_organization = None

        if request.user.is_authenticated:
            memberships = Membership.objects.filter(
                user=request.user, is_active=True,
            ).select_related('organization', 'role')

            membership = None
            current_org_id = request.session.get('current_org_id')
            if current_org_id:
                membership = memberships.filter(organization_id=current_org_id).first()

            if membership is None and memberships.count() == 1:
                membership = memberships.first()
                request.session['current_org_id'] = membership.organization_id

            if membership is not None:
                request.current_membership = membership
                request.current_organization = membership.organization

        return self.get_response(request)
