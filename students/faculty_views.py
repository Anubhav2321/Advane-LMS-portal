from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

# Import Models
from .models import (
    Course, Enrollment, LiveClass, LibraryDocument, 
    Assignment, AssignmentSubmission, FacultyProfile, User,
    Profile, ProctoringLog, CourseGroupMessage #  NEW IMPORTS ADDED
)

# Import Forms 
from .forms import (
    AssignmentForm, AssignmentGradeForm, FacultyProfileUpdateForm, 
    LiveClassForm, LibraryDocumentForm,
    FacultyProfilePicForm, CourseGroupMessageForm #  NEW IMPORTS ADDED
)

# FACULTY PANEL VIEWS

@login_required
def faculty_dashboard(request):
    """
    Main Dashboard for Faculty Members.
    Displays quick stats, upcoming classes, and recent documents.
    Now fully dynamic with Assignments, Submissions, Forms, and Profile Pics!
    """
    user = request.user
    
    # Security Check: Only allow users marked as faculty
    if not getattr(user, 'is_faculty', False):
        messages.error(request, "Access Denied! Only faculty members can view this page.")
        return redirect('dashboard')
    
    # Fetch assigned courses for this specific faculty
    assigned_courses = Course.objects.all()
    total_courses = assigned_courses.count()
    
    # Fetch total unique students enrolled in these assigned courses
    total_students = Enrollment.objects.filter(course__in=assigned_courses).values('student').distinct().count()
    
    # Upcoming Live Classes for these courses
    upcoming_classes = LiveClass.objects.filter(
        course__in=assigned_courses, 
        date_time__gte=timezone.now()
    ).order_by('date_time')
    
    # Recent Documents uploaded for these courses
    documents = LibraryDocument.objects.filter(
        course__in=assigned_courses
    ).order_by('-uploaded_at')[:5]

    # 🚀 NEW: ASSIGNMENTS & PENDING STATS LOGIC
    # Fetch all assignments created for their courses
    assignments = Assignment.objects.filter(course__in=assigned_courses).order_by('-created_at')
    
    # Fetch submissions that are not graded yet
    pending_submissions = AssignmentSubmission.objects.filter(
        assignment__course__in=assigned_courses, 
        is_graded=False
    ).order_by('submitted_at')
    
    pending_assignments_count = pending_submissions.count()

    # Get or create Faculty Professional Profile
    faculty_profile, created = FacultyProfile.objects.get_or_create(user=user)
    
    # 🚀 NEW: Get or create Base Profile (For Profile Picture)
    base_profile, _ = Profile.objects.get_or_create(user=user)

    # 🚀 NEW: FETCH AI PROCTORING LOGS FOR EXAM MONITOR
    proctoring_logs = ProctoringLog.objects.filter(
        exam__course__in=assigned_courses
    ).order_by('-timestamp')[:20]

    # 🚀 INITIALIZE FORMS FOR DASHBOARD UI

    assignment_form = AssignmentForm(faculty=user)
    
    live_class_form = LiveClassForm()
    live_class_form.fields['course'].queryset = assigned_courses # Restrict to their courses
    
    library_form = LibraryDocumentForm()
    library_form.fields['course'].queryset = assigned_courses # Restrict to their courses
    
    profile_form = FacultyProfileUpdateForm(instance=faculty_profile)
    
    # 🚀 NEW: Profile Pic Form
    profile_pic_form = FacultyProfilePicForm(instance=base_profile)

    context = {
        'user': user,
        'assigned_courses': assigned_courses,
        'total_courses': total_courses,
        'total_students': total_students,
        'upcoming_classes': upcoming_classes,
        'documents': documents,
        
        # CONTEXT DATA
        'assignments': assignments,
        'pending_submissions': pending_submissions,
        'pending_assignments_count': pending_assignments_count,
        'faculty_profile': faculty_profile,
        'base_profile': base_profile, # 🚀 Added
        'proctoring_logs': proctoring_logs, # 🚀 Added
        
        # FORMS FOR MODALS/TABS
        'assignment_form': assignment_form,
        'live_class_form': live_class_form,
        'library_form': library_form,
        'profile_form': profile_form,
        'profile_pic_form': profile_pic_form, # 🚀 Added
    }
    return render(request, 'faculty_dashboard.html', context)


# ACTION VIEWS FOR HANDLING FORM SUBMISSIONS (POST REQUESTS)

@login_required
def faculty_create_assignment(request):
    if request.method == 'POST' and getattr(request.user, 'is_faculty', False):
        form = AssignmentForm(request.POST, faculty=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment created successfully!")
        else:
            messages.error(request, "Error creating assignment. Please check the inputs.")
    return redirect('faculty_dashboard')


@login_required
def faculty_schedule_live(request):
    if request.method == 'POST' and getattr(request.user, 'is_faculty', False):
        form = LiveClassForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data.get('course')
            if course in Course.objects.filter(assigned_faculty=request.user):
                form.save()
                messages.success(request, "Live class scheduled successfully!")
            else:
                messages.error(request, "You can only schedule classes for your own assigned modules.")
        else:
            messages.error(request, "Error scheduling live class.")
    return redirect('faculty_dashboard')


@login_required
def faculty_upload_document(request):
    if request.method == 'POST' and getattr(request.user, 'is_faculty', False):
        form = LibraryDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.cleaned_data.get('course')
            if course in Course.objects.filter(assigned_faculty=request.user):
                doc = form.save(commit=False)
                doc.uploaded_by = request.user
                doc.save()
                messages.success(request, "Asset uploaded to Digital Archive!")
            else:
                messages.error(request, "You can only upload documents for your own assigned modules.")
        else:
            messages.error(request, "Upload failed. Check file type (PDF/Doc only).")
    return redirect('faculty_dashboard')


@login_required
def faculty_update_profile(request):
    if request.method == 'POST' and getattr(request.user, 'is_faculty', False):
        faculty_profile, _ = FacultyProfile.objects.get_or_create(user=request.user)
        form = FacultyProfileUpdateForm(request.POST, instance=faculty_profile)
        
        if form.is_valid():
            form.save()
            # Also update base User info
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.save()
            
            messages.success(request, "Faculty Profile updated successfully!")
        else:
            messages.error(request, "Failed to update profile.")
    return redirect('faculty_dashboard')


# 🚀 NEW: ACTION VIEW FOR AUTO-SUBMIT PROFILE PICTURE
@login_required
def faculty_update_profile_pic(request):
    if request.method == 'POST' and getattr(request.user, 'is_faculty', False):
        base_profile, _ = Profile.objects.get_or_create(user=request.user)
        form = FacultyProfilePicForm(request.POST, request.FILES, instance=base_profile)
        
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated instantly!")
        else:
            messages.error(request, "Failed to upload picture. Check file size/format.")
    return redirect('faculty_dashboard')


# PREVIOUS VIEWS (KEPT INTACT AS REQUESTED)

@login_required
def faculty_courses(request):
    """ View for My Courses tab """
    if not getattr(request.user, 'is_faculty', False): 
        return redirect('dashboard')
    
    assigned_courses = Course.objects.filter(assigned_faculty=request.user)
    return render(request, 'faculty_courses.html', {'user': request.user, 'courses': assigned_courses})


@login_required
def faculty_live_studio(request):
    """ View for Live Studio tab """
    if not getattr(request.user, 'is_faculty', False): 
        return redirect('dashboard')
        
    return render(request, 'faculty_live_studio.html', {'user': request.user})


@login_required
def faculty_digital_archive(request):
    """ View for Digital Archive tab """
    if not getattr(request.user, 'is_faculty', False): 
        return redirect('dashboard')
        
    return render(request, 'faculty_digital_archive.html', {'user': request.user})


@login_required
def faculty_exam_monitor(request):
    """ View for AI Exam Monitor tab """
    if not getattr(request.user, 'is_faculty', False): 
        return redirect('dashboard')
        
    return render(request, 'faculty_exam_monitor.html', {'user': request.user})


@login_required
def faculty_community(request):
    """ View for Community CommLink tab """
    if not getattr(request.user, 'is_faculty', False): 
        return redirect('dashboard')
        
    return render(request, 'faculty_community.html', {'user': request.user})


@login_required
def faculty_profile(request):
    """ View for Faculty Profile tab """
    if not getattr(request.user, 'is_faculty', False): 
        return redirect('dashboard')
        
    return render(request, 'faculty_profile.html', {'user': request.user})