#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from decouple import config
from django.core.cache import cache

def main():
    """Run administrative tasks."""
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", config("DJANGO_SETTINGS_MODULE", default="mycrm.settings.prod")
    )
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        from django.core.cache import cache
        print("[Cache] Clearing cache on startup (safe mode)...")
        try:
            cache.clear()
            print("[Cache] Cleared successfully ✅")
        except Exception as e:
            print(f"[Cache] Failed to clear cache: {e}")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
