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

    def __str__(self):
        role = "Teacher" if self.is_teacher else ("Faculty" if self.is_faculty else "Student")
        return f"{self.username} | {role}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

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

    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"


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
    title = models.CharField(max_length=255, default="New Notice")
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_global = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

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

# --- NEW: Lesson Comment Model ---
class LessonComment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.student.username} on {self.lesson.title}"

# =================================================================
# 🚀 NEW: ASSIGNMENT SYSTEM (FOR FACULTY PANEL "PENDING ASSIGNMENTS")
# =================================================================

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateTimeField()
    total_marks = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    file = models.FileField(upload_to='assignments/submissions/', blank=True, null=True)
    text_answer = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    is_graded = models.BooleanField(default=False)
    marks_obtained = models.FloatField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} -> {self.assignment.title}"

# =================================================================


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
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

@receiver(post_delete, sender=LibraryDocument)
def delete_document_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)

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