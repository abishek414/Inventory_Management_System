import os

from django.core.wsgi import get_wsgi_application

try:
    from dotenv import load_dotenv
except ImportError:
    pass
else:
    load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
