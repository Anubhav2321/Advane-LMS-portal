"""
seed_db.py - Robust database seeder and synchronizer for AdvancedLMS on Render/Production.
- Performs resilient per-model update_or_create sync from mydata.json to guarantee 
  all faculty users, profiles, avatars, courses, live classes, exams, and notes load
  without transaction aborts or duplicate key crashes on PostgreSQL.
- Resets primary key sequences so subsequent creates never throw sequence collision errors.
"""
import os
import sys
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_core.settings')
django.setup()

from django.conf import settings
from django.db import connection
from django.core.management.color import no_style
from django.apps import apps
from students.models import (
    User, Profile, FacultyProfile, Course, Lesson, LiveClass, 
    Exam, LibraryDocument, Assignment
)

def reset_postgres_sequences():
    """
    Synchronizes PostgreSQL auto-increment sequence counters with highest primary keys.
    """
    if connection.vendor != 'postgresql':
        return
    print("[INFO] Resetting PostgreSQL primary key sequences...")
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

def smart_sync_production(force=False):
    """
    Reads mydata.json and syncs users, profiles, faculty profiles, courses, live classes,
    exams, library docs, and assignments using update_or_create to prevent unique-constraint
    failures on existing production databases.
    """
    data_file = os.path.join(str(settings.BASE_DIR), 'mydata.json')
    if not os.path.exists(data_file):
        print(f"[ERROR] Fixture file not found: {data_file}")
        return {"status": "error", "message": "mydata.json not found"}

    with open(data_file, 'r', encoding='utf-8') as f:
        items = json.load(f)

    # 1. Sync Users
    users_data = [x for x in items if x['model'] == 'students.user']
    synced_users = 0
    for u in users_data:
        flds = u['fields']
        user, _ = User.objects.update_or_create(
            username=flds['username'],
            defaults={
                'email': flds.get('email', ''),
                'first_name': flds.get('first_name', ''),
                'last_name': flds.get('last_name', ''),
                'is_faculty': flds.get('is_faculty', False),
                'is_teacher': flds.get('is_teacher', False),
                'is_student': flds.get('is_student', True),
                'is_staff': flds.get('is_staff', False),
                'is_superuser': flds.get('is_superuser', False),
                'phone': flds.get('phone', ''),
                'student_id': flds.get('student_id', ''),
            }
        )
        if flds.get('password'):
            user.password = flds['password']
            user.save(update_fields=['password'])
        synced_users += 1

    # 2. Sync Profiles (With Profile Pictures & Avatars)
    profiles_data = [x for x in items if x['model'] == 'students.profile']
    synced_profiles = 0
    for p in profiles_data:
        flds = p['fields']
        u_val = flds.get('user')
        uname = u_val[0] if isinstance(u_val, list) else u_val
        user = User.objects.filter(username=uname).first()
        if user:
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    'profile_pic': flds.get('profile_pic'),
                    'bio': flds.get('bio', ''),
                    'phone': flds.get('phone', ''),
                    'student_id': flds.get('student_id', ''),
                    'linkedin_url': flds.get('linkedin_url', ''),
                    'github_url': flds.get('github_url', ''),
                }
            )
            synced_profiles += 1

    # 3. Sync FacultyProfiles
    faculty_data = [x for x in items if x['model'] == 'students.facultyprofile']
    synced_faculty = 0
    for fp in faculty_data:
        flds = fp['fields']
        u_val = flds.get('user')
        uname = u_val[0] if isinstance(u_val, list) else u_val
        user = User.objects.filter(username=uname).first()
        if user:
            FacultyProfile.objects.update_or_create(
                user=user,
                defaults={
                    'department': flds.get('department', ''),
                    'experience_years': flds.get('experience_years', 0),
                    'salary': flds.get('salary', 0.0),
                    'specialization': flds.get('specialization', ''),
                    'background': flds.get('background', ''),
                    'job_role': flds.get('job_role', 'Professor / Instructor'),
                }
            )
            synced_faculty += 1

    # 4. Sync Courses
    courses_data = [x for x in items if x['model'] == 'students.course']
    synced_courses = 0
    for c in courses_data:
        flds = c['fields']
        cid = c.get('pk')
        Course.objects.update_or_create(
            id=cid,
            defaults={
                'title': flds.get('title', ''),
                'slug': flds.get('slug', ''),
                'description': flds.get('description', ''),
                'price': flds.get('price', 0.0),
                'coin_price': flds.get('coin_price', 0),
                'is_coin_purchasable': flds.get('is_coin_purchasable', False),
                'thumbnail': flds.get('thumbnail'),
                'total_modules': flds.get('total_modules', 1),
                'faculty_name': flds.get('faculty_name', ''),
                'is_published': flds.get('is_published', True),
                'difficulty': flds.get('difficulty', 'Beginner'),
            }
        )
        synced_courses += 1

    # 5. Sync Live Classes
    classes_data = [x for x in items if x['model'] == 'students.liveclass']
    synced_classes = 0
    for lc in classes_data:
        flds = lc['fields']
        lid = lc.get('pk')
        fac_val = flds.get('faculty')
        fac_user = None
        if isinstance(fac_val, list):
            fac_user = User.objects.filter(username=fac_val[0]).first()
        elif fac_val:
            fac_user = User.objects.filter(pk=fac_val).first()
        
        LiveClass.objects.update_or_create(
            id=lid,
            defaults={
                'title': flds.get('title', ''),
                'subject_name': flds.get('subject_name', ''),
                'stream_url': flds.get('stream_url', ''),
                'meeting_platform': flds.get('meeting_platform', 'jitsi'),
                'start_time': flds.get('start_time'),
                'duration_minutes': flds.get('duration_minutes', 60),
                'is_active': flds.get('is_active', False),
                'faculty': fac_user,
            }
        )
        synced_classes += 1

    # 6. Sync Exams
    exams_data = [x for x in items if x['model'] == 'students.exam']
    synced_exams = 0
    for ex in exams_data:
        flds = ex['fields']
        eid = ex.get('pk')
        Exam.objects.update_or_create(
            id=eid,
            defaults={
                'title': flds.get('title', ''),
                'subject_name': flds.get('subject_name', ''),
                'exam_type': flds.get('exam_type', 'mcq'),
                'duration_minutes': flds.get('duration_minutes', 30),
                'total_marks': flds.get('total_marks', 100),
                'pass_marks': flds.get('pass_marks', 40),
                'deadline_date': flds.get('deadline_date'),
                'is_expired': flds.get('is_expired', False),
            }
        )
        synced_exams += 1

    # 7. Sync Library Documents
    docs_data = [x for x in items if x['model'] == 'students.librarydocument']
    synced_docs = 0
    for doc in docs_data:
        flds = doc['fields']
        did = doc.get('pk')
        LibraryDocument.objects.update_or_create(
            id=did,
            defaults={
                'title': flds.get('title', ''),
                'subject_name': flds.get('subject_name', ''),
                'category': flds.get('category', 'lecture_notes'),
                'file': flds.get('file'),
                'description': flds.get('description', ''),
            }
        )
        synced_docs += 1

    # 8. Sync Assignments
    assignments_data = [x for x in items if x['model'] == 'students.assignment']
    synced_assignments = 0
    for a in assignments_data:
        flds = a['fields']
        aid = a.get('pk')
        Assignment.objects.update_or_create(
            id=aid,
            defaults={
                'title': flds.get('title', ''),
                'description': flds.get('description', ''),
                'due_date': flds.get('due_date'),
                'pass_marks': flds.get('pass_marks', 40),
                'total_marks': flds.get('total_marks', 100),
                'brief_file': flds.get('brief_file'),
            }
        )
        synced_assignments += 1

    reset_postgres_sequences()

    return {
        "status": "success",
        "synced_users": synced_users,
        "synced_profiles": synced_profiles,
        "synced_faculty_profiles": synced_faculty,
        "active_faculty_users": User.objects.filter(is_faculty=True).count(),
        "synced_courses": synced_courses,
        "synced_live_classes": synced_classes,
        "synced_exams": synced_exams,
        "synced_documents": synced_docs,
        "synced_assignments": synced_assignments,
    }

def seed():
    force = '--force' in sys.argv or os.getenv('FORCE_SEED', '').lower() in ('1', 'true', 'yes')
    faculty_count = User.objects.filter(is_faculty=True).count()
    has_courses = Course.objects.exists()

    if faculty_count >= 10 and has_courses and not force:
        print(f"[SAFEGUARD] Database already contains active faculty ({faculty_count}) and courses.")
        reset_postgres_sequences()
        return

    print(f"[INFO] Running smart production sync from mydata.json...")
    res = smart_sync_production(force=force)
    print(f"[SUCCESS] Result: {res}")

if __name__ == '__main__':
    seed()
