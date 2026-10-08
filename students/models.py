import os
import re  # CRITICAL IMPORT: Video fix er jonno eta must lagbe
import requests #  NEW: Google profile picture download er jonno
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile #  NEW: Image save korar jonno
from allauth.account.signals import user_logged_in #  NEW: Login signal
from allauth.socialaccount.models import SocialAccount # NEW: Google data fetch korar jonno

# 1. CUSTOM USER MODEL

class User(AbstractUser):
    is_student = models.BooleanField(default=True, verbose_name="Is Student")
    is_teacher = models.BooleanField(default=False, verbose_name="Is Teacher")
    is_faculty = models.BooleanField(default=False, verbose_name="Is Faculty") # NEW: Added Faculty Role
    
    student_level = models.CharField(
        max_length=50, 
        choices=[('Beginner', 'Beginner'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')],
        default='Beginner'
    )
    stream = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Science, Arts, Engineering")
    
    #  NEW: LMS COIN ECONOMY 

    lms_coins = models.PositiveIntegerField(default=100, help_text="Virtual coins for LMS Economy")
    
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-date_joined']

    def save(self, *args, **kwargs):
        if self.is_staff or self.is_superuser:
            self.is_student = False
        super().save(*args, **kwargs)

    def __str__(self):
        role = "Teacher" if self.is_teacher else ("Faculty" if self.is_faculty else "Student")
        return f"{self.username} | {role}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def profile_pic_url(self):
        """
        Returns high-resolution, crystal-clear profile picture URL.
        Checks uploaded profile image first, then linked Google SocialAccount picture.
        """
        try:
            if hasattr(self, 'profile') and self.profile and self.profile.profile_pic:
                name = self.profile.profile_pic.name
                if name and name != 'profile_pics/default.png':
                    return self.profile.profile_pic.url
        except Exception:
            pass

        try:
            from allauth.socialaccount.models import SocialAccount
            social = SocialAccount.objects.filter(user=self, provider='google').first()
            if social and social.extra_data:
                pic = social.extra_data.get('picture')
                if pic:
                    for low_res in ['=s96-c', '=s50-c', '=s64-c', '=s100']:
                        if low_res in pic:
                            pic = pic.replace(low_res, '=s384-c')
                            break
                    return pic
        except Exception:
            pass

        return None

import io
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

def process_and_clarify_avatar(image_file, target_size=(512, 512)):
    """
    Takes any image (low quality, blurry, high quality, phone orientation)
    and turns it into a crystal-clear, centered, unblurred 512x512 portrait.
    - Corrects EXIF phone orientation
    - Converts cleanly to RGB
    - Center-crops to 1:1 square
    - Resamples with Lanczos high-fidelity filter
    - Enhances contrast to remove haze/washout
    - Enhances sharpness and applies unsharp mask for facial clarity
    - Saves as 95% quality optimized JPEG
    """
    try:
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        img = Image.open(image_file)

        # 1. Correct mobile camera EXIF orientation
        img = ImageOps.exif_transpose(img)

        # 2. Convert to RGB cleanly without color corruption
        if img.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if 'A' in img.getbands():
                bg.paste(img, mask=img.split()[-1])
            else:
                bg.paste(img)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # 3. Center crop to 1:1 square so face is centered and not stretched
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))

        # 4. High-resolution Lanczos resampling
        img = img.resize(target_size, Image.Resampling.LANCZOS)

        # 5. Smart facial clarity enhancement
        enhancer_c = ImageEnhance.Contrast(img)
        img = enhancer_c.enhance(1.10)

        enhancer_s = ImageEnhance.Sharpness(img)
        img = enhancer_s.enhance(1.35)

        # Subtle unsharp mask to clarify facial features without noise
        img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=3))

        # 6. Save as crisp JPEG
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=95, optimize=True)
        buffer.seek(0)
        return ContentFile(buffer.getvalue())
    except Exception as e:
        print(f"[AVATAR PROCESSING ERROR]: {e}")
        return None

# 2. PROFILE MODEL

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Profile Picture Field
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-enhance profile picture if freshly uploaded
        if self.profile_pic:
            try:
                from django.core.files.uploadedfile import UploadedFile
                if hasattr(self.profile_pic, 'file') and isinstance(self.profile_pic.file, UploadedFile):
                    processed = process_and_clarify_avatar(self.profile_pic)
                    if processed:
                        filename = f"user_{self.user_id}_avatar.jpg"
                        self.profile_pic.save(filename, processed, save=False)
            except Exception:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Profile: {self.user.username}"

# NEW: FACULTY PROFILE MODEL
class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_profile', limit_choices_to={'is_faculty': True})
    department = models.CharField(max_length=100, blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    specialization = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Data Science, AI, Backend")
    background = models.CharField(max_length=100, blank=True, null=True, help_text="e.g., Science, Arts")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Faculty Profile: {self.user.full_name}"

# 3. COURSE MODEL

class Course(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, help_text="Auto-generated from title")
    description = models.TextField()
    
    #  Faculty Name (String Field)
    faculty_name = models.CharField(max_length=100, default="Expert Faculty") 
    
    # NEW: Assigned Faculty (Foreign Key)
    assigned_faculty = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_courses', limit_choices_to={'is_faculty': True})

    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_published = models.BooleanField(default=True)
    
    #  NEW: Coin Purchase Logic 

    is_coin_purchasable = models.BooleanField(default=False, help_text="Check this to allow purchasing with coins")
    coin_price = models.PositiveIntegerField(default=0, help_text="Price in LMS Coins (if purchasable)")
    
    total_modules = models.PositiveIntegerField(default=0)
    difficulty_level = models.CharField(
        max_length=20, 
        choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')],
        default='Medium'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(Course, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

# 4. LESSON MODEL (CRITICAL UPDATE HERE)

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, blank=True)
    
    video_file = models.FileField(upload_to='lessons/videos/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="Paste YouTube or Video Link here") 
    
    content = models.TextField(blank=True, null=True)
    
    duration = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 10:30") 
    order = models.PositiveIntegerField(default=1)
    is_preview = models.BooleanField(default=False)
    
    # Tracking field
    is_completed = models.BooleanField(default=False) 

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']

    @property
    def duration_in_seconds(self):
        """Converts duration string like '10:30' into total seconds."""
        if not self.duration:
            return 0
        try:
            parts = self.duration.split(':')
            if len(parts) == 3: # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2: # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(parts[0]) * 60 # Treat as just minutes
        except:
            return 0

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # Trim whitespace from URL if present to avoid errors
        if self.video_url: 
            self.video_url = self.video_url.strip()
        super(Lesson, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.order}. {self.title}"

    # --- ADVANCED YOUTUBE ID EXTRACTOR (Fixes Error 153) ---
    def get_youtube_embed_url(self):
        if not self.video_url:
            return ""
        
        # Strip whitespace again just in case
        url = self.video_url.strip()
        
        # Regex to handle: standard, share, embed, shorts, mobile links
        regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        
        match = re.search(regex, url)
        
        if match:
            # If ID found (e.g. dQw4w9WgXcQ), convert to Embed URL
            # rel=0 means show related videos from same channel only
            return f"https://www.youtube.com/embed/{match.group(1)}?rel=0"
        
        # Fallback: Return original URL if it doesn't match standard patterns
        return url

# 5. ENROLLMENT MODEL

class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    progress = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-enrolled_at']

    def update_progress(self, percent):
        self.progress = min(100.0, max(0.0, percent))
        if self.progress == 100.0:
            self.is_completed = True
        self.save()

    def get_real_progress(self):
        """
        Calculate real progress based on Overall Course Requirements.
        Tasks = Lessons (watch time > 80% or marked complete) + Quizzes (PASSED, score >= 50%) + Live Classes (attended) + Documents (read) + Assignments (submitted)
        Duplicate attempts and failed quizzes do NOT falsely inflate progress.
        """
        # 1. Lesson Tasks
        total_lessons = self.course.lessons.count()
        completed_lessons = 0
        for lp in LessonProgress.objects.filter(student=self.student, lesson__course=self.course):
            required_time = lp.lesson.duration_in_seconds * 0.8
            if lp.is_completed or (required_time > 0 and lp.watch_time_seconds >= required_time):
                completed_lessons += 1
        completed_lessons = min(total_lessons, completed_lessons)

        # 2. Quiz Tasks (Count ONLY distinct PASSED quizzes; failed attempts do not count!)
        total_quizzes = Exam.objects.filter(course=self.course, is_active=True).count()
        passed_exam_ids = set()
        for qr in QuizResult.objects.filter(student=self.student, exam__course=self.course):
            if qr.total_marks > 0:
                if (qr.score / qr.total_marks) >= 0.5:
                    passed_exam_ids.add(qr.exam_id)
            elif qr.score > 0:
                passed_exam_ids.add(qr.exam_id)
        completed_quizzes = min(total_quizzes, len(passed_exam_ids))

        # 3. Live Class Tasks
        total_classes = self.course.live_classes.count()
        attended_classes = min(
            total_classes,
            LiveClassAttendance.objects.filter(student=self.student, live_class__course=self.course).values('live_class_id').distinct().count()
        )

        # 4. Document Tasks
        total_docs = self.course.documents.count()
        read_docs = min(
            total_docs,
            DocumentView.objects.filter(student=self.student, document__course=self.course).values('document_id').distinct().count()
        )

        # 5. Assignment Tasks
        total_assignments = self.course.assignments.count()
        submitted_assignments = min(
            total_assignments,
            AssignmentSubmission.objects.filter(student=self.student, assignment__course=self.course).values('assignment_id').distinct().count()
        )

        total_tasks = total_lessons + total_quizzes + total_classes + total_docs + total_assignments
        completed_tasks = completed_lessons + completed_quizzes + attended_classes + read_docs + submitted_assignments

        if total_tasks == 0:
            return {'percent': 0.0, 'completed': 0, 'total': 0}
        
        percent = min(100.0, max(0.0, round((completed_tasks / total_tasks) * 100, 1)))
        return {'percent': percent, 'completed': min(total_tasks, completed_tasks), 'total': total_tasks}

    def sync_progress(self):
        """Sync the progress field with real lesson progress data."""
        data = self.get_real_progress()
        self.progress = data['percent']
        if data['percent'] >= 100.0:
            self.is_completed = True
        self.save(update_fields=['progress', 'is_completed'])

    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"


# 5.5 LESSON PROGRESS MODEL (Per-Student Lesson Tracking)

class LessonProgress(models.Model):
    """
    Tracks which lessons each student has completed.
    Enables real progress calculation: completed_lessons / total_lessons * 100
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_progress')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    watch_time_seconds = models.PositiveIntegerField(default=0, help_text="Total seconds spent watching")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lesson')
        ordering = ['lesson__order']

    def __str__(self):
        status = "✅" if self.is_completed else "⏳"
        return f"{status} {self.student.username} — {self.lesson.title}"


# 6. EXAM & QUIZ LOGIC

class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    exam_link = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(default=15)
    
    total_marks = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        if self.deadline and timezone.now() > self.deadline:
            return True
        return False

    def __str__(self):
        return self.title

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    def __str__(self): return self.title

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    
    question_text = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_option = models.CharField(max_length=200)
    
    marks = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.question_text[:50]

class QuizResult(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score = models.FloatField()
    total_marks = models.FloatField(default=0)
    taken_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.score}"


# 7. UTILITY MODELS

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('notice', 'Notice / Announcement'),
        ('course', 'New Course'),
        ('lesson', 'New Lesson'),
        ('live_class', 'Live Class'),
        ('exam', 'AI Exam / Quiz'),
        ('document', 'Study Material'),
        ('assignment', 'Assignment Task'),
        ('coins', 'LMS Coins Reward'),
        ('system', 'System Alert'),
    ]

    title = models.CharField(max_length=255, default="New Notice")
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='notice')
    action_url = models.CharField(max_length=500, blank=True, null=True, help_text="Direct link to suitable task")
    action_label = models.CharField(max_length=100, blank=True, null=True, default="View Details", help_text="Button text for suitable task")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='received_notifications', help_text="Target student or null for global")
    is_global = models.BooleanField(default=True)
    read_by = models.ManyToManyField(User, blank=True, related_name='read_notifications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.title}"

    @property
    def icon_class(self):
        icon_map = {
            'course': 'fas fa-graduation-cap',
            'lesson': 'fas fa-play-circle',
            'live_class': 'fas fa-video',
            'exam': 'fas fa-clipboard-check',
            'document': 'fas fa-file-alt',
            'assignment': 'fas fa-tasks',
            'notice': 'fas fa-bullhorn',
            'coins': 'fas fa-coins',
            'system': 'fas fa-bell',
        }
        return icon_map.get(self.notification_type, 'fas fa-bell')

    @property
    def badge_color(self):
        color_map = {
            'course': '#00f3ff',      # Neon Cyan
            'lesson': '#38bdf8',      # Light Blue
            'live_class': '#ff3366',  # Neon Red/Pink
            'exam': '#00e676',        # Emerald Green
            'document': '#bc13fe',    # Neon Purple
            'assignment': '#ffaa00',  # Amber
            'notice': '#f59e0b',      # Yellow
            'coins': '#ffd700',       # Gold
            'system': '#94a3b8',      # Slate
        }
        return color_map.get(self.notification_type, '#00f3ff')

    @property
    def badge_bg(self):
        bg_map = {
            'course': 'rgba(0, 243, 255, 0.12)',
            'lesson': 'rgba(56, 189, 248, 0.12)',
            'live_class': 'rgba(255, 51, 102, 0.12)',
            'exam': 'rgba(0, 230, 118, 0.12)',
            'document': 'rgba(188, 19, 254, 0.12)',
            'assignment': 'rgba(255, 170, 0, 0.12)',
            'notice': 'rgba(245, 158, 11, 0.12)',
            'coins': 'rgba(255, 215, 0, 0.15)',
            'system': 'rgba(148, 163, 184, 0.12)',
        }
        return bg_map.get(self.notification_type, 'rgba(0, 243, 255, 0.12)')

    @property
    def badge_text(self):
        type_names = dict(self.NOTIFICATION_TYPES)
        return type_names.get(self.notification_type, 'Notice')

class LiveClass(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='live_classes', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    meeting_link = models.URLField()
    date_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date_time']

    def __str__(self):
        return self.title

class LibraryDocument(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='General')
    file = models.FileField(upload_to='library_docs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title

# --- NEW: OVERALL PROGRESS TRACKING MODELS ---
class LiveClassAttendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='class_attendance')
    live_class = models.ForeignKey(LiveClass, on_delete=models.CASCADE, related_name='attendees')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'live_class')

    def __str__(self):
        return f"{self.student.username} joined {self.live_class.title}"

class DocumentView(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_views')
    document = models.ForeignKey(LibraryDocument, on_delete=models.CASCADE, related_name='viewers')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'document')

    def __str__(self):
        return f"{self.student.username} read {self.document.title}"

# --- NEW: Lesson Comment Model ---
class LessonComment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.student.username} on {self.lesson.title}"

# 🚀 NEW: ASSIGNMENT SYSTEM (FOR FACULTY PANEL "PENDING ASSIGNMENTS")

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    file = models.FileField(upload_to='assignments/briefs/', blank=True, null=True, help_text="Brief attachment in PDF, DOCX, ZIP, image, etc.")
    due_date = models.DateTimeField()
    total_marks = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.course.title}"

    @property
    def file_extension(self):
        if self.file and self.file.name:
            return self.file.name.split('.')[-1].upper()
        return ''

    @property
    def file_name(self):
        if self.file and self.file.name:
            import os
            return os.path.basename(self.file.name)
        return ''

    @property
    def is_past_due(self):
        if self.due_date:
            return timezone.now() > self.due_date
        return False


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    file = models.FileField(upload_to='assignments/submissions/', blank=True, null=True)
    text_answer = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_graded = models.BooleanField(default=False)
    marks_obtained = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f"{self.student.username} -> {self.assignment.title}"

    @property
    def is_late(self):
        if self.assignment and self.assignment.due_date and self.submitted_at:
            return self.submitted_at > self.assignment.due_date
        return False

    @property
    def file_extension(self):
        if self.file and self.file.name:
            return self.file.name.split('.')[-1].upper()
        return ''

    @property
    def file_name(self):
        if self.file and self.file.name:
            import os
            return os.path.basename(self.file.name)
        return ''



# 9. AI FEATURES MODELS

# 1. AI Code Reviewer & Optimizer
class AICodeSubmission(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, null=True, blank=True)
    code_content = models.TextField()
    language = models.CharField(max_length=50, default='Python')
    
    # AI Response fields
    ai_feedback = models.TextField(blank=True, null=True)
    optimized_code = models.TextField(blank=True, null=True)
    suggestions = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Code Review: {self.student.username} ({self.language})"

# 2. AI Personalized Study Roadmap
class StudyRoadmap(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    target_skill = models.CharField(max_length=200, help_text="e.g. Full Stack Python")
    duration_weeks = models.IntegerField(default=4)
    
    # Stores the generated JSON roadmap
    roadmap_data = models.TextField(help_text="Stores JSON data of the schedule")
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Roadmap for {self.student.username}: {self.target_skill}"

# 3. AI Proctoring Logs (For Exams)
class ProctoringLog(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    
    violation_type = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    screenshot = models.ImageField(upload_to='proctoring_proofs/', blank=True, null=True)
    
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Violation: {self.student.username} in {self.exam.title}"

# 4. Smart Video Notes (Magic Notes)
class AIVideoNote(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    
    summary = models.TextField(help_text="AI Generated Summary")
    key_points = models.TextField(help_text="Bullet points extracted from video")
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notes for {self.lesson.title} - {self.student.username}"

# 8. SIGNALS

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if kwargs.get('raw', False):
        return
    try:
        instance.profile.save()
    except Exception:
        pass

@receiver(post_delete, sender=LibraryDocument)
def delete_document_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)

# --- 🔔 REAL-TIME NOTIFICATION SIGNALS (ADMIN ADDS CONTENT / TASKS) ---

@receiver(post_save, sender=Course)
def notify_on_course_created(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        try:
            Notification.objects.create(
                title=f"New Course: {instance.title}",
                message=f"A brand new course '{instance.title}' is now open! Check out the modules and enroll to begin your journey.",
                notification_type='course',
                action_url=f"/courses/",
                action_label="Explore Course",
                is_global=True,
            )
        except Exception:
            pass

@receiver(post_save, sender=Lesson)
def notify_on_lesson_created(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        try:
            course_title = instance.course.title if instance.course else "Course"
            action_url = f"/courses/watch/{instance.course.id}/{instance.id}/" if instance.course else "/courses/"
            Notification.objects.create(
                title=f"New Lesson: {instance.title}",
                message=f"Lesson #{instance.order} '{instance.title}' has been added to '{course_title}'. Continue your learning!",
                notification_type='lesson',
                action_url=action_url,
                action_label="Watch Lesson",
                is_global=True,
            )
        except Exception:
            pass

@receiver(post_save, sender=LiveClass)
def notify_on_live_class_created(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        try:
            time_str = instance.date_time.strftime("%d %b %Y at %I:%M %p") if instance.date_time else "soon"
            c_info = f" for '{instance.course.title}'" if instance.course else ""
            Notification.objects.create(
                title=f"Live Class: {instance.title}",
                message=f"Live interactive class '{instance.title}'{c_info} is scheduled for {time_str}. Make sure to attend!",
                notification_type='live_class',
                action_url="/live-classes/",
                action_label="Join Live Class",
                is_global=True,
            )
        except Exception:
            pass

@receiver(post_save, sender=Exam)
def notify_on_exam_created(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        try:
            c_info = f" in '{instance.course.title}'" if instance.course else ""
            Notification.objects.create(
                title=f"New AI Exam: {instance.title}",
                message=f"A new exam assessment '{instance.title}'{c_info} is ready. Complete this task to earn certifications & coins!",
                notification_type='exam',
                action_url=f"/take-exam/{instance.id}/",
                action_label="Start Exam",
                is_global=True,
            )
        except Exception:
            pass

@receiver(post_save, sender=LibraryDocument)
def notify_on_library_doc_created(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        try:
            c_info = f" [{instance.course.title}]" if instance.course else ""
            Notification.objects.create(
                title=f"New Study Material: {instance.title}",
                message=f"Study resource '{instance.title}'{c_info} ({instance.category}) has been uploaded to the Digital Library.",
                notification_type='document',
                action_url="/library/",
                action_label="View in Library",
                is_global=True,
            )
        except Exception:
            pass

@receiver(post_save, sender=Assignment)
def notify_on_assignment_created(sender, instance, created, **kwargs):
    if kwargs.get('raw', False):
        return
    if created:
        try:
            c_info = f" in '{instance.course.title}'" if instance.course else ""
            due_str = f" Due date: {instance.due_date.strftime('%d %b %Y')}." if hasattr(instance, 'due_date') and instance.due_date else ""
            action_url = f"/courses/watch/{instance.course.id}/" if instance.course else "/courses/"
            Notification.objects.create(
                title=f"New Assignment Task: {instance.title}",
                message=f"A new course assignment '{instance.title}'{c_info} has been posted.{due_str} Submit your solution on time!",
                notification_type='assignment',
                action_url=action_url,
                action_label="Submit Task",
                is_global=True,
            )
        except Exception:
            pass


# --- 🚀 FIX: GOOGLE PROFILE PICTURE & NAME AUTO-SAVE ---

@receiver(user_logged_in)
def fetch_google_profile_pic(request, user, **kwargs):
    try:
        # Find the Google social account linked to this user
        social_account = SocialAccount.objects.filter(user=user, provider='google').first()
        
        if social_account:
            # 1. FIX MISSING NAMES FROM GOOGLE
            name_updated = False
            
            if not user.first_name:
                user.first_name = social_account.extra_data.get('given_name', '')
                name_updated = True
                
            if not user.last_name:
                user.last_name = social_account.extra_data.get('family_name', '')
                name_updated = True
                
            # Fallback if given_name/family_name isn't available but 'name' is
            if not user.first_name and social_account.extra_data.get('name'):
                user.first_name = social_account.extra_data.get('name')
                name_updated = True

            # Save the user if name was updated
            if name_updated:
                user.save(update_fields=['first_name', 'last_name'])

            # 2. FIX PROFILE PICTURE
            if not user.profile.profile_pic:
                picture_url = social_account.extra_data.get('picture')
                if picture_url:
                    high_res_url = picture_url
                    for low_res in ['=s96-c', '=s50-c', '=s64-c']:
                        if low_res in high_res_url:
                            high_res_url = high_res_url.replace(low_res, '=s384-c')
                            break
                    response = requests.get(high_res_url)
                    if response.status_code != 200:
                        response = requests.get(picture_url)
                    if response.status_code == 200:
                        file_name = f"{user.username}_google_pic.jpg"
                        user.profile.profile_pic.save(file_name, ContentFile(response.content), save=True)
                    
    except Exception as e:
        print(f"Could not save Google profile data: {e}")

# --- COURSE COMMUNITY / WHATSAPP STYLE GROUP ---

class CourseGroupMessage(models.Model):
    # which course group is being message to .
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='group_messages')
    
    # Who is sending the message (must be a student enrolled in the course)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    
    # --- NEW: Reply Feature ---
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    
    # Message text and image/file (can be either or both)
    text = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='group_attachments/', blank=True, null=True)
    
    # --- NEW: Pin Feature ---
    is_pinned = models.BooleanField(default=False)
    
    # --- PREVIOUS NEW: Edit Feature (Restored) ---
    is_edited = models.BooleanField(default=False)
    
    # --- NEW: Chat Bounty System ---
    bounty_amount = models.PositiveIntegerField(default=0, help_text="Amount offered for solving this question")
    is_bounty_resolved = models.BooleanField(default=False)
    bounty_winner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name="won_bounties"
    )
    
    # While sending the message
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Like WhatsApp, your messages are on top and new messages are for water.
        ordering = ['created_at'] 

    def __str__(self):
        return f"Message by {self.sender.username} in {self.course.title}"

# --- NEW: Emoji Reaction Model ---
class MessageReaction(models.Model):
    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('haha', '😂'),
        ('sad', '😢'),
        ('wow', '😮'),
        ('handshake', '🤝'),
        ('fire', '🔥'),
    ]
    
    message = models.ForeignKey(CourseGroupMessage, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=20, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user', 'reaction_type')

    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type} on Msg ID {self.message.id}"


# 🚀 NEW: BOUNTY ARENA (SYNTAX SINGULARITY) MODELS

class DynamicBountyProblem(models.Model):
    """
    Stores the AI-generated coding problem specific to a student.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bounty_problems')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='bounty_problems')
    language = models.CharField(max_length=50)
    topic = models.CharField(max_length=100)
    difficulty = models.CharField(max_length=50)
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    base_code = models.TextField()
    
    base_bounty_coins = models.IntegerField(default=10)
    is_solved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.student.username}"

class ProblemTestCase(models.Model):
    """
    Stores the test cases for each generated problem.
    Some are visible to students, some are hidden for backend evaluation.
    """
    problem = models.ForeignKey(DynamicBountyProblem, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=True)

    def __str__(self):
        return f"Test Case for {self.problem.title} (Hidden: {self.is_hidden})"

class BountySubmission(models.Model):
    """
    Tracks every time a student submits code to solve a Bounty Problem.
    """
    problem = models.ForeignKey(DynamicBountyProblem, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bounty_submissions')
    
    submitted_code = models.TextField()
    status = models.CharField(max_length=50) # e.g., 'Accepted', 'Wrong Answer', 'Runtime Error'
    execution_time = models.FloatField(null=True, blank=True)
    
    attempt_number = models.IntegerField(default=1)
    earned_coins = models.IntegerField(default=0)
    multiplier_applied = models.FloatField(default=1.0)
    
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submission by {self.student.username} - {self.status}"


# 10. STUDENT ACTIVITY TRACKING (Admin Analytics)

class StudentActivity(models.Model):
    """
    Tracks every student action for admin analytics dashboards.
    Enables daily/weekly/monthly activity graphs and per-student tracking.
    """
    ACTIVITY_TYPES = [
        ('login', 'Login'),
        ('lesson_watch', 'Lesson Watched'),
        ('quiz_taken', 'Quiz Taken'),
        ('quiz_passed', 'Quiz Passed'),
        ('assignment_submit', 'Assignment Submitted'),
        ('bounty_attempt', 'Bounty Attempted'),
        ('bounty_solved', 'Bounty Solved'),
        ('course_enroll', 'Course Enrolled'),
        ('chat_message', 'Chat Message Sent'),
        ('profile_update', 'Profile Updated'),
        ('course_complete', 'Course Completed'),
        ('code_review', 'Code Review Requested'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Student Activities'

    def __str__(self):
        return f"{self.student.username} - {self.get_activity_type_display()} ({self.created_at.strftime('%d %b %Y %H:%M')})"


def log_student_activity(user, activity_type, description='', course=None, metadata=None):
    """
    Helper function to log student activity from anywhere in the codebase.
    Usage: log_student_activity(request.user, 'login', 'User logged in')
    """
    if user and user.is_authenticated and user.is_student and not user.is_staff and not user.is_superuser:
        StudentActivity.objects.create(
            student=user,
            activity_type=activity_type,
            description=description,
            course=course,
            metadata=metadata or {}
        )


# 11. PAYMENT SYSTEM (Coupons + Transaction Ledger)

class Coupon(models.Model):
    code = models.CharField(max_length=30, unique=True)
    percent_off = models.PositiveIntegerField(default=10, help_text="Discount percentage (1-100)")
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.valid_until and self.valid_until < timezone.now():
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def __str__(self):
        return f"{self.code} ({self.percent_off}% off)"


class Payment(models.Model):
    METHOD_CHOICES = [
        ('card', 'Credit / Debit Card'),
        ('upi', 'UPI'),
        ('net', 'Net Banking'),
        ('wallet', 'Wallet'),
        ('qr', 'QR Code'),
        ('coins', 'LMS Coins'),
    ]
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, related_name='payments')
    txn_id = models.CharField(max_length=30, unique=True, editable=False)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    provider = models.CharField(max_length=30, blank=True, help_text="visa / gpay / sbi / paytm ...")
    instrument = models.CharField(max_length=60, blank=True, help_text="Masked card / UPI id / bank name")
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    coins_spent = models.PositiveIntegerField(default=0)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.txn_id:
            import uuid
            self.txn_id = 'TXN' + timezone.now().strftime('%y%m%d') + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.txn_id} - {self.student.username} - {self.status}"