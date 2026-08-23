"""
WSGI config for the Inventory Management System project.

Exposes the WSGI callable as a module-level variable named ``application``.
This is what PythonAnywhere's WSGI config file will import when we get to
deployment.
"""

import os

from django.core.wsgi import get_wsgi_application

try:
    from dotenv import load_dotenv
except ImportError:
    pass  # python-dotenv not installed — falls back to real env vars only
else:
    # Local/dev convenience only. In production (PythonAnywhere) real
    # environment variables are set directly in the WSGI config file, and
    # load_dotenv() never overrides a variable that's already set — so this
    # is harmless there even if it runs.
    load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
