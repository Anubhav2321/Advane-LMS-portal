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
    FacultyProfile, #  NEW: Added FacultyProfile
    Assignment,           # 🚀 NEW: Added Assignment Model
    AssignmentSubmission  # 🚀 NEW: Added Assignment Submission Model
)

User = get_user_model()

# 1. STUDENT REGISTRATION FORM

class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
        required=True
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        required=True
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}),
        label="Password",
        help_text="Minimum 8 characters required."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'confirm_password', 'stream', 'student_level']
        widgets = {
            'stream': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Science, Arts'}),
            'student_level': forms.Select(choices=[
                ('Beginner', 'Beginner'), 
                ('Intermediate', 'Intermediate'), 
                ('Advanced', 'Advanced')
            ], attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered. Please login.")
        return email

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
        user.set_password(self.cleaned_data["password"])
        user.username = self.cleaned_data["email"]
        
        if commit:
            user.save()
            if not hasattr(user, 'profile'):
                Profile.objects.create(user=user)
        return user


# 2. COURSE CREATION FORM (ADMIN)

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'faculty_name', 'thumbnail', 'price', 'total_modules', 'difficulty_level', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Course Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed Course Description'}),
            'faculty_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Instructor Name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Course Price (0 for Free)'}),
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
    class Meta:
        model = Notification
        fields = ['title', 'message', 'is_global']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notice Headline'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Notice Content...'}),
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
           'profile_pic': forms.FileInput(attrs={'class': 'form-control', 'id': 'id_profile_pic'})
        }

# 8. LESSON COMMENT FORM (NEW ADDITION)

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

# 9. FACULTY REGISTRATION FORM (CUSTOM ADMIN PANEL) 🚀 NEW

class FacultyRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter temporary password'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}))
    experience_years = forms.IntegerField(required=False, initial=0, widget=forms.NumberInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unique Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Faculty Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

    def save(self, commit=True):
        # 1. Create the User
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password']) # Hash the password
        user.is_student = False  # Not a student
        user.is_faculty = True   # Make them a faculty member
        
        if commit:
            user.save()
            # 2. Create their Faculty Profile automatically
            FacultyProfile.objects.create(
                user=user,
                department=self.cleaned_data.get('department'),
                experience_years=self.cleaned_data.get('experience_years')
            )
        return user


# 🚀 NEW: FACULTY PANEL FORMS

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date', 'total_marks']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Assignment Title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write the assignment instructions here...'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 100'}),
        }

    def __init__(self, *args, **kwargs):
        faculty = kwargs.pop('faculty', None)
        super().__init__(*args, **kwargs)
        if faculty:
            # Dropdown e sudhu oi course gulo dekhabe jeta ei faculty ke assign kora ache
            self.fields['course'].queryset = Course.objects.filter(assigned_faculty=faculty)

class AssignmentGradeForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['marks_obtained', 'feedback']
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter marks'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Feedback for the student...'}),
        }

class FacultyProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = FacultyProfile
        fields = ['department', 'experience_years', 'specialization', 'background']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. IT Department'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Artificial Intelligence'}),
            'background': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}),
        }