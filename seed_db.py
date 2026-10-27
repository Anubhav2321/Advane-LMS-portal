"""
seed_db.py - Resilient, zero-crash database seeder & synchronizer for AdvancedLMS on Render.
- Uses update_or_create / get_or_create with precise model field mapping matching mydata.json.
- Each model is protected by per-item try-except blocks so individual data quirks NEVER crash the build.
- Synchronizes PostgreSQL primary key sequence counters to eliminate subsequent duplicate key collisions.
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
    Exam, LibraryDocument, Assignment, Enrollment
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
                        try:
                            cursor.execute(sql)
                        except Exception as sqle:
                            print(f"[WARN] Sequence statement notice: {sqle}")
                print(f"[OK] Sequences synchronized for app: {app_name}")
        except Exception as e:
            print(f"[WARN] Sequence reset for {app_name}: {e}")

def smart_sync_production(force=False):
    """
    Reads mydata.json and syncs users, profiles, faculty profiles, courses, lessons,
    live classes, exams, library docs, assignments, and enrollments.
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
        try:
            flds = u['fields']
            uname = flds['username']
            user = User.objects.filter(username=uname).first()
            if not user:
                user = User(username=uname)

            user.email = flds.get('email', '') or ''
            user.first_name = flds.get('first_name', '') or ''
            user.last_name = flds.get('last_name', '') or ''
            user.is_faculty = flds.get('is_faculty', False)
            user.is_teacher = flds.get('is_teacher', False)
            user.is_student = flds.get('is_student', True)
            user.is_staff = flds.get('is_staff', False)
            user.is_superuser = flds.get('is_superuser', False)
            user.phone = flds.get('phone', '') or ''
            user.student_level = flds.get('student_level', 'Beginner')
            user.stream = flds.get('stream', '') or ''
            user.lms_coins = flds.get('lms_coins', 100)
            user.reputation_score = flds.get('reputation_score', 100)
            user.engagement_score = flds.get('engagement_score', 100)

            # Unique student_id handling to prevent PostgreSQL duplicate key crashes
            sid = flds.get('student_id')
            if sid:
                existing = User.objects.filter(student_id=sid).exclude(username=uname).first()
                if not existing:
                    user.student_id = sid

            if flds.get('password'):
                user.password = flds['password']

            user.save()
            synced_users += 1
        except Exception as ue:
            print(f"[WARN] User sync notice for {u.get('fields', {}).get('username')}: {ue}")

    # 2. Sync Profiles (With Profile Pictures & Avatars)
    profiles_data = [x for x in items if x['model'] == 'students.profile']
    synced_profiles = 0
    for p in profiles_data:
        try:
            flds = p['fields']
            u_val = flds.get('user')
            uname = u_val[0] if isinstance(u_val, list) else u_val
            user = User.objects.filter(username=uname).first() if isinstance(uname, str) else User.objects.filter(pk=uname).first()
            if user:
                prof, _ = Profile.objects.get_or_create(user=user)
                if flds.get('profile_pic'):
                    prof.profile_pic = flds['profile_pic']
                prof.bio = flds.get('bio', '') or ''
                prof.phone = flds.get('phone', '') or ''
                prof.linkedin_url = flds.get('linkedin_url', '') or ''
                prof.github_url = flds.get('github_url', '') or ''
                prof.address = flds.get('address', '') or ''
                prof.save()
                synced_profiles += 1
        except Exception as pe:
            print(f"[WARN] Profile sync notice: {pe}")

    # 3. Sync FacultyProfiles
    faculty_data = [x for x in items if x['model'] == 'students.facultyprofile']
    synced_faculty = 0
    for fp in faculty_data:
        try:
            flds = fp['fields']
            u_val = flds.get('user')
            uname = u_val[0] if isinstance(u_val, list) else u_val
            user = User.objects.filter(username=uname).first() if isinstance(uname, str) else User.objects.filter(pk=uname).first()
            if user:
                fac, _ = FacultyProfile.objects.get_or_create(user=user)
                fac.department = flds.get('department', '') or ''
                fac.experience_years = flds.get('experience_years', 0) or 0
                fac.salary = flds.get('salary', 0.0) or 0.0
                fac.specialization = flds.get('specialization', '') or ''
                fac.background = flds.get('background', '') or ''
                fac.job_role = flds.get('job_role', 'Professor / Instructor') or 'Professor'
                fac.save()
                synced_faculty += 1
        except Exception as fe:
            print(f"[WARN] FacultyProfile sync notice: {fe}")

    # 4. Sync Courses
    courses_data = [x for x in items if x['model'] == 'students.course']
    synced_courses = 0
    for c in courses_data:
        try:
            flds = c['fields']
            cid = c.get('pk')
            course, _ = Course.objects.get_or_create(id=cid)
            course.title = flds.get('title', '')
            course.slug = flds.get('slug', '')
            course.description = flds.get('description', '')
            course.faculty_name = flds.get('faculty_name', '')
            course.price = flds.get('price', 0.0) or 0.0
            course.coin_price = flds.get('coin_price', 0) or 0
            course.is_coin_purchasable = flds.get('is_coin_purchasable', False)
            if flds.get('thumbnail'):
                course.thumbnail = flds['thumbnail']
            course.total_modules = flds.get('total_modules', 1) or 1
            course.is_published = flds.get('is_published', True)
            course.difficulty_level = flds.get('difficulty_level', 'Beginner')
            course.save()
            synced_courses += 1
        except Exception as ce:
            print(f"[WARN] Course sync notice for id {c.get('pk')}: {ce}")

    # 5. Sync Lessons
    lessons_data = [x for x in items if x['model'] == 'students.lesson']
    synced_lessons = 0
    for l in lessons_data:
        try:
            flds = l['fields']
            lid = l.get('pk')
            course_id = flds.get('course')
            course = Course.objects.filter(id=course_id).first() if course_id else None
            lesson, _ = Lesson.objects.get_or_create(id=lid)
            lesson.course = course
            lesson.title = flds.get('title', '')
            lesson.slug = flds.get('slug', '')
            lesson.video_file = flds.get('video_file', '')
            lesson.video_url = flds.get('video_url', '')
            lesson.content = flds.get('content', '')
            lesson.duration = flds.get('duration', '')
            lesson.order = flds.get('order', 1) or 1
            lesson.is_preview = flds.get('is_preview', False)
            lesson.is_completed = flds.get('is_completed', False)
            lesson.save()
            synced_lessons += 1
        except Exception as le:
            print(f"[WARN] Lesson sync notice for id {l.get('pk')}: {le}")

    # 6. Sync Live Classes
    classes_data = [x for x in items if x['model'] == 'students.liveclass']
    synced_classes = 0
    for lc in classes_data:
        try:
            flds = lc['fields']
            lid = lc.get('pk')
            cid = flds.get('course')
            course = Course.objects.filter(id=cid).first() if cid else None
            lc_obj, _ = LiveClass.objects.get_or_create(id=lid)
            lc_obj.course = course
            lc_obj.title = flds.get('title', '')
            lc_obj.description = flds.get('description', '')
            lc_obj.meeting_link = flds.get('meeting_link', '')
            lc_obj.date_time = flds.get('date_time')
            lc_obj.duration_minutes = flds.get('duration_minutes', 60) or 60
            lc_obj.platform = flds.get('platform', 'Google Meet')
            lc_obj.instructor_name = flds.get('instructor_name', '')
            lc_obj.meeting_id = flds.get('meeting_id', '')
            lc_obj.passcode = flds.get('passcode', '')
            lc_obj.recording_url = flds.get('recording_url', '')
            lc_obj.resources_link = flds.get('resources_link', '')
            lc_obj.agenda = flds.get('agenda', '')
            lc_obj.is_cancelled = flds.get('is_cancelled', False)
            lc_obj.save()
            synced_classes += 1
        except Exception as lce:
            print(f"[WARN] LiveClass sync notice for id {lc.get('pk')}: {lce}")

    # 7. Sync Exams
    exams_data = [x for x in items if x['model'] == 'students.exam']
    synced_exams = 0
    for ex in exams_data:
        try:
            flds = ex['fields']
            eid = ex.get('pk')
            cid = flds.get('course')
            course = Course.objects.filter(id=cid).first() if cid else None
            exam_obj, _ = Exam.objects.get_or_create(id=eid)
            exam_obj.course = course
            exam_obj.title = flds.get('title', '')
            exam_obj.description = flds.get('description', '')
            exam_obj.exam_link = flds.get('exam_link', '')
            exam_obj.deadline = flds.get('deadline')
            exam_obj.duration_minutes = flds.get('duration_minutes', 30) or 30
            exam_obj.total_marks = flds.get('total_marks', 100) or 100
            exam_obj.is_active = flds.get('is_active', True)
            exam_obj.save()
            synced_exams += 1
        except Exception as ee:
            print(f"[WARN] Exam sync notice for id {ex.get('pk')}: {ee}")

    # 8. Sync Library Documents
    docs_data = [x for x in items if x['model'] == 'students.librarydocument']
    synced_docs = 0
    for doc in docs_data:
        try:
            flds = doc['fields']
            did = doc.get('pk')
            cid = flds.get('course')
            course = Course.objects.filter(id=cid).first() if cid else None
            up_val = flds.get('uploaded_by')
            up_user = None
            if isinstance(up_val, list) and up_val:
                up_user = User.objects.filter(username=up_val[0]).first()
            elif up_val:
                up_user = User.objects.filter(pk=up_val).first()

            doc_obj, _ = LibraryDocument.objects.get_or_create(id=did)
            doc_obj.course = course
            doc_obj.title = flds.get('title', '')
            doc_obj.category = flds.get('category', 'lecture_notes')
            if flds.get('file'):
                doc_obj.file = flds['file']
            doc_obj.uploaded_by = up_user
            doc_obj.save()
            synced_docs += 1
        except Exception as de:
            print(f"[WARN] LibraryDocument sync notice for id {doc.get('pk')}: {de}")

    # 9. Sync Assignments
    assignments_data = [x for x in items if x['model'] == 'students.assignment']
    synced_assignments = 0
    for a in assignments_data:
        try:
            flds = a['fields']
            aid = a.get('pk')
            cid = flds.get('course')
            course = Course.objects.filter(id=cid).first() if cid else None
            ass_obj, _ = Assignment.objects.get_or_create(id=aid)
            ass_obj.course = course
            ass_obj.title = flds.get('title', '')
            ass_obj.description = flds.get('description', '')
            if flds.get('file'):
                ass_obj.file = flds['file']
            ass_obj.due_date = flds.get('due_date')
            ass_obj.total_marks = flds.get('total_marks', 100) or 100
            ass_obj.pass_marks = flds.get('pass_marks', 40) or 40
            ass_obj.save()
            synced_assignments += 1
        except Exception as ae:
            print(f"[WARN] Assignment sync notice for id {a.get('pk')}: {ae}")

    # 10. Sync Enrollments
    enrollment_data = [x for x in items if x['model'] == 'students.enrollment']
    synced_enrollments = 0
    for en in enrollment_data:
        try:
            flds = en['fields']
            eid = en.get('pk')
            s_val = flds.get('student')
            s_user = User.objects.filter(username=s_val[0]).first() if isinstance(s_val, list) else User.objects.filter(pk=s_val).first()
            c_val = flds.get('course')
            course = Course.objects.filter(pk=c_val).first() if c_val else None
            if s_user and course:
                enr_obj, _ = Enrollment.objects.get_or_create(student=s_user, course=course)
                enr_obj.progress = flds.get('progress', 0) or 0
                enr_obj.is_completed = flds.get('is_completed', False)
                enr_obj.save()
                synced_enrollments += 1
        except Exception as ene:
            print(f"[WARN] Enrollment sync notice for id {en.get('pk')}: {ene}")

    reset_postgres_sequences()

    return {
        "status": "success",
        "synced_users": synced_users,
        "synced_profiles": synced_profiles,
        "synced_faculty_profiles": synced_faculty,
        "active_faculty_users": User.objects.filter(is_faculty=True).count(),
        "synced_courses": synced_courses,
        "synced_lessons": synced_lessons,
        "synced_live_classes": synced_classes,
        "synced_exams": synced_exams,
        "synced_documents": synced_docs,
        "synced_assignments": synced_assignments,
        "synced_enrollments": synced_enrollments,
    }

def seed():
    force = '--force' in sys.argv or os.getenv('FORCE_SEED', '').lower() in ('1', 'true', 'yes')
    faculty_count = User.objects.filter(is_faculty=True).count()
    has_courses = Course.objects.exists()

    if faculty_count >= 10 and has_courses and not force:
        print(f"[SAFEGUARD] Database already contains active faculty ({faculty_count}) and courses.")
        reset_postgres_sequences()
        return

    print(f"[INFO] Running resilient production sync from mydata.json...")
    res = smart_sync_production(force=force)
    print(f"[SUCCESS] Result: {res}")

if __name__ == '__main__':
    seed()
