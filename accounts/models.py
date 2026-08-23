from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for the whole project.

    Starting with a custom user model (even though it's close to Django's
    default for now) means we can add fields later — e.g. a phone number
    or a default organization — without a painful migration that swaps the
    user model out from under existing data.

    Which organization(s) a user belongs to, and what they're allowed to do
    in each one, is *not* stored here — that's the job of the
    `organizations` app (Organization / Role / Membership), built in the
    next piece. A single login can belong to more than one organization.
    """

    email = models.EmailField('email address', unique=True)

    def __str__(self):
        return self.get_full_name() or self.username
