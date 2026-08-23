"""
WSGI config for the Inventory Management System project.

Exposes the WSGI callable as a module-level variable named ``application``.
This is what PythonAnywhere's WSGI config file will import when we get to
deployment.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
