from django.db import migrations
import random

def backfill_student_ids(apps, schema_editor):
    User = apps.get_model('students', 'User')
    Profile = apps.get_model('students', 'Profile')

    existing_ids = set(
        User.objects.exclude(student_id__isnull=True)
                    .exclude(student_id='')
                    .values_list('student_id', flat=True)
    )
    existing_ids.update(
        Profile.objects.exclude(student_id__isnull=True)
                       .exclude(student_id='')
                       .values_list('student_id', flat=True)
    )

    def get_candidate():
        for _ in range(10000):
            c = str(random.randint(100000, 999999))
            if c not in existing_ids:
                existing_ids.add(c)
                return c
        import time
        return str(int(time.time()))[-6:]

    for user in User.objects.all():
        if user.is_staff or user.is_superuser:
            continue
        # If user is student or normal account
        if not user.student_id:
            profile = Profile.objects.filter(user=user).first()
            if profile and profile.student_id:
                user_sid = profile.student_id
            else:
                user_sid = get_candidate()
            user.student_id = user_sid
            User.objects.filter(pk=user.pk).update(student_id=user_sid)
            if profile:
                Profile.objects.filter(pk=profile.pk).update(student_id=user_sid)
            else:
                Profile.objects.create(user=user, student_id=user_sid)
        else:
            profile = Profile.objects.filter(user=user).first()
            if profile and not profile.student_id:
                Profile.objects.filter(pk=profile.pk).update(student_id=user.student_id)
            elif not profile:
                Profile.objects.create(user=user, student_id=user.student_id)

def reverse_backfill(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('students', '0020_supportticketmessage'),
    ]

    operations = [
        migrations.RunPython(backfill_student_ids, reverse_backfill),
    ]
