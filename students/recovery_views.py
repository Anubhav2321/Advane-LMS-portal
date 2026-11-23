import json
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import (
    User, Course, Enrollment, Assignment, Exam, QuizResult,
    Notification, StudentActivity, AcademicAppeal, StudentStudyLeave,
    FacultyMentorshipSession, log_student_activity
)


# ========================================================
# 🙋 1. STUDENT ACADEMIC APPEAL & ASSISTANCE REQUESTS
# ========================================================

@login_required
def submit_academic_appeal(request):
    """
    Allows a student to submit a formal Academic Appeal or Grace Request
    explaining genuine difficulties (medical, technical, family, exams)
    and requesting grace time, mentorship, or course pause.
    """
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        appeal_type = request.POST.get('appeal_type', 'medical')
        requested_relief = request.POST.get('requested_relief', 'grace_extension')
        message = request.POST.get('message', '').strip()
        supporting_doc = request.FILES.get('supporting_document')

        course = get_object_or_404(Course, id=course_id) if course_id else None
        if not course:
            msg = "Please select the relevant course for your appeal."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('dashboard')

        if not message:
            msg = "Please provide an explanation describing your situation."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('course_watch', course_id=course.id)

        appeal = AcademicAppeal.objects.create(
            student=request.user,
            course=course,
            appeal_type=appeal_type,
            requested_relief=requested_relief,
            message=message,
            supporting_document=supporting_doc,
            status='pending'
        )

        # Notify Course Assigned Faculty
        faculty_user = course.assigned_faculty
        student_name = request.user.get_full_name() or request.user.username
        notif_msg = (
            f"Student {student_name} submitted an academic appeal for '{course.title}' "
            f"requesting {appeal.get_requested_relief_display()} due to {appeal.get_appeal_type_display()}. "
            f"Explanation: \"{message[:140]}...\""
        )

        if faculty_user:
            try:
                Notification.objects.create(
                    recipient=faculty_user,
                    is_global=False,
                    title=f"📩 Academic Appeal: {student_name} ({course.title})",
                    message=notif_msg,
                    notification_type='system',
                    action_url=f"/admin-panel/students/{request.user.id}/?appeal_id={appeal.id}#appeals",
                    action_label="Review & Grant Grace"
                )
            except Exception:
                pass

        # Notify all System Administrators
        admin_users = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).distinct()
        for admin in admin_users:
            try:
                Notification.objects.create(
                    recipient=admin,
                    is_global=False,
                    title=f"📩 Academic Appeal: {student_name} ({course.title})",
                    message=notif_msg,
                    notification_type='system',
                    action_url=f"/admin-panel/students/{request.user.id}/?appeal_id={appeal.id}#appeals",
                    action_label="Review & Grant Grace"
                )
            except Exception:
                pass

        # Log Activity
        log_student_activity(
            request.user,
            'chat_message',
            f"Submitted academic assistance appeal for {course.title}: {appeal.get_requested_relief_display()}.",
            course=course
        )

        success_msg = "Your academic appeal has been submitted successfully! The course faculty and administration have been notified to review your request."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg, 'appeal_id': appeal.id})

        messages.success(request, success_msg)
        return redirect('course_watch', course_id=course.id)

    return redirect('dashboard')


# ========================================================
# 🏖️ 2. STUDENT PLANNED STUDY LEAVE / PAUSE
# ========================================================

@login_required
def apply_study_leave(request):
    """
    Allows a student to apply for a planned study leave (e.g., hospitalization, surgery,
    board exam preparation, remote travel). When approved, study streak is frozen and
    inactive penalties are halted.
    """
    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        reason = request.POST.get('reason', 'medical')
        explanation = request.POST.get('explanation', '').strip()
        supporting_doc = request.FILES.get('supporting_doc')

        if not (start_date_str and end_date_str and explanation):
            msg = "Please provide start date, end date, and an explanation for your leave request."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('dashboard')

        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            msg = "Invalid date format. Please use YYYY-MM-DD."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('dashboard')

        if end_date < start_date:
            msg = "Leave end date cannot be earlier than start date."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('dashboard')

        days_count = (end_date - start_date).days + 1
        if days_count > 45:
            msg = "Study leave duration cannot exceed 45 consecutive days. For longer leaves, contact administration directly."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect('dashboard')

        leave = StudentStudyLeave.objects.create(
            student=request.user,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            explanation=explanation,
            supporting_doc=supporting_doc,
            status='pending'
        )

        student_name = request.user.get_full_name() or request.user.username
        notif_msg = (
            f"Student {student_name} requested a {days_count}-day Study Leave "
            f"({start_date.strftime('%d %b')} to {end_date.strftime('%d %b, %Y')}) for {leave.get_reason_display()}. "
            f"Reason: \"{explanation[:140]}...\""
        )

        # Notify Admins
        for admin in User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).distinct():
            try:
                Notification.objects.create(
                    recipient=admin,
                    is_global=False,
                    title=f"🏖️ Study Leave Application: {student_name}",
                    message=notif_msg,
                    notification_type='system',
                    action_url=f"/admin-panel/students/{request.user.id}/#leave-requests",
                    action_label="Review Leave"
                )
            except Exception:
                pass

        # Notify Course Faculties to schedule a 1-on-1 Mentorship session
        try:
            enrolled_courses = Course.objects.filter(enrollments__student=request.user).select_related('assigned_faculty').distinct()
            alerted_faculties = set()
            for c in enrolled_courses:
                fac = c.assigned_faculty
                if fac and fac != request.user and fac.id not in alerted_faculties:
                    alerted_faculties.add(fac.id)
                    Notification.objects.create(
                        recipient=fac,
                        is_global=False,
                        title=f"🏖️ Study Leave Alert: {student_name} ({c.title})",
                        message=(
                            f"Student {student_name} has taken a {days_count}-day Study Leave "
                            f"({start_date.strftime('%d %b')} to {end_date.strftime('%d %b, %Y')}). Reason: {leave.get_reason_display()}.\n"
                            f"As their course instructor, please schedule a 1-on-1 Mentorship class to guide their study plan and catch-up."
                        ),
                        notification_type='system',
                        action_url="/faculty/dashboard/#tab-mentorship",
                        action_label="Schedule Mentorship Class"
                    )
        except Exception as fac_err:
            print(f"[Warning] Failed to notify faculties of study leave: {fac_err}")

        success_msg = f"Your study leave request for {days_count} days ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b, %Y')}) has been submitted for administrative review."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg, 'leave_id': leave.id})

        messages.success(request, success_msg)
        return redirect('dashboard')

    return redirect('dashboard')


# ========================================================
# ⏸️ 3. STUDENT COURSE HOLD ACKNOWLEDGMENT
# ========================================================

@login_required
def acknowledge_course_hold(request, course_id):
    """
    When an enrollment is placed on hold by administration due to zero response,
    the student can click 'Acknowledge & Resume Coursework' to restore normal access.
    """
    enrollment = get_object_or_404(Enrollment, student=request.user, course_id=course_id)
    if request.method == 'POST':
        enrollment.is_on_hold = False
        enrollment.hold_reason = ""
        enrollment.save(update_fields=['is_on_hold', 'hold_reason'])

        log_student_activity(
            request.user,
            'lesson_watch',
            f"Acknowledged academic inactivity notice and resumed active participation in '{enrollment.course.title}'.",
            course=enrollment.course
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': "Access restored."})

        try:
            messages.success(request, f"Welcome back! Your access to '{enrollment.course.title}' has been restored. Happy learning!")
        except Exception:
            pass
        return redirect('course_watch', course_id=course_id)

    return redirect('course_watch', course_id=course_id)


# ========================================================
# ✨ 4. ADMIN & FACULTY: GRANT GRACE EXTENSION
# ========================================================

@staff_member_required
def admin_grant_grace_period(request, student_id, course_id):
    """
    Enables Administrators or Course Faculty to grant a 3, 5, 7, or 14-day grace extension
    to a student for a specific course. Re-opens past-due assignments and exams without penalties.
    """
    student = get_object_or_404(User, id=student_id)
    course = get_object_or_404(Course, id=course_id)
    enrollment = get_object_or_404(Enrollment, student=student, course=course)

    if request.method == 'POST':
        days = int(request.POST.get('days', 5))
        forgive_penalty = request.POST.get('forgive_penalty', 'true') == 'true'
        admin_notes = request.POST.get('admin_notes', '').strip()
        appeal_id = request.POST.get('appeal_id')

        now = timezone.now()
        new_deadline = now + datetime.timedelta(days=days)

        enrollment.grace_period_until = new_deadline
        enrollment.is_on_hold = False
        enrollment.hold_reason = ""
        enrollment.save(update_fields=['grace_period_until', 'is_on_hold', 'hold_reason'])

        # Forgive reputation penalty if selected
        if forgive_penalty and student.reputation_score < 100:
            student.reputation_score = min(100, student.reputation_score + 25)
            student.save(update_fields=['reputation_score'])

        # If connected to an appeal, mark it approved
        if appeal_id and appeal_id.isdigit():
            appeal = AcademicAppeal.objects.filter(id=int(appeal_id), student=student).first()
            if appeal:
                appeal.status = 'approved'
                appeal.resolved_by = request.user
                appeal.resolved_at = now
                appeal.admin_notes = admin_notes or f"Granted {days}-day grace extension."
                appeal.save()

        # Send encouraging, celebratory notification to student
        formatted_date = new_deadline.strftime('%d %b, %Y • %I:%M %p')
        Notification.objects.create(
            recipient=student,
            is_global=False,
            title=f"🎉 Grace Extension Granted: {course.title}",
            message=(
                f"Great news, {student.first_name or student.username}! The Academic Faculty & Administration "
                f"have approved an extension for '{course.title}'. You have been granted a {days}-day grace window "
                f"(valid until {formatted_date}). All expired assignments and module quizzes are temporarily re-opened. "
                f"Your reputation is safeguarded. We're here to help you succeed!"
            ),
            notification_type='notice',
            action_url=f"/courses/watch/{course.id}/",
            action_label="Open Course Workspace"
        )

        # Log Activity
        log_student_activity(
            student,
            'reputation_reward',
            f"Granted {days}-day academic grace extension by {request.user.username} in {course.title}.",
            course=course
        )

        success_msg = f"{days}-day grace extension successfully granted to {student.full_name} for '{course.title}' (until {new_deadline.strftime('%d %b, %Y')})."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg, 'grace_until': formatted_date})

        messages.success(request, success_msg)
        return redirect('admin_student_detail', user_id=student.id)

    return redirect('admin_student_detail', user_id=student.id)


# ========================================================
# 🤝 5. FACULTY & ADMIN: SCHEDULE 1-ON-1 MENTORSHIP CALL
# ========================================================

@login_required
def faculty_schedule_mentorship(request, student_id=None):
    """
    Schedules an official 1-on-1 counseling, mentorship, or doubt-clearing session
    conducted by Faculty (or Admins) with a live Google Meet / Zoom meeting link.
    """
    if not (getattr(request.user, 'is_faculty', False) or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access restricted to faculty members and administrators.")
        return redirect('dashboard')

    target_student_id = student_id or request.POST.get('student_id')
    student = get_object_or_404(User, id=target_student_id)

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if not next_url:
        next_url = f"/admin-panel/students/{student.id}/" if request.user.is_staff else "/faculty/dashboard/#tab-mentorship"

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        topic = request.POST.get('topic', '1-on-1 Academic Counseling & Guidance').strip()
        meeting_link = request.POST.get('meeting_link', '').strip()
        meeting_time_str = request.POST.get('meeting_time')
        notes = request.POST.get('notes', '').strip()
        appeal_id = request.POST.get('appeal_id')

        course = Course.objects.filter(id=course_id).first() if course_id else None

        if not meeting_link or not meeting_time_str:
            msg = "Please provide both the meeting link and the scheduled date/time."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg}, status=400)
            messages.error(request, msg)
            return redirect(next_url)

        try:
            meeting_time = timezone.make_aware(datetime.datetime.strptime(meeting_time_str, '%Y-%m-%dT%H:%M'))
        except Exception:
            meeting_time = timezone.now() + datetime.timedelta(days=1)

        session = FacultyMentorshipSession.objects.create(
            student=student,
            faculty_or_admin=request.user,
            course=course,
            topic=topic,
            meeting_link=meeting_link,
            meeting_time=meeting_time,
            notes=notes,
            status='scheduled'
        )

        # If linked to an appeal, mark as counseled
        if appeal_id and str(appeal_id).isdigit():
            appeal = AcademicAppeal.objects.filter(id=int(appeal_id), student=student).first()
            if appeal:
                appeal.status = 'counseled'
                appeal.resolved_by = request.user
                appeal.resolved_at = timezone.now()
                appeal.admin_notes = f"Scheduled 1-on-1 Mentorship session with Faculty {request.user.get_full_name() or request.user.username} for {meeting_time.strftime('%d %b, %Y %I:%M %p')}."
                appeal.save()

        # Send high-priority notification to student with one-click Join link
        mentor_name = request.user.get_full_name() or request.user.username
        formatted_dt = meeting_time.strftime('%d %b, %Y at %I:%M %p')
        Notification.objects.create(
            recipient=student,
            is_global=False,
            title=f"🤝 1-on-1 Faculty Mentorship: {topic}",
            message=(
                f"Hello {student.first_name or student.username}! Faculty Instructor {mentor_name} has scheduled a personalized "
                f"1-on-1 mentorship session for you on {formatted_dt} ({course.title if course else 'Academic Counseling'}).\n"
                f"Topic: {topic}\n"
                f"Meeting Link: {meeting_link}\n"
                f"Instructor Note: {notes or 'Looking forward to clearing your doubts and getting your coursework back on track!'}"
            ),
            notification_type='live_class',
            action_url=meeting_link,
            action_label="Join Mentorship Class"
        )

        # Log Activity
        log_student_activity(
            student,
            'lesson_watch',
            f"1-on-1 mentorship session scheduled by {request.user.username} for {formatted_dt}.",
            course=course
        )

        success_msg = f"1-on-1 mentorship session successfully scheduled with {student.get_full_name() or student.username} for {formatted_dt}!"
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': success_msg, 'session_id': session.id})

        messages.success(request, success_msg)
        return redirect(next_url)

    return redirect(next_url)


def admin_schedule_mentorship(request, student_id):
    """
    Backwards-compatible wrapper delegating to faculty_schedule_mentorship.
    """
    return faculty_schedule_mentorship(request, student_id)


# ========================================================
# ⏸️ 6. ADMIN & FACULTY: TOGGLE COURSE HOLD
# ========================================================

@staff_member_required
def admin_toggle_course_hold(request, student_id, course_id):
    """
    Places a course on temporary hold (Level 3 Warning Action) or restores active status.
    """
    student = get_object_or_404(User, id=student_id)
    course = get_object_or_404(Course, id=course_id)
    enrollment = get_object_or_404(Enrollment, student=student, course=course)

    if request.method == 'POST':
        action = request.POST.get('action', 'toggle')
        reason = request.POST.get('reason', 'Academic inactivity review pending').strip()

        if action == 'hold' or (action == 'toggle' and not enrollment.is_on_hold):
            enrollment.is_on_hold = True
            enrollment.hold_reason = reason
            enrollment.save(update_fields=['is_on_hold', 'hold_reason'])

            Notification.objects.create(
                recipient=student,
                is_global=False,
                title=f"⚠️ Course Access on Hold: {course.title}",
                message=(
                    f"Notice: Course access to '{course.title}' has been temporarily placed on hold by administration "
                    f"due to zero recorded participation. Please submit an academic appeal or confirm your resumption of studies."
                ),
                notification_type='notice',
                action_url=f"/courses/watch/{course.id}/",
                action_label="Review Course Status"
            )
            msg = f"Course '{course.title}' placed on hold for {student.full_name}."
        else:
            enrollment.is_on_hold = False
            enrollment.hold_reason = ""
            enrollment.save(update_fields=['is_on_hold', 'hold_reason'])

            Notification.objects.create(
                recipient=student,
                is_global=False,
                title=f"✅ Course Access Restored: {course.title}",
                message=f"Access to '{course.title}' has been fully restored by administration. You may now continue your coursework.",
                notification_type='notice',
                action_url=f"/courses/watch/{course.id}/",
                action_label="Go to Course"
            )
            msg = f"Course access restored for {student.full_name} in '{course.title}'."

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg, 'is_on_hold': enrollment.is_on_hold})

        messages.success(request, msg)
        return redirect('admin_student_detail', user_id=student.id)

    return redirect('admin_student_detail', user_id=student.id)


# ========================================================
# 📋 7. ADMIN REVIEW STUDY LEAVES & APPEALS
# ========================================================

@staff_member_required
def admin_review_study_leave(request, leave_id):
    """
    Allows admin or faculty to approve or decline a student's study leave request.
    """
    leave = get_object_or_404(StudentStudyLeave, id=leave_id)
    if request.method == 'POST':
        action = request.POST.get('action', 'approve')
        admin_response = request.POST.get('admin_response', '').strip()

        if action == 'approve':
            leave.status = 'approved'
            leave.reviewed_by = request.user
            leave.admin_response = admin_response or "Approved. Daily streak and deadlines are safeguarded during your leave."
            leave.save()

            Notification.objects.create(
                recipient=leave.student,
                is_global=False,
                title=f"🏖️ Study Leave Approved ({leave.start_date.strftime('%d %b')} - {leave.end_date.strftime('%d %b, %Y')})",
                message=(
                    f"Your requested study leave has been officially APPROVED by {request.user.username}. "
                    f"During this period, your study streak will stay protected and you will not be penalized for missed deadlines. "
                    f"Take good care!"
                ),
                notification_type='notice',
                action_url="/dashboard/",
                action_label="Open Dashboard"
            )
            msg = f"Study leave approved for {leave.student.full_name}."
        else:
            leave.status = 'rejected'
            leave.reviewed_by = request.user
            leave.admin_response = admin_response or "Leave request declined by administration."
            leave.save()

            Notification.objects.create(
                recipient=leave.student,
                is_global=False,
                title="Study Leave Request Declined",
                message=f"Your study leave request could not be approved at this time. Note: {leave.admin_response}",
                notification_type='notice',
                action_url="/dashboard/",
                action_label="Open Dashboard"
            )
            msg = f"Study leave declined for {leave.student.full_name}."

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg, 'status': leave.status})

        messages.success(request, msg)
        return redirect('admin_student_detail', user_id=leave.student.id)

    return redirect('admin_student_detail', user_id=leave.student.id)


@staff_member_required
def admin_review_appeal(request, appeal_id):
    """
    Allows admin or faculty to approve or decline an academic appeal with custom feedback.
    """
    appeal = get_object_or_404(AcademicAppeal, id=appeal_id)
    if request.method == 'POST':
        status = request.POST.get('status', 'approved')
        admin_notes = request.POST.get('admin_notes', '').strip()

        appeal.status = status
        appeal.resolved_by = request.user
        appeal.resolved_at = timezone.now()
        appeal.admin_notes = admin_notes
        appeal.save()

        status_label = "Approved" if status == 'approved' else ("Declined" if status == 'rejected' else "Counseled")
        Notification.objects.create(
            recipient=appeal.student,
            is_global=False,
            title=f"Academic Appeal Update: {status_label} ({appeal.course.title})",
            message=f"Your academic appeal for '{appeal.course.title}' has been reviewed ({status_label}). Feedback: {admin_notes or 'Your request has been addressed.'}",
            notification_type='notice',
            action_url=f"/courses/watch/{appeal.course.id}/",
            action_label="Open Course"
        )

        msg = f"Appeal #{appeal.id} updated to {status_label}."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': msg, 'status': status})

        messages.success(request, msg)
        return redirect('admin_student_detail', user_id=appeal.student.id)

    return redirect('admin_student_detail', user_id=appeal.student.id)
