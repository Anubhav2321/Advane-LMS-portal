from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importing all views from students app (Main Views)
from students.views import (
    # 1. Public
    home_view, 
    contact_developers_view,

    # 2. Auth
    register_view, 
    login_view, 
    logout_view,

    # 3. Student Features
    student_dashboard, 
    all_courses, 
    enroll_course, 
    course_watch,       
    live_classes, 
    library_view, 
    profile_view,       #  Profile View

    # 4. Payment System
    payment_page,
    process_payment,
    purchase_with_coins, # 🪙 NEW: Imported for Coin Payment

    # 👉 🚀 NEW: SYNTAX SINGULARITY (AI Coding Arena)
    syntax_singularity_view,
    generate_ai_challenge,
    submit_bounty_code,  # 🚀 NEW: Added this import!

    # 5. Quiz & AI
    student_exam_list,  # Exam List View
    take_exam,          # Take Exam View
    generate_quiz_view, 
    save_quiz_view, 
    submit_quiz_view,   
    ai_chat,
    execute_code_api,   # 👉 🚀 NEW: Imported the Docker Code Execution API

    # 6. Admin Panel (Dashboard)
    admin_dashboard, 
    
    # 7. Admin Management (Lists & Edits)
    admin_student_list, 
    admin_student_detail,
    admin_update_student_info,
    admin_toggle_block, 
    admin_delete_student, 
    admin_reset_password,

    admin_course_list,          
    admin_edit_course,          
    admin_delete_course,        

    admin_document_list,        
    admin_edit_document,        
    admin_delete_document,      

    admin_enrollment_list,      
    admin_delete_enrollment,    
    
    # 8. Admin Actions (Create Forms)
    admin_create_course,
    admin_create_notice,
    admin_create_live_class,
    admin_create_exam,
    add_library_view,
    admin_add_lesson, # Lesson View
    
    # 🚀 NEW: Faculty Actions (Kept in views.py)
    admin_create_faculty 
)

# 🚀 NEW: Importing Faculty Views from the new file
from students.faculty_views import (
    faculty_dashboard,
    faculty_courses,
    faculty_live_studio,
    faculty_digital_archive,
    faculty_exam_monitor,
    faculty_community,
    faculty_profile
)

#  9. ADVANCED COMMUNITY CHAT URLs 
from students.community_views import (
    course_community_chat,
    toggle_pin_message,
    add_message_reaction,
    get_student_info,
    delete_message,   # ADDED for Delete API
    edit_message,     # ADDED for Edit API
    accept_bounty     #  NEW: ADDED for Bounty System API
)

urlpatterns = [

    # 1. Django Default Admin
    path('admin/', admin.site.urls),

    #  NEW: Allauth URLs for Google Login 
    path('accounts/', include('allauth.urls')), 

    # 2. Public Pages
    path('', home_view, name='home'),
    path('contact/', contact_developers_view, name='contact_developers'),

    # 3. Authentication
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # 4. Student Dashboard & Features
    path('dashboard/', student_dashboard, name='dashboard'),
    path('profile/', profile_view, name='profile'), 

    # Courses
    path('courses/', all_courses, name='all_courses'),
    path('courses/enroll/<int:course_id>/', enroll_course, name='enroll_course'),
    
    # Payment Flow
    path('courses/payment/<int:course_id>/', payment_page, name='payment_page'),
    path('courses/payment/<int:course_id>/process/', process_payment, name='process_payment'),
    
    #  NEW: BUY COURSE WITH COINS URL 
    path('courses/payment/<int:course_id>/coin-purchase/', purchase_with_coins, name='purchase_with_coins'),

    # Watch Course
    path('courses/watch/<int:course_id>/', course_watch, name='course_watch'),
    path('courses/watch/<int:course_id>/<int:lesson_id>/', course_watch, name='course_watch'),

    # Core Features
    path('live-classes/', live_classes, name='live_classes'),
    path('library/', library_view, name='library'),
    
    #  9. ADVANCED COMMUNITY CHAT URLs 
    path('community/<slug:slug>/', course_community_chat, name='course_community_chat'),
    
    # AJAX APIs for Chat Features
    path('api/chat/pin/<int:message_id>/', toggle_pin_message, name='toggle_pin_message'),
    path('api/chat/react/<int:message_id>/', add_message_reaction, name='add_message_reaction'),
    path('api/chat/user-info/<int:user_id>/', get_student_info, name='get_student_info'),
    
    #  NEW: Delete & Edit Messages API 
    path('api/chat/delete/<int:message_id>/', delete_message, name='delete_message'),
    path('api/chat/edit/<int:message_id>/', edit_message, name='edit_message'),
    
    #  NEW: Bounty System API ---
    path('api/chat/accept-bounty/<int:reply_id>/', accept_bounty, name='accept_bounty'), 
    
    #  NEW: Local Docker Code Execution API (THE MISSING LINK IS NOW HERE!)
    path('api/chat/execute-code/', execute_code_api, name='execute_code_api'),
    
    # 👉 🚀 NEW: SYNTAX SINGULARITY (LeetCode Style AI Arena URLs)
    path('syntax-singularity/', syntax_singularity_view, name='syntax_singularity'),
    path('api/generate-challenge/', generate_ai_challenge, name='generate_challenge'),
    path('api/submit-bounty/', submit_bounty_code, name='submit_bounty'), # 🚀 NEW: Added this route!
    
    # 5. Quiz & AI System
    # New Exam Logic (Course Linked)
    path('my-exams/', student_exam_list, name='student_exam_list'), 
    path('take-exam/<int:exam_id>/', take_exam, name='take_exam'), 
    
    # AI Quiz Generation
    path('quiz/generate/', generate_quiz_view, name='generate_quiz'),
    path('quiz/save/', save_quiz_view, name='save_quiz'),
    path('quiz/submit/<int:exam_id>/', submit_quiz_view, name='submit_quiz'), 
    
    # AI Chatbot Endpoint
    path('api/ai-chat/', ai_chat, name='ai_chat'),

    # 6. Admin Panel System
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    
    #  A. Student Management 
    path('admin-panel/students/', admin_student_list, name='admin_student_list'),
    path('admin-panel/students/<int:user_id>/', admin_student_detail, name='admin_student_detail'),
    path('admin-panel/students/<int:user_id>/update/', admin_update_student_info, name='admin_update_student_info'),
    path('admin-panel/students/<int:user_id>/block/', admin_toggle_block, name='admin_toggle_block'),
    path('admin-panel/students/<int:user_id>/delete/', admin_delete_student, name='admin_delete_student'),
    path('admin-panel/students/<int:user_id>/reset-pass/', admin_reset_password, name='admin_reset_password'),

    #  B. Course Management (List & Edit) 
    path('admin-panel/courses/', admin_course_list, name='admin_course_list'),
    path('admin-panel/courses/edit/<int:course_id>/', admin_edit_course, name='admin_edit_course'),
    path('admin-panel/course/delete/<int:course_id>/', admin_delete_course, name='admin_delete_course'),

    #  C. Library Management (List & Edit) 
    path('admin-panel/documents/', admin_document_list, name='admin_document_list'),
    path('admin-panel/documents/edit/<int:doc_id>/', admin_edit_document, name='admin_edit_document'),
    path('admin-panel/documents/delete/<int:doc_id>/', admin_delete_document, name='admin_delete_document'),

    #  D. Enrollment Management 
    path('admin-panel/enrollments/', admin_enrollment_list, name='admin_enrollment_list'),
    path('admin-panel/enrollments/delete/<int:enroll_id>/', admin_delete_enrollment, name='admin_delete_enrollment'),

    #  E. Content Creation (Forms) 
    path('admin-panel/create-course/', admin_create_course, name='admin_create_course'),
    path('admin-panel/create-notice/', admin_create_notice, name='admin_create_notice'),
    path('admin-panel/create-class/', admin_create_live_class, name='admin_create_live_class'),
    path('admin-panel/create-exam/', admin_create_exam, name='admin_create_exam'),
    path('admin-panel/library/add/', add_library_view, name='add_library'),
    
    #  F. Lesson Management 
    path('admin-panel/course/<int:course_id>/add-lesson/', admin_add_lesson, name='admin_add_lesson'),
    
    # 🚀 NEW: Faculty Creation Route (Admin action)
    path('admin-panel/create-faculty/', admin_create_faculty, name='admin_create_faculty'),
    
    # 🚀 NEW: Faculty Dashboard & Features Routes (Faculty actions)
    path('faculty-panel/', faculty_dashboard, name='faculty_dashboard'),
    path('faculty-panel/my-courses/', faculty_courses, name='faculty_courses'),
    path('faculty-panel/live-studio/', faculty_live_studio, name='faculty_live_studio'),
    path('faculty-panel/digital-archive/', faculty_digital_archive, name='faculty_digital_archive'),
    path('faculty-panel/exam-monitor/', faculty_exam_monitor, name='faculty_exam_monitor'),
    path('faculty-panel/community/', faculty_community, name='faculty_community'),
    path('faculty-panel/profile/', faculty_profile, name='faculty_profile'),
    
    # System Logout for Faculty
    path('faculty-panel/disconnect/', logout_view, name='faculty_logout'),
]

# Media & Static Files Configuration
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if settings.STATICFILES_DIRS:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    else:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)