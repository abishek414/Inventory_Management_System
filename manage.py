#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass  # python-dotenv not installed yet — falls back to real env vars only
    else:
        # Reads a local ".env" file (if one exists) into the environment, so
        # settings.py's os.environ.get(...) calls can pick up real values —
        # e.g. real email credentials — without you having to set them by
        # hand in every new terminal window. See .env.example for the list
        # of variables it understands. Never commit the real ".env" file —
        # it's already in .gitignore.
        load_dotenv()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
