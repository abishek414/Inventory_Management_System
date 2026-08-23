from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm

from .models import User


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-check-input' if isinstance(field.widget, forms.CheckboxInput) else 'form-control'
            field.widget.attrs['class'] = css


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    email = User._meta.get_field('email').formfield(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class PasswordResetRequestForm(BootstrapFormMixin, PasswordResetForm):
    pass


class SetNewPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass
