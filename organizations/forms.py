from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.forms import BootstrapFormMixin
from accounts.models import User

from .models import Organization, Role


class CreateOrganizationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']


class CreateRoleForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Role
        fields = [
            'name', 'can_view_inventory', 'can_add_stock', 'can_remove_stock',
            'can_edit_items', 'can_upload_excel', 'can_manage_users',
        ]


class AddMemberForm(BootstrapFormMixin, UserCreationForm):
    """
    Creates a brand-new login AND immediately assigns it a Role in the
    organization creating it. This matches how the system is meant to
    work per the original brief: the organization sets up accounts for
    its own staff and assigns their access level, rather than staff
    self-registering and asking to join.

    The admin using this form is responsible for passing the username
    and password to that employee themselves — the form doesn't email
    anything.
    """

    role = forms.ModelChoiceField(queryset=Role.objects.none(), empty_label=None)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role')

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.fields['role'].queryset = organization.roles.all()
