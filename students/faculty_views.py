from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

# Import Models
from .models import Course, Enrollment, LiveClass, LibraryDocument

# =====================================================================
# FACULTY PANEL VIEWS
# =====================================================================

@login_required
def faculty_dashboard(request):
    """
    Main Dashboard for Faculty Members.
    Displays quick stats, upcoming classes, and recent documents.
    """
    user = request.user
    
    # Security Check: Only allow users marked as faculty
    if not getattr(user, 'is_faculty', False):
        messages.error(request, "Access Denied! Only faculty members can view this page.")
        return redirect('dashboard')
    
    # Fetch assigned courses for this specific faculty
    assigned_courses = Course.objects.filter(assigned_faculty=user)
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

    context = {
        'user': user,
        'assigned_courses': assigned_courses,
        'total_courses': total_courses,
        'total_students': total_students,
        'upcoming_classes': upcoming_classes,
        'documents': documents,
    }
    return render(request, 'faculty_dashboard.html', context)


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