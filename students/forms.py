import re
from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    Course, 
    Notification, 
    LiveClass, 
    Exam, 
    LibraryDocument, 
    Profile,
    Lesson,
    LessonComment, # UPDATE: Imported LessonComment Model
    CourseGroupMessage,    # Community Chat Message Form
    Assignment,
    AssignmentSubmission,
    SupportTicket
)

User = get_user_model()

# 1. STUDENT REGISTRATION FORM

class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autocomplete': 'given-name'}),
        required=True,
        label="First Name"
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'autocomplete': 'family-name'}),
        required=False,
        label="Last Name"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address', 'autocomplete': 'email', 'autocapitalize': 'none', 'spellcheck': 'false'}),
        required=True,
        label="Email Address"
    )
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (e.g. +91 98765 43210)', 'autocomplete': 'tel', 'id': 'regPhone'}),
        required=False,
        label="Phone Number"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password', 'id': 'regPassword', 'autocomplete': 'new-password'}),
        label="Password",
        help_text="Minimum 8 characters required."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password', 'id': 'regConfirmPassword', 'autocomplete': 'new-password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'password', 'confirm_password', 'stream', 'student_level']
        widgets = {
            'stream': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Science, Arts, Engineering'}),
            'student_level': forms.Select(choices=[
                ('Beginner', 'Beginner'), 
                ('Intermediate', 'Intermediate'), 
                ('Advanced', 'Advanced')
            ], attrs={'class': 'form-control'}),
        }

    def clean_first_name(self):
        first_name = (self.cleaned_data.get('first_name') or '').strip()
        if not first_name:
            raise ValidationError("First name is required.")
        return first_name

    def clean_last_name(self):
        return (self.cleaned_data.get('last_name') or '').strip()

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered. Please login or use a different email.")
        return email

    def clean_phone(self):
        phone = (self.cleaned_data.get('phone') or '').strip()
        if phone:
            digits = re.sub(r'\D', '', phone)
            if len(digits) < 7:
                raise ValidationError("Please enter a valid phone number with at least 7 digits.")
            from django.db.models import Q
            if User.objects.filter(Q(phone=phone) | Q(profile__phone=phone)).exists():
                raise ValidationError("This phone number is already registered. Please login or use a different phone number.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match!")
            
            if len(password) < 8:
                self.add_error('password', "Password must be at least 8 characters long.")
                
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        first_name = (self.cleaned_data.get("first_name") or '').strip()
        last_name = (self.cleaned_data.get("last_name") or '').strip()
        email = (self.cleaned_data.get("email") or '').strip().lower()
        phone = (self.cleaned_data.get("phone") or '').strip()

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone

        # 🌟 Username is directly generated from First Name
        clean_first = re.sub(r'[^a-zA-Z0-9_]', '', first_name.strip().lower())
        if not clean_first:
            clean_first = 'student'
        
        base_user = clean_first
        candidate_username = base_user
        counter = 1
        while User.objects.filter(username__iexact=candidate_username).exists():
            counter += 1
            candidate_username = f"{base_user}{counter}"

        user.username = candidate_username
        user.is_student = True
        user.set_password(self.cleaned_data["password"])
        
        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            if phone:
                profile.phone = phone
            if user.student_id:
                profile.student_id = user.student_id
            profile.save()

        return user


# 2. COURSE CREATION FORM (ADMIN)

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'faculty_name', 'thumbnail', 'price', 'is_coin_purchasable', 'coin_price', 'total_modules', 'difficulty_level', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Course Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed Course Description'}),
            'faculty_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Instructor Name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Course Price (0 for Free)'}),
            'is_coin_purchasable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'coin_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Coin Price'}),
            'total_modules': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Number of Modules'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price < 0:
            raise ValidationError("Price cannot be negative.")
        return price

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get('thumbnail')
        if thumbnail:
            if thumbnail.size > 2 * 1024 * 1024: # 2MB limit
                raise ValidationError("Image file too large ( > 2mb ).")
        return thumbnail

# 2.1. LESSON CREATION FORM

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['course', 'title', 'video_url', 'duration', 'order']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lesson Title'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}), 
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10:00'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# 3. NOTIFICATION FORM

class NotificationForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.filter(is_student=True).order_by('username'),
        required=False,
        empty_label="All Students (Broadcast Global)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type', 'action_url', 'action_label', 'recipient', 'is_global']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mandatory Project Submission'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write notification details or task requirements...'}),
            'notification_type': forms.Select(attrs={'class': 'form-control'}),
            'action_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., /courses/, /my-exams/, /live-classes/ (Optional)'}),
            'action_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Open Task, Start Quiz (Optional)'}),
            'is_global': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# 4. LIVE CLASS FORM

class LiveClassForm(forms.ModelForm):
    class Meta:
        model = LiveClass
        fields = ['title', 'course', 'date_time', 'meeting_link', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class Topic'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'date_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'meeting_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Zoom/Google Meet Link'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_date_time(self):
        date_time = self.cleaned_data.get('date_time')
        if date_time < timezone.now():
            raise ValidationError("Meeting time cannot be in the past!")
        return date_time



# 5. EXAM & QUIZ FORM

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'course', 'exam_link', 'description', 'deadline', 'duration_minutes', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Exam Title'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'exam_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'External Link (e.g. Google Form)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Duration (mins)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# 6. LIBRARY UPLOAD FORM

class LibraryDocumentForm(forms.ModelForm):
    class Meta:
        model = LibraryDocument
        fields = ['course', 'title', 'category', 'file']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}), 
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Document Title'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category (e.g. Notes, Syllabus)'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            valid_extensions = ['pdf', 'docx', 'doc', 'ppt', 'pptx', 'txt']
            if ext not in valid_extensions:
                raise ValidationError("Unsupported file extension. Please upload PDF or Office docs.")
        return file

# 7. PROFILE PICTURE FORM

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_pic']
        widgets = {
           'profile_pic': forms.FileInput(attrs={
               'class': 'form-control', 
               'id': 'id_profile_pic',
               'style': 'display: none;',
               'onchange': 'this.form.submit();'
           })
        }

# 8. LESSON COMMENT FORM

class LessonCommentForm(forms.ModelForm):
    class Meta:
        model = LessonComment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'comment-input', 
                'rows': 3, 
                'placeholder': 'Ask a doubt or share your thoughts...'
            }),
        }

# 9. COMMUNITY CHAT MESSAGE FORM

class CourseGroupMessageForm(forms.ModelForm):
    class Meta:
        model = CourseGroupMessage
        fields = ['text', 'attachment']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 1, 
                'placeholder': 'Type your message to the class...'
            }),
            'attachment': forms.FileInput(attrs={
                'class': 'form-control', 
                'style': 'display: none;', 
                'id': 'chat_attachment',
                'onchange': 'this.form.submit();'
            })
        }


# 10. ASSIGNMENT MANAGEMENT FORMS

class AssignmentForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
        }),
        required=True
    )

    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'file', 'due_date', 'total_marks']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Full-Stack REST API & Database Migration'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide instructions, evaluation criteria, and submission specifications...'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '100'}),
        }


class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['file', 'text_answer']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'text_answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add code explanations, live deployment links, GitHub repos, or execution notes...'
            }),
        }


# ========================================================
# 11. STUDENT PROFILE UPDATE FORM & SUPPORT TICKET FORM
# ========================================================

class StudentProfileUpdateForm(forms.Form):
    first_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address', 'autocomplete': 'email'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number (e.g. +91 98765 43210)', 'autocomplete': 'tel'})
    )
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Write a brief bio about yourself, your skills, goals...'})
    )
    profile_pic = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'id': 'modal_profile_pic'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            self.fields['phone'].initial = self.user.phone or (getattr(self.user, 'profile', None) and self.user.profile.phone) or ''
            if hasattr(self.user, 'profile') and self.user.profile:
                self.fields['bio'].initial = self.user.profile.bio or ''

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            raise ValidationError("Email is required.")
        query = User.objects.filter(email__iexact=email)
        if self.user:
            query = query.exclude(pk=self.user.pk)
        if query.exists():
            raise ValidationError("This email address is already registered with another account.")
        return email

    def save(self):
        if not self.user:
            return None
        self.user.first_name = self.cleaned_data.get('first_name', self.user.first_name)
        self.user.last_name = self.cleaned_data.get('last_name', self.user.last_name)
        self.user.email = self.cleaned_data.get('email')
        phone = self.cleaned_data.get('phone', '').strip()
        self.user.phone = phone
        self.user.save(update_fields=['first_name', 'last_name', 'email', 'phone'])

        profile = getattr(self.user, 'profile', None)
        if not profile:
            profile = Profile.objects.create(user=self.user)
        profile.phone = phone
        profile.bio = self.cleaned_data.get('bio', '').strip()
        pic = self.cleaned_data.get('profile_pic')
        if pic:
            profile.profile_pic = pic
        profile.save()
        return self.user


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['category', 'priority', 'subject', 'message']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'ticket_category'}),
            'priority': forms.Select(attrs={'class': 'form-control', 'id': 'ticket_priority'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief summary (e.g. Password reset assistance needed)', 'id': 'ticket_subject'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Provide details about your problem, registered contact info, error messages, or request...',
                'id': 'ticket_message'
            }),
        }