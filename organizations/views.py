from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import permission_required
from .forms import AddMemberForm, CreateOrganizationForm, CreateRoleForm
from .models import Membership, Role


@login_required
def create_organization(request):
    """
    Any logged-in user can create an organization; doing so makes them its
    Owner — a role that's created automatically with every permission
    switched on, so the very first person in a new organization is never
    locked out of managing it.
    """
    if request.method == 'POST':
        form = CreateOrganizationForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.created_by = request.user
            org.save()

            owner_role = Role.objects.create(
                organization=org,
                name='Owner',
                can_view_inventory=True,
                can_add_stock=True,
                can_remove_stock=True,
                can_edit_items=True,
                can_upload_excel=True,
                can_manage_users=True,
            )
            Membership.objects.create(user=request.user, organization=org, role=owner_role)

            request.session['current_org_id'] = org.id
            messages.success(request, f'"{org.name}" created — you are its Owner.')
            return redirect('dashboard')
    else:
        form = CreateOrganizationForm()

    return render(request, 'organizations/create_organization.html', {'form': form})


@login_required
def switch_organization(request, org_id):
    """Changes which organization's data the current session is working in."""
    membership = Membership.objects.filter(
        user=request.user, organization_id=org_id, is_active=True,
    ).select_related('organization').first()

    if membership is None:
        messages.error(request, "You're not a member of that organization.")
    else:
        request.session['current_org_id'] = membership.organization_id
        messages.success(request, f'Switched to "{membership.organization.name}".')

    return redirect('dashboard')


@permission_required('can_manage_users')
def manage_roles(request):
    roles = request.current_organization.roles.all()
    return render(request, 'organizations/manage_roles.html', {'roles': roles})


@permission_required('can_manage_users')
def create_role(request):
    if request.method == 'POST':
        form = CreateRoleForm(request.POST)
        if form.is_valid():
            role = form.save(commit=False)
            role.organization = request.current_organization
            role.save()
            messages.success(request, f'Role "{role.name}" created.')
            return redirect('organizations:manage_roles')
    else:
        form = CreateRoleForm()

    return render(request, 'organizations/create_role.html', {'form': form})


@permission_required('can_manage_users')
def manage_members(request):
    members = request.current_organization.memberships.select_related('user', 'role')
    return render(request, 'organizations/manage_members.html', {'members': members})


@permission_required('can_manage_users')
def add_member(request):
    org = request.current_organization

    if request.method == 'POST':
        form = AddMemberForm(request.POST, organization=org)
        if form.is_valid():
            user = form.save()
            Membership.objects.create(user=user, organization=org, role=form.cleaned_data['role'])
            messages.success(
                request,
                f'Account "{user.username}" created and added to "{org.name}" as '
                f'{form.cleaned_data["role"].name}. Share their username and password '
                'with them directly — this form does not email anything.',
            )
            return redirect('organizations:manage_members')
    else:
        form = AddMemberForm(organization=org)

    return render(request, 'organizations/add_member.html', {'form': form})
