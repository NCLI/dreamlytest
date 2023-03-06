#!/nix/store/0pyymzxf7n0fzpaqnvwv92ab72v3jq8d-python3-3.10.9/bin/python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import subprocess
import signal


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daikoudream.settings')
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
