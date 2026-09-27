from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Profile, Course, Lesson, Enrollment, 
    Notification, LiveClass, LibraryDocument, 
    Exam, Question, QuizResult, Quiz,
    CourseGroupMessage,
    LessonComment, DynamicBountyProblem, 
    ProblemTestCase, BountySubmission, MessageReaction,
    AICodeSubmission, StudyRoadmap, ProctoringLog, AIVideoNote
)

# 1. Custom User Admin (Student/Teacher Info)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'is_student', 'is_teacher', 'student_level', 'lms_coins')
    list_filter = ('is_student', 'is_teacher', 'student_level')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Academic Info', {'fields': ('is_student', 'is_teacher', 'student_level', 'stream', 'lms_coins')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Academic Info', {'fields': ('is_student', 'is_teacher', 'student_level', 'stream', 'lms_coins')}),
    )

admin.site.register(User, CustomUserAdmin)


# 2. Course & Lesson Admin

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('title', 'faculty_name', 'price', 'total_modules', 'is_published', 'is_coin_purchasable', 'created_at')
    list_filter = ('is_published', 'difficulty_level', 'is_coin_purchasable')
    search_fields = ('title', 'description', 'faculty_name')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_preview', 'is_completed')
    list_filter = ('course', 'is_preview')


# 3. Exam & Question Admin (Updated Logic)

# Inline for Questions within Exam
class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1  # Default will show 1 question.

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ('title', 'course', 'duration_minutes', 'total_marks', 'is_active')
    list_filter = ('is_active', 'course')
    search_fields = ('title',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'exam', 'correct_option', 'marks')
    list_filter = ('exam',)


# 4. Other Features Admin

admin.site.register(Enrollment)
admin.site.register(Notification)
admin.site.register(LiveClass)
admin.site.register(LibraryDocument)
admin.site.register(QuizResult)
admin.site.register(Quiz) # Dummy Quiz model registered if needed   
admin.site.register(LessonComment)

#  5. COMMUNITY CHAT ADMIN 

@admin.register(CourseGroupMessage)
class CourseGroupMessageAdmin(admin.ModelAdmin):
    list_display = ('course', 'sender', 'created_at', 'text', 'is_pinned', 'bounty_amount', 'is_bounty_resolved')
    list_filter = ('course', 'created_at', 'is_pinned', 'is_bounty_resolved')
    search_fields = ('text', 'sender__username', 'course__title')

admin.site.register(MessageReaction)

#  6. AI & BOUNTY ARENA ADMIN 

@admin.register(DynamicBountyProblem)
class DynamicBountyProblemAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'course', 'language', 'difficulty', 'base_bounty_coins', 'is_solved')
    list_filter = ('language', 'difficulty', 'is_solved', 'course')
    search_fields = ('title', 'student__username')

@admin.register(ProblemTestCase)
class ProblemTestCaseAdmin(admin.ModelAdmin):
    list_display = ('problem', 'is_hidden')
    list_filter = ('is_hidden',)

@admin.register(BountySubmission)
class BountySubmissionAdmin(admin.ModelAdmin):
    list_display = ('problem', 'student', 'status', 'earned_coins', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('student__username', 'problem__title')

# AI Feature Admins
admin.site.register(AICodeSubmission)
admin.site.register(StudyRoadmap)
admin.site.register(ProctoringLog)
admin.site.register(AIVideoNote)