from django.urls import path
from students import community_views
from . import views
from . import compiler_service  # NEW: Import the compiler service for Docker Execution

urlpatterns = [

    # Authentication
    path('', views.login_view, name='login'),  
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Student Panel Features
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('courses/', views.all_courses, name='all_courses'),
    path('courses/watch/<int:course_id>/', views.course_watch, name='course_watch'),
    path('courses/enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    
    path('live-classes/', views.live_classes, name='live_classes'),
    path('library/', views.library_view, name='library'),
    path('exams/', views.exams_view, name='exams'),
    path('profile/', views.profile_view, name='profile'),
    
    # Payments
    path('payment/<int:course_id>/', views.payment_page, name='payment_page'),
    path('payment/process/<int:course_id>/', views.process_payment, name='process_payment'),
    path('payment/coins/<int:course_id>/', views.purchase_with_coins, name='purchase_with_coins'),

    # API (Chatbot)
    path('api/ai-chat/', views.ai_chat, name='ai_chat'),

    # Admin Panel System & Forms
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/create-course/', views.admin_create_course, name='admin_create_course'),
    path('admin-panel/create-notice/', views.admin_create_notice, name='admin_create_notice'),
    path('admin-panel/create-live-class/', views.admin_create_live_class, name='admin_create_live_class'),
    path('admin-panel/create-exam/', views.admin_create_exam, name='admin_create_exam'),
    path('admin-panel/add-library/', views.add_library_view, name='add_library'),
    path('admin-panel/course/<int:course_id>/add-lesson/', views.admin_add_lesson, name='admin_add_lesson'),
    
    # 🚀 NEW: Create Faculty Route
    path('admin-panel/create-faculty/', views.admin_create_faculty, name='admin_create_faculty'),
    
    # Student Management List & Actions
    path('admin-panel/students/', views.admin_student_list, name='admin_student_list'),
    path('admin-panel/students/<int:user_id>/', views.admin_student_detail, name='admin_student_detail'),
    path('admin-panel/students/<int:user_id>/update/', views.admin_update_student_info, name='admin_update_student_info'),
    path('admin-panel/students/<int:user_id>/block/', views.admin_toggle_block, name='admin_toggle_block'),
    path('admin-panel/students/<int:user_id>/delete/', views.admin_delete_student, name='admin_delete_student'),
    path('admin-panel/students/<int:user_id>/reset-pass/', views.admin_reset_password, name='admin_reset_password'),

    # Course, Doc, Enrollment Management
    path('admin-panel/courses/', views.admin_course_list, name='admin_course_list'),
    path('admin-panel/courses/<int:course_id>/edit/', views.admin_edit_course, name='admin_edit_course'),
    path('admin-panel/courses/<int:course_id>/delete/', views.admin_delete_course, name='admin_delete_course'),
    path('admin-panel/documents/', views.admin_document_list, name='admin_document_list'),
    path('admin-panel/documents/<int:doc_id>/edit/', views.admin_edit_document, name='admin_edit_document'),
    path('admin-panel/documents/<int:doc_id>/delete/', views.admin_delete_document, name='admin_delete_document'),
    path('admin-panel/enrollments/', views.admin_enrollment_list, name='admin_enrollment_list'),
    path('admin-panel/enrollments/<int:enroll_id>/delete/', views.admin_delete_enrollment, name='admin_delete_enrollment'),

    # Quiz APIs
    path('exams/generate-quiz/', views.generate_quiz_view, name='generate_quiz'),
    path('exams/save-quiz/', views.save_quiz_view, name='save_quiz'),
    path('exams/take/<int:exam_id>/', views.take_quiz_view, name='take_quiz'),
    path('exams/submit/<int:exam_id>/', views.submit_quiz_view, name='submit_quiz'),

    # COMMUNITY CHAT & API URLS 
    path('community/<slug:slug>/', community_views.course_community_chat, name='course_community_chat'),
    path('api/chat/pin/<int:message_id>/', community_views.toggle_pin_message, name='toggle_pin_message'),
    path('api/chat/react/<int:message_id>/', community_views.add_message_reaction, name='add_message_reaction'),
    path('api/chat/user-info/<int:user_id>/', community_views.get_student_info, name='get_student_info'),
    path('api/chat/delete/<int:message_id>/', community_views.delete_message, name='delete_message'),
    path('api/chat/edit/<int:message_id>/', community_views.edit_message, name='edit_message'),
    path('api/chat/execute-local-code/', compiler_service.run_code_in_docker, name='run_code_in_docker'),
    
    # 🚀 SYNTAX SINGULARITY URLS
    path('syntax-singularity/', views.syntax_singularity_view, name='syntax_singularity'),
    path('api/generate-challenge/', views.generate_ai_challenge, name='generate_challenge'),
    path('api/bounty/submit/', views.submit_bounty_code, name='submit_bounty_code'),

    # 🚀 FACULTY PANEL SYSTEM
    path('faculty-panel/', views.faculty_dashboard, name='faculty_dashboard'),
]