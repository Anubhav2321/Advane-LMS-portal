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

# Background auto-sync on server startup if faculty data or exam questions are missing in production DB
try:
    from students.models import User, Question
    missing_faculty = User.objects.filter(is_faculty=True).count() < 10
    missing_questions = Question.objects.count() < 50 or not Question.objects.filter(exam_id=50).exists()
    is_production = bool(os.getenv('RENDER') or os.getenv('PRODUCTION') or os.getenv('DATABASE_URL'))
    if (missing_faculty or missing_questions) and is_production:
        print(f"[WSGI-BOOT] Data missing in production DB (faculty missing: {missing_faculty}, questions missing: {missing_questions}). Triggering auto-sync...")
        from seed_db import smart_sync_production
        smart_sync_production(force=True)
except Exception as e:
    print(f"[WSGI-BOOT] Auto-sync notice: {e}")

