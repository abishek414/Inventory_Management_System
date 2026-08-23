from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.forms import BootstrapFormMixin
from accounts.models import User

from .models import Membership, Organization, Role


class CreateOrganizationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']


class CreateRoleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            'name', 'can_view_inventory', 'can_add_stock', 'can_remove_stock',
            'can_borrow_items', 'can_delete_items',
            'can_edit_items', 'can_upload_excel', 'can_manage_users',
        ]


class AddMemberForm(BootstrapFormMixin, UserCreationForm):
    role = forms.ModelChoiceField(queryset=Role.objects.none(), empty_label='— Choose a role —')

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role')

    def __init__(self, *args, organization=None, can_assign_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is not None:
            queryset = organization.roles.all()
            if not can_assign_admin:
                queryset = queryset.exclude(is_owner_role=True)
            self.fields['role'].queryset = queryset


class EditMembershipForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Membership
        fields = ['role', 'is_active']

    def __init__(self, *args, organization=None, can_assign_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].empty_label = None
        if organization is not None:
            queryset = organization.roles.all()
            if not can_assign_admin:
                queryset = queryset.exclude(is_owner_role=True)
            self.fields['role'].queryset = queryset
