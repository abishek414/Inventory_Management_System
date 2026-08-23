from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm

from .models import User


class BootstrapFormMixin:
    """
    Django doesn't add any CSS classes to form fields by default, so
    without this every <input> renders as a bare, unstyled browser
    control even inside our Bootstrap-based templates. This mixin adds
    the right Bootstrap class to every field automatically, so any form
    that uses it "just looks right" without repeating widget attrs by
    hand. Shared with organizations/forms.py.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs['class'] = css


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    """
    Account signup form.

    This only creates a *login* (a User). It does not create or join an
    organization — that's a separate step in the `organizations` app: a
    new user either creates a brand-new organization (becoming its
    Owner) or has an account created for them directly by an existing
    organization admin (see organizations.views.add_member).
    """

    email = User._meta.get_field('email').formfield(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """Just Django's built-in login form, styled to match the rest of the site."""
    pass


class PasswordResetRequestForm(BootstrapFormMixin, PasswordResetForm):
    """The "enter your email" form on the forgot-password page — just Django's
    built-in form, styled to match the rest of the site."""
    pass


class SetNewPasswordForm(BootstrapFormMixin, SetPasswordForm):
    """The "choose a new password" form reached from the emailed reset link —
    just Django's built-in form, styled to match the rest of the site."""
    pass
