from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import permission_required
from .forms import AddMemberForm, CreateOrganizationForm, CreateRoleForm, EditMembershipForm
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
                is_owner_role=True,
                can_view_inventory=True,
                can_add_stock=True,
                can_remove_stock=True,
                can_borrow_items=True,
                can_delete_items=True,
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
def edit_role(request, role_id):
    """
    Editing a role's permissions affects *everyone* who holds that role at
    once — unlike editing one person's membership. That makes this the
    more dangerous of the two edit screens: turning off "manage users"
    here can silently strip that permission from every current holder of
    the role, including the person making the change.

    The built-in Owner role is exempt from this entirely — it can't be
    opened for editing at all. Owner always has every permission, by
    definition, so there is nothing to configure and nothing to
    accidentally break. That's what guarantees an organization can never
    end up with no one able to manage it: as long as one active member
    still holds Owner, someone always can. For every other (custom) role,
    the check below still blocks a save that would leave literally nobody
    in the organization able to manage users.
    """
    org = request.current_organization
    role = get_object_or_404(Role, pk=role_id, organization=org)

    if role.is_owner_role:
        messages.error(
            request,
            "The Owner role can't be edited — it always has full access by design, "
            "so the organization can never end up with no one able to manage it.",
        )
        return redirect('organizations:manage_roles')

    if request.method == 'POST':
        form = CreateRoleForm(request.POST, instance=role)
        if form.is_valid():
            losing_manage_permission = role.can_manage_users and not form.cleaned_data['can_manage_users']
            other_role_covers_it = Membership.objects.filter(
                organization=org, is_active=True, role__can_manage_users=True,
            ).exclude(role=role).exists()

            if losing_manage_permission and not other_role_covers_it:
                messages.error(
                    request,
                    "Can't save — no one in this organization would be able to manage users "
                    "anymore. Give another role \"Manage users\" first (or keep at least one "
                    "active member on a role that has it) before turning it off here.",
                )
            else:
                form.save()
                messages.success(request, f'Role "{role.name}" updated.')
                return redirect('organizations:manage_roles')
    else:
        form = CreateRoleForm(instance=role)

    return render(request, 'organizations/edit_role.html', {'form': form, 'role': role})


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


@permission_required('can_manage_users')
def edit_member(request, membership_id):
    """
    Reassign a member's Role, or deactivate their membership (revokes
    their access to this organization without deleting their login —
    they might belong to other organizations too).
    """
    membership = get_object_or_404(
        Membership, pk=membership_id, organization=request.current_organization,
    )
    org = request.current_organization

    if membership.user_id == request.user.id:
        messages.error(
            request,
            "You can't change your own role or deactivate yourself from here — have another "
            "admin do it, or use Django admin (/admin/) directly.",
        )
        return redirect('organizations:manage_members')

    if request.method == 'POST':
        form = EditMembershipForm(request.POST, instance=membership, organization=org)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            new_is_active = form.cleaned_data['is_active']

            # Guard against locking everyone (possibly including yourself)
            # out of managing this organization by removing the last
            # active can_manage_users membership.
            other_managers_exist = Membership.objects.filter(
                organization=org, is_active=True, role__can_manage_users=True,
            ).exclude(pk=membership.pk).exists()
            this_would_still_manage = new_is_active and new_role.can_manage_users

            if not this_would_still_manage and not other_managers_exist:
                messages.error(
                    request,
                    "Can't save — this would leave the organization with no one able to "
                    "manage users. Give someone else that permission first.",
                )
            else:
                form.save()
                messages.success(request, f"Updated {membership.user.username}'s membership.")
                return redirect('organizations:manage_members')
    else:
        form = EditMembershipForm(instance=membership, organization=org)

    return render(request, 'organizations/edit_member.html', {'form': form, 'membership': membership})
