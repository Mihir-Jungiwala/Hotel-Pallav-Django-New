#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Load a local .env file if present (e.g. DJANGO_DEBUG=True for local
    # development) so running the app doesn't require setting shell
    # environment variables by hand — cross-platform, unlike shell-specific
    # `export`/`set`/`$env:` syntax. No-op in production, where real
    # environment variables are set directly by the host.
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Main.settings')
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
