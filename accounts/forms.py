from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    """
    Account signup form.

    This only creates a *login* (a User). It does not create or join an
    organization yet — that's handled by the `organizations` app in the
    next piece, where a new user will either create a brand-new
    organization (becoming its owner) or accept an invitation to join an
    existing one.
    """

    email = User._meta.get_field('email').formfield(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
