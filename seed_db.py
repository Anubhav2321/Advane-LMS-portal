"""
seed_db.py - Safe database seeder for AdvancedLMS on Render/Production.
- Prevents data loss: Will NOT overwrite existing data if the database already contains courses/users.
- On a fresh/empty database: Loads initial data from mydata.json.
- On PostgreSQL: Resets primary key sequences so auto-increment never throws duplicate key errors.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_core.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.core.management.color import no_style
from django.apps import apps
from students.models import Course, User

def reset_postgres_sequences():
    """
    Synchronizes PostgreSQL auto-increment sequence counters with the highest existing primary keys.
    Prevents 'duplicate key value violates unique constraint' errors when creating new records.
    """
    if connection.vendor != 'postgresql':
        return
    print("[INFO] Resetting PostgreSQL primary key sequences to prevent duplicate key errors...")
    for app_name in ['students', 'auth', 'socialaccount', 'account']:
        try:
            app_config = apps.get_app_config(app_name)
            sequence_sql = connection.ops.sequence_reset_sql(no_style(), app_config.get_models())
            if sequence_sql:
                with connection.cursor() as cursor:
                    for sql in sequence_sql:
                        cursor.execute(sql)
                print(f"[OK] Sequences synchronized for app: {app_name}")
        except Exception as e:
            print(f"[WARN] Sequence reset for {app_name}: {e}")

def seed():
    force = '--force' in sys.argv or os.getenv('FORCE_SEED', '').lower() in ('1', 'true', 'yes')
    faculty_count = User.objects.filter(is_faculty=True).count()
    has_courses = Course.objects.exists()
    has_users = User.objects.filter(is_superuser=True).exists()

    # If already populated with full faculty data and courses, skip unless forced
    if faculty_count >= 10 and (has_courses or has_users) and not force:
        print(f"[SAFEGUARD] Database already contains active faculty ({faculty_count}) and courses.")
        print("[SAFEGUARD] Skipping loaddata. Use --force or FORCE_SEED=1 to re-sync.")
        reset_postgres_sequences()
        return

    print(f"[INFO] Seeding / synchronizing database from mydata.json (faculty count: {faculty_count}, force: {force})...")
    try:
        call_command('loaddata', 'mydata.json')
        print("[SUCCESS] Initial fixtures successfully loaded!")
    except Exception as e:
        print(f"[ERROR] Failed to load mydata.json: {e}")

    reset_postgres_sequences()

if __name__ == '__main__':
    seed()
