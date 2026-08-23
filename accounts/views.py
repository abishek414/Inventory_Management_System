from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SignUpForm


def home(request):
    """
    Landing page for signed-out visitors (log in / sign up pitch). If
    you're already logged in, "Home" just takes you straight to your
    dashboard — there's nothing else useful to show you first.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'accounts/home.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def dashboard(request):
    """
    Placeholder home screen after login.

    Once the `organizations` app exists, this becomes: show the user's
    organization(s), let them switch between them, and (once `inventory`
    exists) show a stock overview for the active organization.
    """
    return render(request, 'accounts/dashboard.html')
