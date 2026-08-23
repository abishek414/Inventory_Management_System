"""
ASGI config for the Inventory Management System project.

Not needed for the PythonAnywhere deployment (which uses WSGI), but kept
for completeness / in case you ever run this behind an ASGI server.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
