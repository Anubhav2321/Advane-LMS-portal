import os
import uuid
import subprocess
import json
import datetime
import time
import re  
import requests 
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q, Avg, Count, Sum, F
from django.db.models.functions import TruncDate
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator

# Import AI Logic
from .ai_utils import extract_text_from_file, generate_quiz_from_text
# Import the powerful AI Service
from .ai_service import generate_learning_assistant_response

# Import Forms
from .forms import (
    StudentRegistrationForm,
    CourseForm,
    NotificationForm,
    LibraryDocumentForm,
    LiveClassForm,
    ExamForm,
    ProfilePictureForm,
    LessonForm,
    LessonCommentForm,
)

# Import Models
from .models import (
    Course,
    Enrollment,
    Notification,
    LiveClass,
    LibraryDocument,
    Exam,
    Profile,
    Lesson,
    Quiz, 
    Question,
    QuizResult,
    LessonComment,
    DynamicBountyProblem,  
    ProblemTestCase,       
    BountySubmission,
    Assignment,            #  NEW: Added Assignment Model
    AssignmentSubmission,  #  NEW: Added Assignment Submission Model
    StudentActivity,       #  NEW: Student Activity Tracking
    log_student_activity,  #  NEW: Activity Logging Helper
    LessonProgress,        #  NEW: Per-Student Lesson Tracking
    DocumentView,          #  NEW: Document Tracking
    LiveClassAttendance,   #  NEW: Live Class Tracking
    process_and_clarify_avatar, #  NEW: Super-clear photo optimization
    AIVideoNote,           #  NEW: Smart AI Lesson Notes
)

User = get_user_model()

# 1. PUBLIC VIEWS (LANDING, CONTACT)

def home_view(request):
    """
    Renders the Landing Page with stats.
    """
    featured_courses = Course.objects.filter(is_published=True).order_by('-created_at')[:6]
    total_students = User.objects.filter(is_student=True, is_staff=False, is_superuser=False).count()
    total_courses_count = Course.objects.count()
    total_exams = Exam.objects.count()
    total_documents = LibraryDocument.objects.count()
    total_live_classes = LiveClass.objects.count()
    
    context = {
        'featured_courses': featured_courses,
        'total_students': total_students,
        'total_courses_count': total_courses_count,
        'total_exams': total_exams,
        'total_documents': total_documents,
        'total_live_classes': total_live_classes,
        'year': timezone.now().year,
    }
    return render(request, 'landing.html', context)

def contact_developers_view(request):
    """
    Renders Contact Page & Handles Form Submission.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        # Here you would integrate SendGrid or SMTP logic
        messages.success(request, f"Thank you {name}, we have received your message and will reply to {email} shortly.")
        return redirect('contact_developers')
        
    return render(request, 'contact.html')

# 2. AUTHENTICATION (REGISTER, LOGIN, LOGOUT)

def register_view(request):
    """
    Handles Student Registration.
    """
    if request.user.is_authenticated:
        messages.success(request, "You are already logged in.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created successfully for {user.first_name}! Please login.")
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'register.html', {'form': form})


def login_view(request):
    """
    Handles User Login.
    """
    if request.user.is_authenticated:
        messages.success(request, "You are already logged in.")
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        # ROUTING: Redirect Faculty to their dashboard
        elif getattr(request.user, 'is_faculty', False):
            return redirect('faculty_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        # Try authenticating as Username (Email in backend)
        user = authenticate(request, username=identifier, password=password)
        
        # Fallback: try finding user by Email explicitly
        if user is None:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name}!")
            
            # Log student login activity
            log_student_activity(user, 'login', f'{user.username} logged in')
            
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            # ROUTING: Redirect Faculty to their dashboard
            elif getattr(user, 'is_faculty', False):
                return redirect('faculty_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid Credentials! Please check your email and password.")

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.error(request, "You have been logged out successfully.")
    return redirect('login')

# 3. STUDENT DASHBOARD & PROFILE FEATURES

@login_required
def student_dashboard(request):
    """
    Main Student Dashboard with 3-Panel Sync Logic + Real Progress Tracking.
    """
    user = request.user
    if user.is_staff or user.is_superuser:
        return redirect('admin_dashboard')
    elif getattr(user, 'is_faculty', False):
        return redirect('faculty_dashboard')
    
    # Fetch Enrollments
    enrollments = Enrollment.objects.filter(student=user).select_related('course').order_by('-last_accessed')
    
    #  NEW: Get IDs of courses the student is enrolled in
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    
    # --- REAL PROGRESS CALCULATIONS ---
    # Attach real progress data to each enrollment for the template
    enriched_enrollments = []
    total_all_lessons = 0
    total_completed_lessons = 0
    
    for enrollment in enrollments:
        progress_data = enrollment.get_real_progress()
        enrollment.real_progress = progress_data['percent']
        enrollment.lessons_completed = progress_data['completed']
        enrollment.total_lessons = progress_data['total']
        enrollment.lessons_remaining = progress_data['total'] - progress_data['completed']
        enrollment.ring_offset = round(163.36 - (enrollment.real_progress / 100.0) * 163.36, 2)
        
        # Sync the progress field with real data
        if abs(enrollment.progress - progress_data['percent']) > 0.5:
            enrollment.progress = progress_data['percent']
            if progress_data['percent'] >= 100.0:
                enrollment.is_completed = True
            enrollment.save(update_fields=['progress', 'is_completed'])
        
        # --- GRANULAR COMPLETED COUNTS (for clickable chips) ---
        # Lessons: count completed LessonProgress records
        enrollment.total_lessons_count = enrollment.course.lessons.count()
        enrollment.completed_lessons_count = LessonProgress.objects.filter(
            student=user, lesson__course=enrollment.course, is_completed=True
        ).count()
        
        # Quizzes: total active quizzes vs attempted
        enrollment.total_quizzes_count = Exam.objects.filter(
            course=enrollment.course, is_active=True
        ).count()
        enrollment.completed_quizzes_count = QuizResult.objects.filter(
            student=user, exam__course=enrollment.course
        ).count()
        
        # Tasks (Assignments): total vs submitted
        enrollment.total_tasks_count = Assignment.objects.filter(
            course=enrollment.course
        ).count()
        enrollment.completed_tasks_count = AssignmentSubmission.objects.filter(
            student=user, assignment__course=enrollment.course
        ).count()

        # Legacy fields (kept for backward compatibility)
        enrollment.quiz_count = enrollment.completed_quizzes_count
        enrollment.assignment_count = enrollment.completed_tasks_count
        
        # Course slug for navigation links
        enrollment.course_slug = enrollment.course.slug
        
        # Faculty profile data for display
        if enrollment.course.assigned_faculty:
            try:
                enrollment.faculty_user = enrollment.course.assigned_faculty
            except Exception:
                enrollment.faculty_user = None
        else:
            enrollment.faculty_user = None
        
        total_all_lessons += progress_data['total']
        total_completed_lessons += progress_data['completed']
        
        enriched_enrollments.append(enrollment)
    
    # Overall progress across all courses
    overall_progress = round((total_completed_lessons / max(total_all_lessons, 1)) * 100, 1)
    
    # Fetch Notifications
    notifications = Notification.objects.all().order_by('-created_at')[:5]
    
    # Calculate Stats
    total_enrolled = enrollments.count()
    completed_courses = enrollments.filter(progress__gte=100).count()
    certificate_eligible = completed_courses
    
    #  GLOBAL LEADERBOARD LOGIC
    top_students = User.objects.filter(is_student=True, is_staff=False, is_superuser=False).select_related('profile').order_by('-lms_coins')[:10]
    
    #  3-PANEL SYNC LOGIC (FETCHING FACULTY DATA)
    
    # 1. Fetch Pending Assignments for enrolled courses
    pending_assignments = Assignment.objects.filter(
        course_id__in=enrolled_course_ids
    ).exclude(
        submissions__student=user
    ).order_by('due_date')[:5]
    
    # 2. Fetch Upcoming Live Classes for enrolled courses
    upcoming_classes = LiveClass.objects.filter(
        course_id__in=enrolled_course_ids,
        date_time__gte=timezone.now()
    ).order_by('date_time')[:5]
    
    # 3. Fetch Active Exams for enrolled courses
    active_exams = Exam.objects.filter(
        course_id__in=enrolled_course_ids,
        is_active=True
    ).exclude(
        quizresult__student=user
    ).order_by('-created_at')[:5]
    
    # 4. Fetch Recent Digital Archive/Library Documents
    recent_documents = LibraryDocument.objects.filter(
        course_id__in=enrolled_course_ids
    ).order_by('-uploaded_at')[:5]
    
    # --- LEARNING ANALYTICS DATA ---
    today = timezone.now().date()
    fourteen_days_ago = today - datetime.timedelta(days=14)
    
    # Weekly activity data (last 14 days)
    weekly_activity = (
        StudentActivity.objects.filter(student=user, created_at__date__gte=fourteen_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    activity_labels = []
    activity_data = []
    for entry in weekly_activity:
        activity_labels.append(entry['date'].strftime('%d %b'))
        activity_data.append(entry['count'])
    
    if not activity_labels:
        for i in range(6, -1, -1):
            d = today - datetime.timedelta(days=i)
            activity_labels.append(d.strftime('%d %b'))
            activity_data.append(0)
    
    # Course progress comparison data for bar chart
    course_progress_labels = []
    course_progress_data = []
    for e in enriched_enrollments:
        course_progress_labels.append(e.course.title[:25])
        course_progress_data.append(e.real_progress)
    
    # Quiz performance trend
    recent_quizzes = QuizResult.objects.filter(student=user).order_by('taken_at')[:20]
    quiz_labels = []
    quiz_data = []
    for qr in recent_quizzes:
        quiz_labels.append(qr.taken_at.strftime('%d %b'))
        pct = int((qr.score / max(qr.total_marks, 1)) * 100) if qr.total_marks else 0
        quiz_data.append(pct)
    
    # Average quiz score
    avg_quiz_score = QuizResult.objects.filter(student=user).aggregate(avg=Avg('score'))['avg']
    avg_quiz_score = round(avg_quiz_score, 1) if avg_quiz_score else 0
    
    # Study streak (consecutive days with at least 1 activity)
    study_streak = 0
    check_date = today
    while True:
        has_activity = StudentActivity.objects.filter(
            student=user, created_at__date=check_date
        ).exists()
        if has_activity:
            study_streak += 1
            check_date -= datetime.timedelta(days=1)
        else:
            break
        if study_streak > 365:
            break
    
    context = {
        'enrollments': enriched_enrollments,
        'notifications': notifications,
        'total_enrolled': total_enrolled,
        'completed_courses': completed_courses,
        'certificate_eligible': certificate_eligible,
        'overall_progress': overall_progress,
        'total_all_lessons': total_all_lessons,
        'total_completed_lessons': total_completed_lessons,
        'top_students': top_students,
        'user': user,
        
        # Learning Analytics (JSON for charts)
        'activity_labels': json.dumps(activity_labels),
        'activity_data': json.dumps(activity_data),
        'course_progress_labels': json.dumps(course_progress_labels),
        'course_progress_data': json.dumps(course_progress_data),
        'quiz_labels': json.dumps(quiz_labels),
        'quiz_data': json.dumps(quiz_data),
        'avg_quiz_score': avg_quiz_score,
        'study_streak': study_streak,
        
        # 3-Panel Sync Data
        'pending_assignments': pending_assignments,
        'upcoming_classes': upcoming_classes,
        'active_exams': active_exams,
        'recent_documents': recent_documents,
    }
    return render(request, 'student_dashboard.html', context)


@login_required
def profile_view(request):
    """
    Student Profile View.
    """
    user = request.user
    
    # Ensure profile object exists
    if not hasattr(user, 'profile'):
        Profile.objects.create(user=user)
    
    # Handle Profile Picture Upload
    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated successfully!")
            return redirect('profile')
    else:
        form = ProfilePictureForm(instance=user.profile)

    # Fetch Enrolled Courses for display
    enrollments = Enrollment.objects.filter(student=user).select_related('course').order_by('-enrolled_at')

    # 🚀 SYNTAX SINGULARITY STATS & GITHUB HEATMAP GRAPH FETCHING

    successful_bounties = BountySubmission.objects.filter(
        student=user, 
        earned_coins__gt=0
    ).select_related('problem').order_by('submitted_at') # ordered ascending for graph
    
    total_bounties_solved = successful_bounties.count()
    bounty_coins_earned = sum(sub.earned_coins for sub in successful_bounties)
    
    # For recent list (descending)
    recent_bounties = BountySubmission.objects.filter(
        student=user, earned_coins__gt=0
    ).select_related('problem').order_by('-submitted_at')[:5]

    # 📊 GRAPH DATA LOGIC (Dictionary of date -> count)
    contribution_data = {}
    for sub in successful_bounties:
        date_str = sub.submitted_at.strftime('%Y-%m-%d')
        contribution_data[date_str] = contribution_data.get(date_str, 0) + 1

    # --- TOP STATS LOGIC FOR PROFILE ---
    today = timezone.now().date()
    
    # Calculate study streak
    study_streak = 0
    check_date = today
    while True:
        has_activity = StudentActivity.objects.filter(
            student=user, created_at__date=check_date
        ).exists()
        if has_activity:
            study_streak += 1
            check_date -= datetime.timedelta(days=1)
        else:
            break
        if study_streak > 365:
            break

    # Calculate lessons done & overall progress
    total_all_lessons = 0
    total_completed_lessons = 0
    for enrollment in enrollments:
        progress_data = enrollment.get_real_progress()
        total_all_lessons += progress_data['total']
        total_completed_lessons += progress_data['completed']
        
    overall_progress = round((total_completed_lessons / max(total_all_lessons, 1)) * 100, 1)
    
    # Average quiz score
    avg_quiz_score = QuizResult.objects.filter(student=user).aggregate(avg=Avg('score'))['avg']
    avg_quiz_score = round(avg_quiz_score, 1) if avg_quiz_score else 0

    total_enrolled = enrollments.count()

    context = {
        'user': user,
        'form': form,
        'enrollments': enrollments,
        'total_bounties_solved': total_bounties_solved,
        'bounty_coins_earned': bounty_coins_earned,
        'recent_bounties': recent_bounties,
        'contribution_json': json.dumps(contribution_data), # <-- Sent to Template for Heatmap Graph
        'study_streak': study_streak,
        'total_completed_lessons': total_completed_lessons,
        'avg_quiz_score': avg_quiz_score,
        'overall_progress': overall_progress,
        'total_enrolled': total_enrolled,
    }
    return render(request, 'student_profile.html', context)

# 4. COURSE & LEARNING LOGIC

@login_required
def all_courses(request):
    """
    Course Store: server-side search, filter (paid/free/coin), sort and pagination.
    Also tells the template which courses the student already owns.
    """
    query = request.GET.get('search', '').strip()
    flt = request.GET.get('filter', 'all')
    sort = request.GET.get('sort', 'default')

    courses_list = Course.objects.filter(is_published=True)

    if query:
        courses_list = courses_list.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(difficulty_level__icontains=query)
        )

    if flt == 'free':
        courses_list = courses_list.filter(price__lte=0)
    elif flt == 'paid':
        courses_list = courses_list.filter(price__gt=0)
    elif flt == 'coin':
        courses_list = courses_list.filter(is_coin_purchasable=True, coin_price__gt=0)
    else:
        flt = 'all'

    sort_map = {
        'low': 'price',
        'high': '-price',
        'az': 'title',
    }
    courses_list = courses_list.order_by(sort_map.get(sort, '-created_at'))
    if sort not in sort_map:
        sort = 'default'

    paginator = Paginator(courses_list, 6)
    courses = paginator.get_page(request.GET.get('page'))

    enrolled_ids = set(
        Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    )

    context = {
        'courses': courses,
        'search_query': query,
        'active_filter': flt,
        'active_sort': sort,
        'enrolled_ids': enrolled_ids,
        'total_results': paginator.count,
        'user_coins': request.user.lms_coins,
    }
    return render(request, 'student_courses.html', context)


@login_required
def enroll_course(request, course_id):
    """
    Handles Course Enrollment logic.
    """
    course = get_object_or_404(Course, id=course_id)
    student = request.user
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=student, course=course).exists():
        messages.info(request, "You are already enrolled!")
        return redirect('dashboard')

    # Payment Check
    if course.price > 0:
        return redirect('payment_page', course_id=course.id)
    
    # Free Course Enrollment
    Enrollment.objects.create(student=student, course=course)
    log_student_activity(student, 'course_enroll', f'Enrolled in {course.title}', course=course)
    messages.success(request, f"Successfully enrolled in {course.title}!")
    return redirect('dashboard')


# ---------------------------------------------------------------
# PAYMENT SYSTEM (server-side validation, coupons, ledger, receipts)
# ---------------------------------------------------------------
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.views.decorators.http import require_POST
from .models import Payment, Coupon

ALLOWED_PROVIDERS = {
    'card': {'visa', 'mastercard', 'amex', 'rupay', 'card'},
    'upi': {'gpay', 'phonepe', 'paytm', 'bhim', 'upi'},
    'wallet': {'paytm', 'amazon', 'phonepe', 'mobikwik'},
    'qr': {'qr'},
    'net': set(),
}
ALLOWED_BANKS = {
    'State Bank of India', 'HDFC Bank', 'ICICI Bank', 'Axis Bank', 'Kotak Mahindra Bank',
    'Punjab National Bank', 'Bank of Baroda', 'Canara Bank', 'Union Bank of India',
    'Yes Bank', 'IndusInd Bank', 'IDFC FIRST Bank', 'Bank of India',
}
UPI_REGEX = re.compile(r'^[\w.\-]{2,}@[A-Za-z]{2,}$')


def _money(value):
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _luhn_ok(number):
    total, alt = 0, False
    for ch in reversed(number):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return len(number) >= 13 and total % 10 == 0


def _detect_card_brand(number):
    if number.startswith('4'):
        return 'visa'
    if re.match(r'^(5[1-5]|2[2-7])', number):
        return 'mastercard'
    if re.match(r'^3[47]', number):
        return 'amex'
    if re.match(r'^(60|65|81|82|508)', number):
        return 'rupay'
    return 'card'


def _price_breakdown(course, coupon=None):
    """Single source of truth for amounts - the frontend only displays what this returns."""
    original = _money(course.price)
    discount = _money(0)
    if coupon and coupon.is_valid():
        discount = _money(original * coupon.percent_off / 100)
    final = max(original - discount, _money(0))
    return original, discount, final


def _get_valid_coupon(code):
    code = (code or '').strip().upper()
    if not code:
        return None
    coupon = Coupon.objects.filter(code=code).first()
    return coupon if coupon and coupon.is_valid() else None


def _wants_json(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def _pay_fail(request, course, message, status=400):
    if _wants_json(request):
        return JsonResponse({'ok': False, 'error': message}, status=status)
    messages.error(request, message)
    return redirect('payment_page', course_id=course.id)


@login_required
def payment_page(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)

    if Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.info(request, "You already own this course.")
        return redirect('course_watch', course_id=course.id)

    if course.price <= 0:
        return redirect('enroll_course', course_id=course.id)

    context = {
        'course': course,
        'user_coins': request.user.lms_coins,
        'can_afford_coins': course.is_coin_purchasable and request.user.lms_coins >= course.coin_price,
        'banks': sorted(ALLOWED_BANKS),
    }
    return render(request, 'payment.html', context)


@login_required
@require_POST
def validate_coupon(request, course_id):
    """AJAX: returns the server-computed price after applying a coupon."""
    course = get_object_or_404(Course, id=course_id)
    code = request.POST.get('code', '')
    coupon = _get_valid_coupon(code)
    original, discount, final = _price_breakdown(course, coupon)
    if not coupon:
        return JsonResponse({
            'ok': False, 'error': 'Invalid or expired coupon code.',
            'original': str(original), 'discount': '0.00', 'final': str(original),
        })
    return JsonResponse({
        'ok': True, 'code': coupon.code, 'percent': coupon.percent_off,
        'original': str(original), 'discount': str(discount), 'final': str(final),
    })


@login_required
@require_POST
def process_payment(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    user = request.user

    if Enrollment.objects.filter(student=user, course=course).exists():
        return _pay_fail(request, course, "You already own this course.")
    if course.price <= 0:
        return _pay_fail(request, course, "This course is free - use Enroll instead.")

    method = request.POST.get('method', '')
    provider = request.POST.get('provider', method).lower()
    if method not in ALLOWED_PROVIDERS:
        return _pay_fail(request, course, "Invalid payment method.")

    instrument = ''

    # ---- per-method server-side validation ----
    if method == 'card':
        number = re.sub(r'\D', '', request.POST.get('card_number', ''))
        expiry = request.POST.get('card_expiry', '').strip()
        cvv = request.POST.get('card_cvv', '').strip()
        holder = request.POST.get('card_name', '').strip()

        if not _luhn_ok(number):
            return _pay_fail(request, course, "Invalid card number.")
        m = re.match(r'^(\d{2})/(\d{2})$', expiry)
        if not m or not (1 <= int(m.group(1)) <= 12):
            return _pay_fail(request, course, "Invalid expiry date.")
        now = timezone.now()
        yy, mm = now.year % 100, now.month
        if int(m.group(2)) < yy or (int(m.group(2)) == yy and int(m.group(1)) < mm):
            return _pay_fail(request, course, "This card has expired.")
        brand = _detect_card_brand(number)
        if not re.match(r'^\d{4}$' if brand == 'amex' else r'^\d{3}$', cvv):
            return _pay_fail(request, course, "Invalid CVV.")
        if len(holder) < 2:
            return _pay_fail(request, course, "Enter the card holder name.")
        provider = brand
        instrument = f"{brand.title()} \u2022\u2022\u2022\u2022 {number[-4:]}"   # only last 4 digits are ever stored

    elif method == 'upi':
        upi_id = request.POST.get('upi_id', '').strip()
        if upi_id:
            if not UPI_REGEX.match(upi_id):
                return _pay_fail(request, course, "Invalid UPI ID.")
            instrument = upi_id
        elif provider not in ALLOWED_PROVIDERS['upi']:
            return _pay_fail(request, course, "Select a UPI app or enter a UPI ID.")
        if provider not in ALLOWED_PROVIDERS['upi']:
            provider = 'upi'

    elif method == 'net':
        bank = request.POST.get('bank', '').strip()
        if bank not in ALLOWED_BANKS:
            return _pay_fail(request, course, "Please select a valid bank.")
        provider = bank.split()[0].lower()
        instrument = bank

    elif method == 'wallet':
        if provider not in ALLOWED_PROVIDERS['wallet']:
            return _pay_fail(request, course, "Select a valid wallet.")
        instrument = provider.title() + " Wallet"

    elif method == 'qr':
        provider = 'qr'
        instrument = 'UPI QR'

    # ---- pricing (always recomputed on the server) ----
    coupon = _get_valid_coupon(request.POST.get('coupon_code', ''))
    original, discount, final = _price_breakdown(course, coupon)

    with transaction.atomic():
        # race-safe duplicate guard
        if Enrollment.objects.select_for_update().filter(student=user, course=course).exists():
            return _pay_fail(request, course, "You already own this course.")

        if coupon:
            locked = Coupon.objects.select_for_update().get(pk=coupon.pk)
            if not locked.is_valid():
                return _pay_fail(request, course, "This coupon is no longer valid.")
            locked.used_count += 1
            locked.save(update_fields=['used_count'])

        payment = Payment.objects.create(
            student=user, course=course, method=method, provider=provider,
            instrument=instrument, original_amount=original,
            discount_amount=discount, amount_paid=final,
            coupon=coupon, status='success',
        )
        Enrollment.objects.create(student=user, course=course)

    log_student_activity(
        user, 'course_enroll', f'Paid and enrolled in {course.title}', course=course,
        metadata={'txn_id': payment.txn_id, 'method': method, 'amount': str(final)},
    )

    receipt_url = reverse('payment_receipt', args=[payment.txn_id])
    if _wants_json(request):
        return JsonResponse({
            'ok': True, 'txn_id': payment.txn_id, 'amount': str(final),
            'redirect': receipt_url,
        })
    messages.success(request, f"Payment Successful! Welcome to {course.title}.")
    return redirect(receipt_url)


@login_required
@require_POST
def purchase_with_coins(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    user = request.user

    if Enrollment.objects.filter(student=user, course=course).exists():
        return _pay_fail(request, course, "You already own this course.")
    if not course.is_coin_purchasable or course.coin_price <= 0:
        return _pay_fail(request, course, "This course cannot be purchased with coins.")

    required = course.coin_price

    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        if locked_user.lms_coins < required:
            return _pay_fail(
                request, course,
                f"Insufficient coins! You need {required - locked_user.lms_coins} more."
            )
        locked_user.lms_coins -= required
        locked_user.save(update_fields=['lms_coins'])

        payment = Payment.objects.create(
            student=user, course=course, method='coins', provider='lms_coins',
            instrument=f"{required} LMS Coins", original_amount=_money(course.price),
            discount_amount=_money(0), amount_paid=_money(0),
            coins_spent=required, status='success',
        )
        Enrollment.objects.create(student=user, course=course)

    log_student_activity(
        user, 'course_enroll', f'Purchased {course.title} with {required} coins', course=course,
        metadata={'txn_id': payment.txn_id, 'method': 'coins', 'coins': required},
    )

    receipt_url = reverse('payment_receipt', args=[payment.txn_id])
    if _wants_json(request):
        return JsonResponse({'ok': True, 'txn_id': payment.txn_id, 'coins': required, 'redirect': receipt_url})
    messages.success(request, f"Course Unlocked! You purchased '{course.title}' using {required} LMS Coins.")
    return redirect(receipt_url)


@login_required
def payment_receipt(request, txn_id):
    payment = get_object_or_404(Payment, txn_id=txn_id, student=request.user)
    return render(request, 'payment_receipt.html', {'payment': payment, 'course': payment.course})


@login_required
def payment_history(request):
    payments = Payment.objects.filter(student=request.user).select_related('course')
    total_spent = payments.filter(status='success').aggregate(s=Sum('amount_paid'))['s'] or 0
    total_coins = payments.filter(status='success').aggregate(s=Sum('coins_spent'))['s'] or 0
    return render(request, 'payment_history.html', {
        'payments': payments, 'total_spent': total_spent, 'total_coins': total_coins,
    })



# --- COURSE WATCH ---
@login_required
def course_watch(request, course_id, lesson_id=None):
    """
    Course Player logic with YouTube/Video File playback, Comment System,
    Real-Time Progress Tracking, AI Notes, and Curriculum Playlist.
    """
    course = get_object_or_404(Course, id=course_id)
    
    # Security Check: Must be enrolled or staff/faculty/superuser
    is_admin_or_faculty = request.user.is_staff or request.user.is_superuser or request.user.is_faculty
    try:
        enrollment = Enrollment.objects.get(student=request.user, course=course)
    except Enrollment.DoesNotExist:
        if is_admin_or_faculty:
            enrollment, _ = Enrollment.objects.get_or_create(student=request.user, course=course)
        else:
            messages.warning(request, "You must enroll in this course to access the content.")
            return redirect('all_courses')

    # Update Last Accessed Time
    enrollment.last_accessed = timezone.now()
    enrollment.save(update_fields=['last_accessed'])

    lessons = course.lessons.all().order_by('order')
    
    current_lesson = None
    next_lesson = None
    prev_lesson = None
    youtube_id = None

    if lessons.exists():
        if lesson_id:
            current_lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
        else:
            # Smart resume: pick the first uncompleted lesson, or the first lesson
            completed_ids = set(
                LessonProgress.objects.filter(
                    student=request.user, lesson__course=course, is_completed=True
                ).values_list('lesson_id', flat=True)
            )
            uncompleted = [l for l in lessons if l.id not in completed_ids]
            current_lesson = uncompleted[0] if uncompleted else lessons.first()
            
        # Logic for Next/Prev buttons
        lesson_list = list(lessons)
        try:
            idx = lesson_list.index(current_lesson)
            if idx > 0:
                prev_lesson = lesson_list[idx - 1]
            if idx < len(lesson_list) - 1:
                next_lesson = lesson_list[idx + 1]
            
            # --- PER-LESSON PROGRESS RECORD ---
            lesson_progress, _ = LessonProgress.objects.get_or_create(
                student=request.user,
                lesson=current_lesson
            )

            # --- YOUTUBE ID EXTRACTION ---
            if current_lesson.video_url:
                url = current_lesson.video_url.strip()
                regex = r'(?:v=|\/embed\/|\/v\/|youtu\.be\/|shorts\/)([0-9A-Za-z_-]{11})'
                match = re.search(regex, url)
                if match:
                    youtube_id = match.group(1)
                elif len(url) == 11:
                    youtube_id = url # Direct 11-char ID

        except ValueError:
            pass

    # --- COMMENT SYSTEM LOGIC ---
    comments = current_lesson.comments.all().select_related('student', 'student__profile').order_by('-created_at') if current_lesson else []
    comment_form = LessonCommentForm()

    if request.method == 'POST' and 'text' in request.POST:
        comment_form = LessonCommentForm(request.POST)
        if comment_form.is_valid() and current_lesson:
            comment = comment_form.save(commit=False)
            comment.lesson = current_lesson
            comment.student = request.user
            comment.save()
            log_student_activity(request.user, 'chat_message', f'Commented on "{current_lesson.title}"', course=course)
            messages.success(request, "Comment posted successfully!")
            return redirect('course_watch', course_id=course.id, lesson_id=current_lesson.id)

    # Calculate real progress from enrollment
    progress_data = enrollment.get_real_progress()
    progress_int = int(progress_data['percent'])
    
    # Completed lesson IDs
    completed_lesson_ids = set(
        LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course,
            is_completed=True
        ).values_list('lesson_id', flat=True)
    )
    
    # --- PER-LESSON PROGRESS MAP ---
    lesson_progress_map = {}
    all_lesson_progress = LessonProgress.objects.filter(
        student=request.user,
        lesson__course=course
    ).select_related('lesson')
    
    for lp in all_lesson_progress:
        required_time = lp.lesson.duration_in_seconds * 0.8
        if lp.is_completed:
            lesson_percent = 100
        elif required_time > 0 and lp.watch_time_seconds > 0:
            lesson_percent = min(100, int((lp.watch_time_seconds / required_time) * 100))
        else:
            lesson_percent = 0
        lesson_progress_map[lp.lesson_id] = {
            'percent': lesson_percent,
            'watch_time': lp.watch_time_seconds,
            'is_completed': lp.is_completed,
        }

    # Total duration formatted
    total_seconds = sum(l.duration_in_seconds for l in lessons)
    if total_seconds >= 3600:
        total_duration_str = f"{total_seconds // 3600}h {(total_seconds % 3600) // 60}m"
    elif total_seconds >= 60:
        total_duration_str = f"{total_seconds // 60}m"
    else:
        total_duration_str = f"{len(lessons)} Lessons"
    
    # --- FACULTY DATA ENRICHMENT ---
    faculty_user = course.assigned_faculty
    faculty_data = {
        'name': faculty_user.full_name if faculty_user else course.faculty_name,
        'department': getattr(getattr(faculty_user, 'faculty_profile', None), 'department', '') if faculty_user else '',
        'specialization': getattr(getattr(faculty_user, 'faculty_profile', None), 'specialization', '') if faculty_user else '',
        'experience': getattr(getattr(faculty_user, 'faculty_profile', None), 'experience_years', 0) if faculty_user else 0,
        'has_pic': bool(faculty_user and faculty_user.profile_pic_url),
        'pic_url': faculty_user.profile_pic_url if (faculty_user and faculty_user.profile_pic_url) else '',
    }
        
    documents = course.documents.all().order_by('-uploaded_at')
    course_exams = Exam.objects.filter(course=course, is_active=True).order_by('-created_at')
    course_assignments = Assignment.objects.filter(course=course).order_by('-due_date')
    
    # Check completed exams and assignments by current student
    passed_exam_ids = set(
        QuizResult.objects.filter(student=request.user, exam__course=course).values_list('exam_id', flat=True)
    )
    submitted_assignment_ids = set(
        AssignmentSubmission.objects.filter(student=request.user, assignment__course=course).values_list('assignment_id', flat=True)
    )

    # Current lesson AI notes if already generated
    current_ai_note = None
    if current_lesson:
        current_ai_note = AIVideoNote.objects.filter(student=request.user, lesson=current_lesson).first()

    # Current lesson progress
    current_lesson_progress = None
    if current_lesson:
        current_lesson_progress = lesson_progress_map.get(current_lesson.id, {
            'percent': 100 if current_lesson.id in completed_lesson_ids else 0,
            'is_completed': current_lesson.id in completed_lesson_ids,
            'watch_time': 0,
        })

    context = {
        'course': course,
        'lessons': lessons,
        'current_lesson': current_lesson,
        'next_lesson': next_lesson,
        'prev_lesson': prev_lesson,
        'progress': progress_int,
        'progress_data': progress_data,
        'completed_lesson_ids': completed_lesson_ids,
        'completed_lessons_count': len(completed_lesson_ids),
        'total_lessons_count': lessons.count(),
        'total_duration_str': total_duration_str,
        'lesson_progress_map': json.dumps(lesson_progress_map),
        'current_lesson_progress': current_lesson_progress,
        'youtube_id': youtube_id,
        'comments': comments,          
        'comment_form': comment_form,
        'documents': documents,
        'faculty_data': faculty_data,
        'course_exams': course_exams,
        'course_assignments': course_assignments,
        'passed_exam_ids': passed_exam_ids,
        'submitted_assignment_ids': submitted_assignment_ids,
        'current_ai_note': current_ai_note,
    }
    return render(request, 'course_watch.html', context)


# --- AI LESSON NOTES API ---
@login_required
@csrf_exempt
def lesson_ai_notes(request, lesson_id):
    """
    Real-time AI Smart Notes & Key Takeaways Generator.
    Powered by Groq AI & backed by AIVideoNote model.
    """
    lesson = get_object_or_404(Lesson, id=lesson_id)
    is_enrolled = Enrollment.objects.filter(student=request.user, course=lesson.course).exists()
    if not is_enrolled and not (request.user.is_staff or request.user.is_superuser or request.user.is_faculty):
        return JsonResponse({'status': 'error', 'message': 'Enrollment required'}, status=403)
        
    if request.method == 'GET':
        ai_note = AIVideoNote.objects.filter(student=request.user, lesson=lesson).first()
        if ai_note:
            return JsonResponse({
                'status': 'success',
                'has_notes': True,
                'summary': ai_note.summary,
                'key_points': ai_note.key_points,
                'generated_at': ai_note.generated_at.strftime('%b %d, %Y %I:%M %p')
            })
        return JsonResponse({'status': 'success', 'has_notes': False})
        
    elif request.method == 'POST':
        try:
            body = json.loads(request.body) if request.body else {}
        except Exception:
            body = {}
        action = body.get('action', 'generate')
        
        if action == 'generate':
            from .ai_utils import generate_ai_lesson_notes
            data = generate_ai_lesson_notes(
                lesson_title=lesson.title,
                lesson_content=lesson.content or '',
                course_title=lesson.course.title
            )
            ai_note, _ = AIVideoNote.objects.update_or_create(
                student=request.user,
                lesson=lesson,
                defaults={
                    'summary': data['summary'],
                    'key_points': data['key_points'],
                }
            )
            log_student_activity(request.user, 'code_review', f'Generated AI Notes for "{lesson.title}"', course=lesson.course)
            return JsonResponse({
                'status': 'success',
                'has_notes': True,
                'summary': ai_note.summary,
                'key_points': ai_note.key_points,
                'generated_at': ai_note.generated_at.strftime('%b %d, %Y %I:%M %p')
            })
        elif action == 'save_custom':
            summary = body.get('summary', '').strip()
            key_points = body.get('key_points', '').strip()
            if not summary and not key_points:
                return JsonResponse({'status': 'error', 'message': 'Notes content cannot be empty'}, status=400)
            ai_note, _ = AIVideoNote.objects.update_or_create(
                student=request.user,
                lesson=lesson,
                defaults={
                    'summary': summary or "Personal Study Notes",
                    'key_points': key_points,
                }
            )
            return JsonResponse({
                'status': 'success',
                'has_notes': True,
                'summary': ai_note.summary,
                'key_points': ai_note.key_points,
                'generated_at': ai_note.generated_at.strftime('%b %d, %Y %I:%M %p')
            })
            
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)



@login_required
def live_classes(request):
    """
    Live Classes View: Filtered STRICTLY by Enrolled Courses
    """
    now = timezone.now()
    
    # 1. Get IDs of courses the student is enrolled in
    enrolled_course_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    
    # 2. Filter Live Classes belonging ONLY to these courses
    classes = LiveClass.objects.filter(
        course__id__in=enrolled_course_ids,
        date_time__gte=now - datetime.timedelta(hours=1)
    ).order_by('date_time')
    
    return render(request, 'student_classes.html', {'classes': classes})


@login_required
def library_view(request):
    """
    Library View: Filtered STRICTLY by Enrolled Courses
    """
    # 1. Get IDs of courses the student is enrolled in
    enrolled_course_ids = Enrollment.objects.filter(student=request.user).values_list('course_id', flat=True)
    
    # 2. Filter documents belonging ONLY to these courses
    documents = LibraryDocument.objects.filter(
        course__id__in=enrolled_course_ids
    ).order_by('-uploaded_at')
    
    query = request.GET.get('search')
    if query:
        documents = documents.filter(title__icontains=query)

    return render(request, 'student_library.html', {'documents': documents})

# 5. QUIZ, EXAMS & AI CHAT

@login_required
def student_exam_list(request):
    """
    Shows Active Exams AND Exam History/Results.
    """
    # 1. Get IDs of courses the student is enrolled in
    enrolled_courses = Enrollment.objects.filter(student=request.user).values_list('course', flat=True)
    
    # 2. Filter exams: ONLY those linked to enrolled courses (Active Exams)
    available_exams = Exam.objects.filter(
        course__in=enrolled_courses, 
        is_active=True
    ).order_by('-created_at')

    # 3. Fetch History/Results
    past_results = QuizResult.objects.filter(student=request.user).select_related('exam').order_by('-taken_at')

    context = {
        'exams': available_exams,
        'results': past_results
    }
    return render(request, 'exam_list.html', context) 

@login_required
def take_exam(request, exam_id):
    """
    Exam Taking Page with Enrolled Check.
    """
    exam = get_object_or_404(Exam, id=exam_id)
    
    # 1. If exam is linked to a course, check enrollment
    if exam.course:
        is_enrolled = Enrollment.objects.filter(student=request.user, course=exam.course).exists()
        if not is_enrolled:
            messages.error(request, 'You must enroll in this course to take the exam.')
            return redirect('dashboard')

    # 2. Render exam page
    context = {
        'exam': exam,
        'questions': exam.questions.all()
    }
    return render(request, 'take_quiz.html', context)


@login_required
def exams_view(request):
    return student_exam_list(request)


@login_required
def generate_quiz_view(request):
    """
    AI Quiz Generator (From Documents).
    """
    if request.method == "POST":
        try:
            # 1. Capture doc_id
            doc_id = request.POST.get('doc_id')
            if not doc_id:
                return JsonResponse({'status': 'error', 'message': 'No document selected!'}, status=400)

            # 2. Find document
            document = get_object_or_404(LibraryDocument, id=doc_id)
            if not document.file:
                return JsonResponse({'status': 'error', 'message': 'File not found on server.'}, status=404)

            # 3. Extract text
            file_path = document.file.path
            extracted_text = extract_text_from_file(file_path)
            
            if len(extracted_text) < 50:
                return JsonResponse({'status': 'error', 'message': 'File is empty or unreadable.'}, status=400)

            # 4. Generate Questions via AI
            generated_questions = generate_quiz_from_text(extracted_text, num_questions=5)
            
            if not generated_questions:
                return JsonResponse({'status': 'error', 'message': 'AI could not generate questions. Please try again.'}, status=500)

            # 5. Transform AI format to frontend format
            # AI returns: {"question": "...", "options": ["A","B","C","D"], "answer": 0}
            # Frontend expects: {"question_text": "...", "option_a": "...", ..., "correct_option": "A"}
            option_letters = ['A', 'B', 'C', 'D']
            formatted_questions = []
            for q in generated_questions:
                opts = q.get('options', [])
                correct_idx = q.get('answer', 0)
                formatted_q = {
                    'question_text': q.get('question', ''),
                    'option_a': opts[0] if len(opts) > 0 else '-',
                    'option_b': opts[1] if len(opts) > 1 else '-',
                    'option_c': opts[2] if len(opts) > 2 else '-',
                    'option_d': opts[3] if len(opts) > 3 else '-',
                    'correct_option': option_letters[correct_idx] if correct_idx < len(option_letters) else 'A',
                    # Keep original format too for save_quiz_view
                    'question': q.get('question', ''),
                    'options': opts,
                    'answer': correct_idx,
                }
                formatted_questions.append(formatted_q)
            
            return JsonResponse({'status': 'success', 'quiz': formatted_questions})

        except Exception as e:
            print(f"Error generating quiz: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)


@login_required
def save_quiz_view(request):
    """
    Saves the AI Generated Quiz AND Links it to a Course.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            title = data.get('title', 'AI Generated Quiz')
            questions = data.get('questions', [])
            course_id = data.get('course_id')
            
            course_obj = None
            if course_id:
                course_obj = get_object_or_404(Course, id=course_id)

            exam = Exam.objects.create(
                title=title,
                course=course_obj,
                description="Generated by AI Assistant",
                duration_minutes=20, 
                is_active=True,
                total_marks=len(questions)
            )
            
            for q in questions:
                opts = q.get('options', [])
                correct_idx = q.get('answer', 0)
                
                Question.objects.create(
                    exam=exam,
                    question_text=q.get('question'),
                    option1=opts[0] if len(opts) > 0 else "-",
                    option2=opts[1] if len(opts) > 1 else "-",
                    option3=opts[2] if len(opts) > 2 else "-",
                    option4=opts[3] if len(opts) > 3 else "-",
                    correct_option=opts[correct_idx] 
                )
                
            return JsonResponse({'status': 'success', 'message': 'Quiz Saved Successfully!'})
            
        except Exception as e:
            print(f"Error saving quiz: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def take_quiz_view(request, exam_id):
    return take_exam(request, exam_id)


@login_required
def submit_quiz_view(request, exam_id):
    """
    Handles Quiz Submission, Grading, and Result Storage.
    """
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == "POST":
        score = 0
        total_questions = exam.questions.count()
        user_answers = {}
        
        for question in exam.questions.all():
            selected_option = request.POST.get(f'q_{question.id}')
            
            if selected_option == question.correct_option:
                score += 1
            
            user_answers[question.id] = {
                'question': question.question_text,
                'selected': selected_option,
                'correct': question.correct_option,
                'is_correct': (selected_option == question.correct_option)
            }

        # Save Result
        try:
            QuizResult.objects.create(
                student=request.user,
                exam=exam,
                score=score,
                total_marks=total_questions
            )
        except TypeError:
             # Fallback
             QuizResult.objects.create(
                student=request.user,
                exam=exam,
                score=score
            )
        
        # Log quiz activity
        log_student_activity(
            request.user, 'quiz_taken',
            f'Took quiz: {exam.title} - Score: {score}/{total_questions}',
            course=exam.course,
            metadata={'score': score, 'total': total_questions}
        )
        
        percentage = int((score / total_questions) * 100) if total_questions > 0 else 0
        
        # --- LMS COIN REWARD SYSTEM (QUIZ SCORE) ---

        if percentage >= 80:
            # Check if they have previously scored 80%+ on this specific exam
            past_success_count = QuizResult.objects.filter(
                student=request.user, 
                exam=exam, 
                score__gte=(total_questions * 0.8)
            ).count()
            
            if past_success_count == 1:
                request.user.lms_coins += 100
                request.user.save(update_fields=['lms_coins'])
                messages.success(request, "Excellent! You scored 80%+ and earned 100 LMS Coins!")

        context = {
            'exam': exam,
            'score': score,
            'total': total_questions,
            'percentage': percentage,
            'user_answers': user_answers
        }
        return render(request, 'quiz_result.html', context)
        
    return redirect('dashboard')


@csrf_exempt
def ai_chat(request):
    """
    AI Chatbot Logic.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('question', '')
            history = data.get('history', [])

            ai_reply = generate_learning_assistant_response(user_message, history)

            return JsonResponse({'answer': ai_reply})
        except Exception as e:
            print(f"AI Service Error: {e}")
            return JsonResponse({'answer': "I am having trouble connecting to my brain right now."}, status=500)
            
    return JsonResponse({'error': "Invalid request"}, status=400)


#  6. PISTON API CODE EXECUTION ENGINE (Cloud-based, works on Render)

# Language configuration for Piston API
PISTON_LANGUAGES = {
    'python': {'language': 'python', 'version': '3.10.0'},
    'javascript': {'language': 'javascript', 'version': '18.15.0'},
    'cpp': {'language': 'c++', 'version': '10.2.0'},
    'java': {'language': 'java', 'version': '15.0.2'},
}

@csrf_exempt
def execute_code_api(request):
    """
    Cloud & Local Code Execution Engine.
    Executes in isolated sandbox with native support for Python, JavaScript, C++, and Java.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid Request. POST required.'}, status=405)
        
    try:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST

        language = (data.get('language') or 'python').strip().lower()
        code = data.get('code', '')
        user_input = data.get('user_input', '')
        
        if not code.strip():
            return JsonResponse({'status': 'error', 'message': 'Code cannot be empty.'})

        # Normalize language aliases
        lang_alias = {
            'py': 'python',
            'js': 'javascript',
            'node': 'javascript',
            'c++': 'cpp',
            'cplusplus': 'cpp'
        }
        language = lang_alias.get(language, language)

        from .compiler_service import execute_locally
        result = execute_locally(language, code, user_input)
        return JsonResponse({
            'status': result['status'],
            'output': result['output'],
            'execution_time': result.get('execution_time', '0.00s'),
            'language': language
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'output': f"Execution server error: {str(e)}", 
            'message': str(e)
        }, status=500)


# 7. ADMIN PANEL SYSTEM (FULL CREATE/DELETE LOGIC)

@staff_member_required
def admin_dashboard(request):
    """
    Admin Dashboard Logic with Analytics Data for Charts + Course Activity Tracker.
    """
    total_students = User.objects.filter(is_student=True, is_staff=False, is_superuser=False).count()
    total_courses = Course.objects.count()
    total_enrollments = Enrollment.objects.count()
    total_docs = LibraryDocument.objects.count()
    total_exams = Exam.objects.count()

    # Fetch Faculties
    total_faculties = User.objects.filter(is_faculty=True).count()
    faculties = User.objects.filter(is_faculty=True).order_by('-date_joined')

    courses = Course.objects.all().order_by('-created_at')
    documents = LibraryDocument.objects.all().order_by('-uploaded_at')
    
    # --- ANALYTICS DATA FOR CHARTS ---
    today = timezone.now().date()
    thirty_days_ago = today - datetime.timedelta(days=30)
    
    # Daily new student registrations (last 30 days)
    daily_registrations = (
        User.objects.filter(is_student=True, is_staff=False, is_superuser=False, date_joined__date__gte=thirty_days_ago)
        .annotate(date=TruncDate('date_joined'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    reg_labels = []
    reg_data = []
    for entry in daily_registrations:
        reg_labels.append(entry['date'].strftime('%d %b'))
        reg_data.append(entry['count'])
    
    # Daily activity counts (last 30 days)
    daily_activities = (
        StudentActivity.objects.filter(created_at__date__gte=thirty_days_ago, student__is_student=True, student__is_staff=False, student__is_superuser=False)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    activity_labels = []
    activity_data = []
    for entry in daily_activities:
        activity_labels.append(entry['date'].strftime('%d %b'))
        activity_data.append(entry['count'])
    
    # Activity type breakdown (pie chart)
    activity_breakdown = (
        StudentActivity.objects.filter(created_at__date__gte=thirty_days_ago, student__is_student=True, student__is_staff=False, student__is_superuser=False)
        .values('activity_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    breakdown_labels = []
    breakdown_data = []
    activity_type_map = dict(StudentActivity.ACTIVITY_TYPES)
    for entry in activity_breakdown:
        breakdown_labels.append(activity_type_map.get(entry['activity_type'], entry['activity_type']))
        breakdown_data.append(entry['count'])
    
    # Recent activities feed (latest 25)
    recent_activities = StudentActivity.objects.filter(student__is_student=True, student__is_staff=False, student__is_superuser=False).select_related('student', 'course').all()[:25]
    
    # Top active students (by activity count in last 30 days)
    top_students = (
        StudentActivity.objects.filter(created_at__date__gte=thirty_days_ago, student__is_student=True, student__is_staff=False, student__is_superuser=False)
        .values('student__id', 'student__username', 'student__first_name', 'student__last_name')
        .annotate(activity_count=Count('id'))
        .order_by('-activity_count')[:10]
    )
    
    # Total activities count
    total_activities = StudentActivity.objects.filter(student__is_student=True, student__is_staff=False, student__is_superuser=False).count()
    
    # --- COURSE ACTIVITY TRACKER DATA ---
    # Student list for dropdown (all students with enrollments)
    all_students = User.objects.filter(is_student=True, is_staff=False, is_superuser=False).order_by('first_name', 'username')
    
    # Course-wise enrollment analytics
    course_enrollment_data = []
    for course in courses[:15]:
        enroll_count = course.enrollments.count()
        avg_progress = course.enrollments.aggregate(avg=Avg('progress'))['avg'] or 0
        completed = course.enrollments.filter(is_completed=True).count()
        completion_rate = round((completed / max(enroll_count, 1)) * 100, 1)
        course_enrollment_data.append({
            'title': course.title[:30],
            'enrollments': enroll_count,
            'avg_progress': round(avg_progress, 1),
            'completion_rate': completion_rate,
        })
    
    # Course progress comparison chart data
    course_names = [c['title'] for c in course_enrollment_data]
    course_avg_progress = [c['avg_progress'] for c in course_enrollment_data]
    course_completion_rates = [c['completion_rate'] for c in course_enrollment_data]
    
    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'total_docs': total_docs,
        'total_faculties': total_faculties,
        'total_exams': total_exams,
        'total_activities': total_activities,
        'faculties': faculties,
        'courses': courses,
        'documents': documents,
        
        # Chart Data (serialized via json_script in template, so pass raw lists)
        'reg_labels': reg_labels,
        'reg_data': reg_data,
        'activity_labels': activity_labels,
        'activity_data': activity_data,
        'breakdown_labels': breakdown_labels,
        'breakdown_data': breakdown_data,
        
        # Course Analytics
        'course_names': course_names,
        'course_avg_progress': course_avg_progress,
        'course_completion_rates': course_completion_rates,
        
        # Student list for Activity Tracker dropdown
        'all_students': all_students,
        
        # Recent activity & top students
        'recent_activities': recent_activities,
        'top_students': top_students,
        
        # Forms
        'course_form': CourseForm(),
        'notice_form': NotificationForm(),
        'class_form': LiveClassForm(),
        'exam_form': ExamForm(),
        'library_form': LibraryDocumentForm(),
        'lesson_form': LessonForm(),
    }
    return render(request, 'custom_admin/dashboard.html', context)


@staff_member_required
def admin_student_courses_api(request, student_id):
    """
    JSON API: Returns the list of courses a specific student is enrolled in.
    """
    student = get_object_or_404(User, id=student_id)
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    courses_data = [{'id': e.course.id, 'title': e.course.title} for e in enrollments]
    return JsonResponse({'courses': courses_data})


# --- NEW: Admin Student Course Activity API ---
@staff_member_required
def admin_student_course_activity(request, student_id, course_id):
    """
    JSON API: Returns detailed activity data for a specific student in a specific course.
    Used by the admin "Course Activity Tracker" section via AJAX.
    """
    student = get_object_or_404(User, id=student_id)
    course = get_object_or_404(Course, id=course_id)
    
    # Check enrollment
    try:
        enrollment = Enrollment.objects.get(student=student, course=course)
    except Enrollment.DoesNotExist:
        return JsonResponse({'error': 'Student is not enrolled in this course'}, status=404)
    
    today = timezone.now().date()
    thirty_days_ago = today - datetime.timedelta(days=30)
    
    # 1. Daily activity for this student in this course (last 30 days)
    daily_data = (
        StudentActivity.objects.filter(
            student=student, course=course,
            created_at__date__gte=thirty_days_ago
        )
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    daily_labels = [e['date'].strftime('%d %b') for e in daily_data]
    daily_counts = [e['count'] for e in daily_data]
    
    # 2. Lesson progress
    total_lessons = course.lessons.count()
    completed_lessons = LessonProgress.objects.filter(
        student=student, lesson__course=course, is_completed=True
    ).count()
    progress_percent = round((completed_lessons / max(total_lessons, 1)) * 100, 1)
    
    # Lesson-by-lesson status
    lessons_status = []
    for lesson in course.lessons.all().order_by('order'):
        lp = LessonProgress.objects.filter(student=student, lesson=lesson).first()
        lessons_status.append({
            'title': lesson.title,
            'order': lesson.order,
            'completed': lp.is_completed if lp else False,
            'completed_at': lp.completed_at.strftime('%d %b %Y, %I:%M %p') if lp and lp.completed_at else None,
        })
    
    # 3. Quiz scores for this course
    quiz_results = QuizResult.objects.filter(
        student=student, exam__course=course
    ).order_by('taken_at')
    quiz_labels = []
    quiz_scores = []
    for qr in quiz_results:
        quiz_labels.append(qr.taken_at.strftime('%d %b'))
        pct = int((qr.score / max(qr.total_marks, 1)) * 100) if qr.total_marks else 0
        quiz_scores.append(pct)
    
    avg_quiz = quiz_results.aggregate(avg=Avg('score'))['avg']
    avg_quiz = round(avg_quiz, 1) if avg_quiz else 0
    
    # 4. Assignment submissions
    submissions = AssignmentSubmission.objects.filter(
        student=student, assignment__course=course
    )
    total_assignments = Assignment.objects.filter(course=course).count()
    submitted_assignments = submissions.count()
    graded_count = submissions.filter(is_graded=True).count()
    avg_marks = submissions.filter(is_graded=True).aggregate(avg=Avg('marks_obtained'))['avg']
    avg_marks = round(avg_marks, 1) if avg_marks else 0
    
    # 5. Activity type breakdown for this course
    type_breakdown = (
        StudentActivity.objects.filter(student=student, course=course)
        .values('activity_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    act_type_map = dict(StudentActivity.ACTIVITY_TYPES)
    type_labels = [act_type_map.get(e['activity_type'], e['activity_type']) for e in type_breakdown]
    type_data = [e['count'] for e in type_breakdown]
    
    # 6. Recent activities (last 20)
    recent = StudentActivity.objects.filter(
        student=student, course=course
    ).order_by('-created_at')[:20]
    recent_list = [{
        'type': act_type_map.get(a.activity_type, a.activity_type),
        'description': a.description or a.get_activity_type_display(),
        'time': a.created_at.strftime('%d %b %Y, %I:%M %p'),
        'icon': a.activity_type,
    } for a in recent]
    
    return JsonResponse({
        'student_name': student.full_name,
        'course_title': course.title,
        'enrolled_at': enrollment.enrolled_at.strftime('%d %b %Y'),
        'last_accessed': enrollment.last_accessed.strftime('%d %b %Y, %I:%M %p') if enrollment.last_accessed else 'N/A',
        
        # Progress
        'progress_percent': progress_percent,
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
        'lessons_status': lessons_status,
        
        # Daily activity chart
        'daily_labels': daily_labels,
        'daily_data': daily_counts,
        
        # Quiz data
        'quiz_labels': quiz_labels,
        'quiz_scores': quiz_scores,
        'avg_quiz_score': avg_quiz,
        'total_quizzes': quiz_results.count(),
        
        # Assignment data
        'total_assignments': total_assignments,
        'submitted_assignments': submitted_assignments,
        'graded_assignments': graded_count,
        'avg_assignment_marks': avg_marks,
        
        # Activity breakdown
        'type_labels': type_labels,
        'type_data': type_data,
        
        # Recent activities
        'recent_activities': recent_list,
    })


# --- Admin Action Views (Create) ---


@staff_member_required
def admin_create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"Course '{course.title}' created successfully!")
        else:
            messages.error(request, "Error creating course. Please check inputs.")
    return redirect('admin_dashboard')

@staff_member_required
def admin_create_notice(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification posted to all students.")
        else:
            messages.error(request, "Failed to post notice.")
    return redirect('admin_dashboard')

@staff_member_required
def admin_create_live_class(request):
    if request.method == 'POST':
        form = LiveClassForm(request.POST)
        if form.is_valid():
            live_class = form.save()
            messages.success(request, f"Live class '{live_class.title}' scheduled.")
        else:
            messages.error(request, "Invalid class details. Date cannot be in past.")
    return redirect('admin_dashboard')

@staff_member_required
def admin_create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            messages.success(request, f"Exam '{exam.title}' created.")
        else:
            messages.error(request, "Failed to create exam.")
    return redirect('admin_dashboard')

@staff_member_required
def add_library_view(request):
    if request.method == 'POST':
        form = LibraryDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.uploaded_by = request.user
            doc.save()
            messages.success(request, f"Document '{doc.title}' uploaded to library.")
        else:
            messages.error(request, "Upload failed. Check file type (PDF/Doc only).")
    return redirect('admin_dashboard')

@staff_member_required
def admin_add_lesson(request, course_id):
    """
    Renders a separate page to add a lesson.
    """
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course # Link to course
            lesson.save()
            messages.success(request, f"Lesson '{lesson.title}' added successfully!")
            return redirect('admin_course_list') # Redirect back to list
        else:
            messages.error(request, "Error adding lesson. Please check inputs.")
    else:
        form = LessonForm(initial={'course': course})
    
    return render(request, 'custom_admin/add_lesson.html', {'form': form, 'course': course})

# --- Admin Student Management Views ---

@staff_member_required
def admin_student_list(request):
    query = request.GET.get('search', '').strip()
    base_students = User.objects.filter(is_student=True, is_staff=False, is_superuser=False)
    if query:
        students = base_students.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query) | Q(username__icontains=query)
        )
    else:
        students = base_students.order_by('-date_joined')

    return render(request, 'custom_admin/student_list.html', {'students': students, 'search_query': query})

@staff_member_required
def admin_student_detail(request, user_id):
    student = get_object_or_404(User, id=user_id)
    if student.is_staff or student.is_superuser:
        messages.info(request, f"{student.full_name} is an administrator, not a student.")
        return redirect('admin_profile')
    enrollments = Enrollment.objects.filter(student=student).order_by('-enrolled_at')
    completed_courses = enrollments.filter(progress=100).count()
    quiz_results = QuizResult.objects.filter(student=student).order_by('-taken_at')
    avg_score = quiz_results.aggregate(Avg('score'))['score__avg']
    avg_score = round(avg_score, 1) if avg_score else 0
    
    # --- STUDENT ACTIVITY ANALYTICS ---
    today = timezone.now().date()
    thirty_days_ago = today - datetime.timedelta(days=30)
    
    # Per-student daily activity (last 30 days)
    student_daily_activity = (
        StudentActivity.objects.filter(student=student, created_at__date__gte=thirty_days_ago)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    stu_activity_labels = []
    stu_activity_data = []
    for entry in student_daily_activity:
        stu_activity_labels.append(entry['date'].strftime('%d %b'))
        stu_activity_data.append(entry['count'])
    
    # Activity type breakdown for this student
    stu_breakdown = (
        StudentActivity.objects.filter(student=student)
        .values('activity_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    stu_breakdown_labels = []
    stu_breakdown_data = []
    activity_type_map = dict(StudentActivity.ACTIVITY_TYPES)
    for entry in stu_breakdown:
        stu_breakdown_labels.append(activity_type_map.get(entry['activity_type'], entry['activity_type']))
        stu_breakdown_data.append(entry['count'])
    
    # Recent activities for this student (last 50)
    student_activities = StudentActivity.objects.filter(student=student).select_related('course')[:50]
    
    # Stats
    total_logins = StudentActivity.objects.filter(student=student, activity_type='login').count()
    total_lessons = StudentActivity.objects.filter(student=student, activity_type='lesson_watch').count()
    total_messages = StudentActivity.objects.filter(student=student, activity_type='chat_message').count()
    total_student_activities = StudentActivity.objects.filter(student=student).count()
    
    # Engagement score (simple formula: activities in last 30 days / 30 * 100, capped at 100)
    recent_count = StudentActivity.objects.filter(student=student, created_at__date__gte=thirty_days_ago).count()
    engagement_score = min(100, int((recent_count / max(30, 1)) * 100))
    
    # Quiz scores over time for chart
    quiz_score_labels = []
    quiz_score_data = []
    for qr in quiz_results[:20]:
        quiz_score_labels.append(qr.taken_at.strftime('%d %b'))
        pct = int((qr.score / max(qr.total_marks, 1)) * 100) if qr.total_marks else 0
        quiz_score_data.append(pct)
    quiz_score_labels.reverse()
    quiz_score_data.reverse()
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'completed_courses': completed_courses,
        'quiz_results': quiz_results,
        'avg_score': avg_score,
        'total_quizzes': quiz_results.count(),
        
        # Activity tracking data
        'student_activities': student_activities,
        'total_logins': total_logins,
        'total_lessons': total_lessons,
        'total_messages': total_messages,
        'total_student_activities': total_student_activities,
        'engagement_score': engagement_score,
        
        # Chart data (JSON)
        'stu_activity_labels': json.dumps(stu_activity_labels),
        'stu_activity_data': json.dumps(stu_activity_data),
        'stu_breakdown_labels': json.dumps(stu_breakdown_labels),
        'stu_breakdown_data': json.dumps(stu_breakdown_data),
        'quiz_score_labels': json.dumps(quiz_score_labels),
        'quiz_score_data': json.dumps(quiz_score_data),
    }
    return render(request, 'custom_admin/student_detail.html', context)

@staff_member_required
def admin_update_student_info(request, user_id):
    student = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        update_type = request.POST.get('update_type')

        if update_type == 'coins':
            # --- ONLY UPDATE COINS ---
            new_coins = request.POST.get('new_coins')
            if new_coins is not None:
                student.lms_coins = int(new_coins)
                student.save(update_fields=['lms_coins'])
                messages.success(request, f"Coin balance updated to {new_coins} for {student.username}.")
        else:
            # --- NORMAL PROFILE UPDATE ---
            student.first_name = request.POST.get('first_name', student.first_name)
            student.last_name = request.POST.get('last_name', student.last_name)
            student.email = request.POST.get('email', student.email)
            student.stream = request.POST.get('stream', student.stream)
            student.student_level = request.POST.get('student_level', student.student_level)
            student.save()
            
            phone = request.POST.get('phone')
            if phone:
                student.profile.phone = phone
                student.profile.save()
                
            messages.success(request, "Student information updated successfully.")
            
    return redirect('admin_student_detail', user_id=user_id)

@staff_member_required
def admin_toggle_block(request, user_id):
    student = get_object_or_404(User, id=user_id)
    student.is_active = not student.is_active
    student.save()
    status = "Active" if student.is_active else "Blocked"
    messages.warning(request, f"User {student.username} is now {status}.")
    return redirect('admin_student_detail', user_id=user_id)

@staff_member_required
def admin_delete_student(request, user_id):
    student = get_object_or_404(User, id=user_id)
    email = student.email
    student.delete()
    messages.error(request, f"Student {email} permanently deleted.")
    return redirect('admin_student_list')

@staff_member_required
def admin_reset_password(request, user_id):
    if request.method == "POST":
        new_pass = request.POST.get('new_password')
        if new_pass:
            student = get_object_or_404(User, id=user_id)
            student.set_password(new_pass)
            student.save()
            messages.success(request, f"Password reset for {student.username}.")
    return redirect('admin_student_detail', user_id=user_id)

# --- Admin Management (Courses, Docs, Enrollments) ---

@staff_member_required
def admin_course_list(request):
    courses = Course.objects.all().order_by('-created_at')
    context = {
        'courses': courses,
    }
    return render(request, 'custom_admin/course_list.html', context)

@staff_member_required
def admin_edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.title}' updated successfully!")
            return redirect('admin_course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'custom_admin/course_edit.html', {'form': form, 'course': course})

@staff_member_required
def admin_delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, "Course deleted successfully.")
    return redirect('admin_dashboard')

@staff_member_required
def admin_document_list(request):
    documents = LibraryDocument.objects.all().order_by('-uploaded_at')
    return render(request, 'custom_admin/document_list.html', {'documents': documents})

@staff_member_required
def admin_edit_document(request, doc_id):
    doc = get_object_or_404(LibraryDocument, id=doc_id)
    if request.method == 'POST':
        form = LibraryDocumentForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully!")
            return redirect('admin_document_list')
    else:
        form = LibraryDocumentForm(instance=doc)
    return render(request, 'custom_admin/document_edit.html', {'form': form, 'doc': doc})

@staff_member_required
def admin_delete_document(request, doc_id):
    doc = get_object_or_404(LibraryDocument, id=doc_id)
    doc.delete()
    messages.success(request, "Document deleted.")
    return redirect('admin_document_list')

@staff_member_required
def admin_enrollment_list(request):
    enrollments = Enrollment.objects.all().select_related('student', 'course').order_by('-enrolled_at')
    return render(request, 'custom_admin/enrollment_list.html', {'enrollments': enrollments})

@staff_member_required
def admin_delete_enrollment(request, enroll_id):
    enroll = get_object_or_404(Enrollment, id=enroll_id)
    enroll.delete()
    messages.success(request, "Enrollment removed.")
    return redirect('admin_enrollment_list')


# --- ADMIN ACTIVITY DATA API (For AJAX Charts) ---

@staff_member_required
def admin_activity_api(request):
    """
    JSON API endpoint for admin activity chart data.
    Supports filtering by student_id, days (range), and activity_type.
    """
    student_id = request.GET.get('student_id')
    days = int(request.GET.get('days', 30))
    activity_type = request.GET.get('type')
    
    today = timezone.now().date()
    start_date = today - datetime.timedelta(days=days)
    
    queryset = StudentActivity.objects.filter(created_at__date__gte=start_date)
    
    if student_id:
        queryset = queryset.filter(student_id=student_id)
    if activity_type:
        queryset = queryset.filter(activity_type=activity_type)
    
    # Daily counts
    daily_data = (
        queryset
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    
    labels = [entry['date'].strftime('%d %b') for entry in daily_data]
    data = [entry['count'] for entry in daily_data]
    
    # Type breakdown
    breakdown = (
        queryset
        .values('activity_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    activity_type_map = dict(StudentActivity.ACTIVITY_TYPES)
    breakdown_labels = [activity_type_map.get(e['activity_type'], e['activity_type']) for e in breakdown]
    breakdown_data = [e['count'] for e in breakdown]
    
    return JsonResponse({
        'labels': labels,
        'data': data,
        'breakdown_labels': breakdown_labels,
        'breakdown_data': breakdown_data,
        'total': queryset.count()
    })


@staff_member_required
def admin_profile(request):
    """
    Admin Profile Management:
    - View and update current admin's profile details, avatar, and password.
    - Add/Create new admin accounts with configurable permissions (staff or superuser).
    - Overview of the administration team and platform metrics.
    """
    admin_user = request.user

    # Ensure profile model instance exists
    if not hasattr(admin_user, 'profile'):
        Profile.objects.create(user=admin_user)

    if request.method == "POST":
        action = request.POST.get('action')

        # 1. Update personal admin profile
        if action == "update_profile":
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            bio = request.POST.get('bio', '').strip()

            # Check email uniqueness if email is changed
            if email:
                email_lower = email.lower()
                if email_lower != admin_user.email.lower():
                    if User.objects.filter(email__iexact=email).exclude(id=admin_user.id).exists():
                        messages.error(request, f"Email ID '{email}' is already registered to another account. Please use a unique Email ID.")
                        return redirect('admin_profile')
                    admin_user.email = email_lower

            # Names have NO uniqueness restriction (e.g. multiple people can be named Avik)
            admin_user.first_name = first_name
            admin_user.last_name = last_name
            admin_user.save()

            profile = admin_user.profile
            profile.phone = phone
            profile.bio = bio
            profile.address = request.POST.get('address', '').strip()
            linkedin = request.POST.get('linkedin_url', '').strip()
            github = request.POST.get('github_url', '').strip()
            profile.linkedin_url = linkedin if linkedin else None
            profile.github_url = github if github else None

            # Handle direct avatar upload with crystal-clear processing
            if request.POST.get('remove_avatar') == '1':
                if profile.profile_pic:
                    profile.profile_pic.delete(save=False)
                    profile.profile_pic = None
            elif 'profile_pic' in request.FILES:
                uploaded_avatar = request.FILES['profile_pic']
                clarified_avatar = process_and_clarify_avatar(uploaded_avatar)
                if clarified_avatar:
                    avatar_filename = f"admin_{admin_user.id}_{int(timezone.now().timestamp())}.jpg"
                    profile.profile_pic.save(avatar_filename, clarified_avatar, save=False)
                else:
                    profile.profile_pic = uploaded_avatar
            profile.save()

            messages.success(request, "Your admin profile details and photo have been updated with crystal-clear quality!")
            return redirect('admin_profile')

        # 2. Change password (Super Administrator clearance only)
        elif action == "change_password":
            if not admin_user.is_superuser:
                messages.error(request, "Access Denied: Staff Administrators do not have permission to change passwords. Only Super Administrators can manage administrator passwords for safety reasons.")
                return redirect('admin_profile')

            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not admin_user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters long.")
            elif new_password != confirm_password:
                messages.error(request, "New password and confirmation do not match.")
            else:
                admin_user.set_password(new_password)
                admin_user.save()
                update_session_auth_hash(request, admin_user)
                messages.success(request, "Your Super Administrator password has been changed successfully!")
            return redirect('admin_profile')

        # 3. Create a new Admin account (Super Administrator clearance only, Identified by Email ID, Password, and Phone Number)
        elif action == "create_admin":
            if not admin_user.is_superuser:
                messages.error(request, "Access Denied: Staff Administrators cannot provision new administrators. Clearance is strictly reserved for Super Administrators.")
                return redirect('admin_profile')

            new_email = request.POST.get('new_email', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            new_phone = request.POST.get('new_phone', '').strip()
            
            # Display name (Can be Avik or any name, NO uniqueness check!)
            admin_name = request.POST.get('admin_name', '').strip()
            new_first_name = request.POST.get('new_first_name', '').strip()
            new_last_name = request.POST.get('new_last_name', '').strip()

            if admin_name and not new_first_name:
                if ' ' in admin_name:
                    new_first_name, new_last_name = admin_name.split(' ', 1)
                else:
                    new_first_name = admin_name

            new_bio = request.POST.get('new_bio', '').strip()
            new_address = request.POST.get('new_address', '').strip()
            new_linkedin = request.POST.get('new_linkedin', '').strip()
            new_github = request.POST.get('new_github', '').strip()
            is_super = request.POST.get('is_superuser') == 'on' and admin_user.is_superuser

            # 1. Unique Email Identification
            if not new_email:
                messages.error(request, "Email ID is required to uniquely identify the administrator.")
                return redirect('admin_profile')
            elif User.objects.filter(email__iexact=new_email).exists():
                messages.error(request, f"An account with Email ID '{new_email}' already exists. Email ID must be unique.")
                return redirect('admin_profile')

            # 2. Password Verification
            if not new_password or len(new_password) < 6:
                messages.error(request, "Initial password must be at least 6 characters.")
                return redirect('admin_profile')

            # 3. Phone Number Verification (Required or Recommended for Identity)
            if not new_phone:
                messages.error(request, "Phone number is required to uniquely identify and contact the administrator.")
                return redirect('admin_profile')

            # Generate collision-free database username based on Email ID
            base_user = new_email.lower().replace('@', '_at_')
            unique_username = base_user
            idx = 1
            while User.objects.filter(username__iexact=unique_username).exists():
                unique_username = f"{base_user}_{idx}"
                idx += 1

            new_admin = User.objects.create_user(
                username=unique_username,
                email=new_email.lower(),
                password=new_password,
                first_name=new_first_name,
                last_name=new_last_name,
                is_staff=True,
                is_student=False,
                is_superuser=is_super
            )

            if not hasattr(new_admin, 'profile'):
                Profile.objects.create(user=new_admin)
            new_profile = new_admin.profile
            new_profile.phone = new_phone
            if new_bio:
                new_profile.bio = new_bio
            if new_address:
                new_profile.address = new_address
            if new_linkedin:
                new_profile.linkedin_url = new_linkedin
            if new_github:
                new_profile.github_url = new_github

            # Process avatar with crystal-clear enhancement
            if 'new_admin_avatar' in request.FILES:
                raw_avatar = request.FILES['new_admin_avatar']
                enhanced_avatar = process_and_clarify_avatar(raw_avatar)
                if enhanced_avatar:
                    avatar_fn = f"admin_{new_admin.id}_{int(timezone.now().timestamp())}.jpg"
                    new_profile.profile_pic.save(avatar_fn, enhanced_avatar, save=False)
                else:
                    new_profile.profile_pic = raw_avatar
            new_profile.save()

            role_label = "Super Administrator" if is_super else "Administrator"
            display_str = new_admin.first_name or new_admin.email
            messages.success(request, f"New {role_label} '{display_str}' created successfully! Identified by Email: '{new_admin.email}' and Phone: '{new_phone}'. They can log in immediately.")
            return redirect('admin_profile')

        # 4. Super Admin Emergency Password Override & Forgot Password Reset for ANY Staff or Super Admin
        elif action == "super_admin_reset_password":
            if not admin_user.is_superuser:
                messages.error(request, "Access Denied: Only Super Administrators have authorization to reset or override administrator passwords.")
                return redirect('admin_profile')

            target_id = request.POST.get('target_admin_id')
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            target_admin = User.objects.filter(id=target_id).filter(Q(is_staff=True) | Q(is_superuser=True)).first()
            if not target_admin:
                messages.error(request, "Target administrator account was not found.")
                return redirect('admin_profile')

            if not new_password or len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters long.")
                return redirect('admin_profile')

            if new_password != confirm_password:
                messages.error(request, "New password and confirmation password do not match.")
                return redirect('admin_profile')

            target_admin.set_password(new_password)
            target_admin.save()

            if target_admin.id == admin_user.id:
                update_session_auth_hash(request, admin_user)

            display_name = target_admin.first_name or target_admin.email
            role_label = "Super Administrator" if target_admin.is_superuser else "Staff Administrator"
            messages.success(request, f"Security Override Successful: Password for {role_label} '{display_name}' ({target_admin.email}) has been updated. They can now log in immediately with the new password.")
            return redirect('admin_profile')

        # 5. Toggle admin active status (superuser only)
        elif action == "toggle_admin_status":
            if not admin_user.is_superuser:
                messages.error(request, "Only Super Administrators can modify administrator status.")
            else:
                target_id = request.POST.get('target_user_id')
                target_user = User.objects.filter(id=target_id, is_staff=True).first()
                if not target_user:
                    messages.error(request, "Admin user not found.")
                elif target_user == admin_user:
                    messages.error(request, "You cannot deactivate your own administrator account.")
                else:
                    target_user.is_active = not target_user.is_active
                    target_user.save()
                    status_text = "activated" if target_user.is_active else "deactivated"
                    display_target = target_user.first_name or target_user.email
                    messages.success(request, f"Administrator '{display_target}' ({target_user.email}) has been {status_text}.")
            return redirect('admin_profile')

    # Team administrators & system stats
    admin_team = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).select_related('profile').order_by('-date_joined')
    total_students_count = User.objects.filter(is_student=True, is_staff=False, is_superuser=False).count()
    total_courses_count = Course.objects.count()
    total_docs_count = LibraryDocument.objects.count()
    total_exams_count = Exam.objects.count()

    context = {
        'admin_user': admin_user,
        'admin_team': admin_team,
        'total_students_count': total_students_count,
        'total_courses_count': total_courses_count,
        'total_docs_count': total_docs_count,
        'total_exams_count': total_exams_count,
    }
    return render(request, 'custom_admin/admin_profile.html', context)


# 8. PREVIOUS: SYNTAX SINGULARITY (AI LOGIC CHECKER)

@login_required
def syntax_singularity_view(request):
    """ Renders the VS Code style Syntax Singularity page. """
    enrolled_courses = Enrollment.objects.filter(student=request.user).select_related('course')
    
    # Simple mapping of keywords to languages for the frontend
    course_language_map = {}
    for enrollment in enrolled_courses:
        title = enrollment.course.title.lower()
        langs = []
        if 'python' in title: langs.append('python')
        if 'java' in title and 'javascript' not in title: langs.append('java')
        if 'c++' in title or 'cpp' in title: langs.append('cpp')
        if 'javascript' in title or 'js' in title or 'node' in title or 'react' in title or 'express' in title or 'angular' in title:
            langs.extend(['javascript', 'Node Js', 'React js', 'Express Js', 'Angular Js'])
        if 'php' in title: langs.append('PHP')
        if 'type' in title and 'script' in title: langs.append('TypeScript')
        if 'css' in title or 'html' in title: langs.append('Css')
        if 'mongo' in title or 'db' in title: langs.extend(['MongoDB', 'DBMS'])
        
        # Fallback to general languages if no specific match
        if not langs:
            langs = ['python', 'java', 'cpp', 'javascript', 'DBMS']
            
        course_language_map[enrollment.course.id] = list(set(langs))
        
    return render(request, 'syntax_singularity.html', {
        'courses': enrolled_courses,
        'course_language_map_json': json.dumps(course_language_map)
    })

@login_required
@csrf_exempt
def generate_ai_challenge(request):
    """ Calls Groq API to generate a dynamic coding problem based on User's typed topic. """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            language = data.get('language', 'python')
            topic = data.get('topic', 'Logic') # Now accepts user-typed topic
            difficulty = data.get('difficulty', 'Easy')
            challenge_type = data.get('challenge_type', 'solve')
            type_instructions = {
                'solve': '',
                'debug': 'CHALLENGE TYPE OVERRIDE: This is a DEBUGGING challenge. `base_code` MUST be a complete but BUGGY implementation (2-3 subtle bugs) that the student must find and fix. The problem statement must describe the expected behaviour, not the bugs.',
                'fill': 'CHALLENGE TYPE OVERRIDE: This is a FILL-IN-THE-BLANKS challenge. `base_code` MUST be an almost complete solution where the key lines are replaced by `___` placeholders (3-5 blanks) that the student must complete.',
                'optimize': 'CHALLENGE TYPE OVERRIDE: This is an OPTIMIZATION challenge. `base_code` MUST be a correct but slow brute-force solution. The student must rewrite it to meet the stated time complexity in Constraints.',
            }
            type_note = type_instructions.get(challenge_type, '')
            
            course_obj = get_object_or_404(Course, id=course_id)
            groq_api_key = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY', ''))
            
            if not groq_api_key:
                return JsonResponse({'status': 'error', 'message': 'Groq API Key is missing in backend.'}, status=500)
                
            headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
            
            prompt = f"""
            You are ARIS, an advanced AI system. Generate a coding problem for a student.
            Language: {language}
            Topic: {topic}
            Difficulty: {difficulty}
            
            CRITICAL INSTRUCTION FOR `description`:
            You MUST format the description exactly like a LeetCode problem. Use markdown.
            Include the following sections strictly:
            1. **Problem Statement**: Clear explanation of the task.
            2. **Example 1**: Input and Output format clearly shown.
            3. **Example 2**: Input and Output format clearly shown.
            4. **Constraints**: Time/Space limits or array size limits.
            
            CRITICAL INSTRUCTION FOR `base_code`: 
            You MUST NOT provide the solution. Provide ONLY the empty function signature/template for the student to start with. The function body MUST be empty (use `pass` in Python, or empty brackets `{{}}` in other languages). DO NOT write the actual logic.
            {type_note}
            
            Return ONLY a valid JSON object without markdown tags:
            {{
                "title": "A short engaging title",
                "description": "The full LeetCode style markdown string",
                "base_code": "def solve(arr):\\n    # Write your logic here\\n    pass"
            }}
            """
            
            payload = {
                "model": "qwen/qwen3.8-27b", # Restore required model for this environment
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5,
                "response_format": {"type": "json_object"},
                "max_tokens": 800
            }
            
            base_url = "https://"
            endpoint = "api.groq.com/openai/v1/chat/completions"
            groq_url = base_url + endpoint
            
            response = requests.post(groq_url, headers=headers, json=payload)
            response_data = response.json()
            
            if 'choices' not in response_data:
                error_msg = response_data.get('error', {}).get('message', str(response_data))
                return JsonResponse({'status': 'error', 'message': f'Groq API Error: {error_msg}'}, status=500)
            
            content = response_data['choices'][0]['message']['content']
            
            # Extract JSON block using regex to avoid conversational text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
                
            try: 
                problem_data = json.loads(content)
            except json.JSONDecodeError as e: 
                return JsonResponse({'status': 'error', 'message': f'AI generated invalid JSON: {str(e)}. Try again.'}, status=500)
            
            base_coins = 10 if difficulty == 'Easy' else (30 if difficulty == 'Medium' else 100)
            
            new_problem = DynamicBountyProblem.objects.create(
                student=request.user, course=course_obj, language=language,
                topic=topic, difficulty=difficulty, title=problem_data['title'],
                description=problem_data['description'], base_code=problem_data.get('base_code', ''),
                base_bounty_coins=base_coins
            )
            
            return JsonResponse({
                'status': 'success', 'problem_id': new_problem.id,
                'title': new_problem.title, 'description': new_problem.description,
                'base_code': new_problem.base_code, 'difficulty': new_problem.difficulty,
                'base_coins': new_problem.base_bounty_coins
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)


@login_required
@csrf_exempt
def submit_bounty_code(request):
    """ Evaluates the student's code logically using Groq AI (No Docker Execution). """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            problem_id = data.get('problem_id')
            submitted_code = data.get('code', '')
            
            problem = get_object_or_404(DynamicBountyProblem, id=problem_id, student=request.user)
            
            if not submitted_code.strip():
                return JsonResponse({'status': 'error', 'message': 'Code cannot be empty.'})

            groq_api_key = getattr(settings, 'GROQ_API_KEY', os.environ.get('GROQ_API_KEY', ''))
            if not groq_api_key:
                return JsonResponse({'status': 'error', 'message': 'Groq API Key is missing.'}, status=500)
            
            #  ONE-SHOT LOGIC: Check attempt count
            attempt_count = BountySubmission.objects.filter(problem=problem, student=request.user).count()
            current_attempt = attempt_count + 1
                
            headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
            
            prompt = f"""
            You are a strict, expert coding instructor.
            Problem Title: {problem.title}
            Problem Description: {problem.description}
            Language: {problem.language}
            
            Student's Code:
            {submitted_code}
            
            Check if the student's code logically and perfectly solves the problem. Ignore minor syntax warnings if the core logic is flawlessly correct.
            
            Return ONLY a valid JSON object in this exact format (no markdown):
            {{
                "is_correct": true or false,
                "feedback": "Short encouraging explanation of what is right, or clear guidance on what is logically wrong."
            }}
            """
            
            payload = {
                "model": "qwen/qwen3.8-27b", 
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
            
            base_url = "https://"
            endpoint = "api.groq.com/openai/v1/chat/completions"
            groq_url = base_url + endpoint
            
            response = requests.post(groq_url, headers=headers, json=payload)
            response_data = response.json()
            
            if 'choices' not in response_data:
                error_msg = response_data.get('error', {}).get('message', str(response_data))
                return JsonResponse({'status': 'error', 'message': f'AI failed to evaluate code: {error_msg}'}, status=500)
            
            content = response_data['choices'][0]['message']['content']
            
            # Extract JSON block using regex to avoid conversational text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
                
            try: 
                eval_result = json.loads(content)
            except json.JSONDecodeError as e: 
                return JsonResponse({'status': 'error', 'message': f'AI response format error: {str(e)}'}, status=500)
            
            is_correct = eval_result.get('is_correct', False)
            feedback = eval_result.get('feedback', 'No feedback provided.')
            
            earned_coins = 0
            
            # ONE-SHOT REWARD LOGIC: Coin Reward only on 1st Attempt
            if is_correct and not problem.is_solved:
                if current_attempt == 1:
                    earned_coins = problem.base_bounty_coins
                    request.user.lms_coins += earned_coins
                    request.user.save(update_fields=['lms_coins'])
                    
                problem.is_solved = True
                problem.save(update_fields=['is_solved'])
            
            BountySubmission.objects.create(
                problem=problem, student=request.user, submitted_code=submitted_code,
                status="AI Accepted" if is_correct else "AI Rejected",
                earned_coins=earned_coins,
                attempt_number=current_attempt
            )
            
            return JsonResponse({
                'status': 'success',
                'is_correct': is_correct,
                'feedback': feedback,
                'earned_coins': earned_coins,
                'attempt': current_attempt
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)

@login_required
@csrf_exempt
def track_progress(request):
    """
    API Endpoint to track video watch time, PDF views, and Live Class attendance.
    Expects JSON: { "type": "video"|"pdf"|"liveclass", "id": 1, "watch_time": 120 }
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            track_type = data.get('type')
            item_id = data.get('id')
            
            if track_type == 'video':
                lesson = get_object_or_404(Lesson, id=item_id)
                watch_time = int(data.get('watch_time', 0))
                
                lesson_progress, _ = LessonProgress.objects.get_or_create(
                    student=request.user, lesson=lesson
                )
                
                # Only update if the new watch time is higher (prevents rewinding losing progress)
                if watch_time > lesson_progress.watch_time_seconds:
                    lesson_progress.watch_time_seconds = watch_time
                    
                    # Check if 80% completed
                    required_time = lesson.duration_in_seconds * 0.8
                    if required_time > 0 and watch_time >= required_time and not lesson_progress.is_completed:
                        lesson_progress.is_completed = True
                        lesson_progress.completed_at = timezone.now()
                        request.user.lms_coins += 20
                        request.user.save(update_fields=['lms_coins'])
                        log_student_activity(request.user, 'lesson_watch', f'Completed "{lesson.title}"', course=lesson.course)
                    
                    lesson_progress.save()
                    
                # Sync progress globally
                enrollment = get_object_or_404(Enrollment, student=request.user, course=lesson.course)
                enrollment.sync_progress()
                
                # Calculate per-lesson completion percentage
                required_time = lesson.duration_in_seconds * 0.8
                if lesson_progress.is_completed:
                    lesson_percent = 100
                elif required_time > 0 and lesson_progress.watch_time_seconds > 0:
                    lesson_percent = min(100, int((lesson_progress.watch_time_seconds / required_time) * 100))
                else:
                    lesson_percent = 0
                
                return JsonResponse({
                    'status': 'success',
                    'progress': enrollment.progress,
                    'is_completed': lesson_progress.is_completed,
                    'lesson_percent': lesson_percent,
                    'watch_time': lesson_progress.watch_time_seconds,
                    'required_time': int(required_time) if required_time > 0 else 0,
                    'coins_earned': 20 if lesson_progress.is_completed else 0,
                })
                
            elif track_type == 'pdf':
                doc = get_object_or_404(LibraryDocument, id=item_id)
                DocumentView.objects.get_or_create(student=request.user, document=doc)
                if doc.course:
                    enrollment = get_object_or_404(Enrollment, student=request.user, course=doc.course)
                    enrollment.sync_progress()
                    return JsonResponse({'status': 'success', 'progress': enrollment.progress})
                return JsonResponse({'status': 'success'})
                
            elif track_type == 'liveclass':
                live_class = get_object_or_404(LiveClass, id=item_id)
                LiveClassAttendance.objects.get_or_create(student=request.user, live_class=live_class)
                if live_class.course:
                    enrollment = get_object_or_404(Enrollment, student=request.user, course=live_class.course)
                    enrollment.sync_progress()
                    return JsonResponse({'status': 'success', 'progress': enrollment.progress})
                return JsonResponse({'status': 'success'})

            elif track_type == 'complete_lesson':
                lesson = get_object_or_404(Lesson, id=item_id)
                lesson_progress, _ = LessonProgress.objects.get_or_create(
                    student=request.user, lesson=lesson
                )
                coins_earned = 0
                if not lesson_progress.is_completed:
                    lesson_progress.is_completed = True
                    lesson_progress.completed_at = timezone.now()
                    if lesson.duration_in_seconds > 0 and lesson_progress.watch_time_seconds < lesson.duration_in_seconds:
                        lesson_progress.watch_time_seconds = lesson.duration_in_seconds
                    lesson_progress.save()
                    request.user.lms_coins += 20
                    request.user.save(update_fields=['lms_coins'])
                    coins_earned = 20
                    log_student_activity(request.user, 'lesson_watch', f'Marked Completed "{lesson.title}"', course=lesson.course)
                
                enrollment = get_object_or_404(Enrollment, student=request.user, course=lesson.course)
                enrollment.sync_progress()
                
                return JsonResponse({
                    'status': 'success',
                    'progress': enrollment.progress,
                    'is_completed': True,
                    'lesson_percent': 100,
                    'watch_time': lesson_progress.watch_time_seconds,
                    'coins_earned': coins_earned,
                })
                
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'}, status=400)