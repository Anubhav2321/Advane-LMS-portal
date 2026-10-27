"""
WSGI config for lms_core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_core.settings')

application = get_wsgi_application()

# Background auto-sync on server startup if faculty data is missing in production DB
try:
    from students.models import User
    if User.objects.filter(is_faculty=True).count() < 10:
        print("[WSGI-BOOT] Faculty data missing in production DB. Triggering auto-sync...")
        from seed_db import smart_sync_production
        smart_sync_production(force=True)
except Exception as e:
    print(f"[WSGI-BOOT] Auto-sync notice: {e}")

