import os
import re
from groq import Groq
from django.conf import settings
from .models import Course, Enrollment

# Helper: Strip <think>...</think> tags from Qwen model responses
def strip_think_tags(text):
    """Removes <think>...</think> blocks that Qwen models add, including trailing blocks."""
    if not text:
        return text
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

def get_course_context():
    """
    Fetches course data from the database to give the AI real-time context.
    Includes: Title, Instructor (Faculty), Level, and Description.
    """
    courses = Course.objects.filter(is_published=True)
    if not courses.exists():
        return "No specific course data is currently available on the platform."
    
    course_list_text = "Here is the list of active courses on Learning-365:\n"
    for c in courses[:25]:
        course_list_text += f"- Course: '{c.title}' | Mentor: {c.faculty_name} | Level: {c.difficulty_level} | Description: {c.description[:120]}...\n"
    return course_list_text

def generate_learning_assistant_response(user_message, chat_history=[], user=None):
    """
    Generates an intelligent, personalized academic response using Groq AI with multi-model fallback.
    """
    client = Groq(
        api_key=settings.GROQ_API_KEY, 
    )

    db_context = get_course_context()

    student_details = ""
    if user and user.is_authenticated:
        enrolled_titles = list(Enrollment.objects.filter(student=user).values_list('course__title', flat=True))
        student_details = f"""
    CURRENT LOGGED-IN STUDENT INFORMATION:
    - Name: {user.first_name or user.username}
    - Username: @{user.username}
    - LMS Coins Balance: {getattr(user, 'lms_coins', 0)} Coins
    - Actively Enrolled Courses: {', '.join(enrolled_titles) if enrolled_titles else 'Not enrolled in any course yet'}
    """

    system_prompt = f"""/no_think
ROLE & PERSONA:
You are 'Learning-365 AI', the premier Academic Mentor, Code Tutor, and LMS Companion.
You speak in a warm, professional, encouraging, and human tone.
Use clear formatting (markdown bolding, lists, and code blocks with syntax highlighting).
Use occasional emojis (🚀, 💡, 🎯, 💻) to keep learning exciting.

{student_details}

PLATFORM KNOWLEDGE BASE & SYSTEM DIRECTORY:
- Courses Catalog: Browse all available tech tracks at /courses/
- My Assessments / AI Exams: Take proctored exams and earn coins at /my-exams/
- Digital Library: Access lecture PDFs and viva question banks at /library/
- Syntax Singularity: Solve coding bounties and earn coins at /syntax-singularity/
- Cloud Compiler / IDE: Built-in code runner for Python, JavaScript, C++, and Java.
- LMS Coins Economy: Students earn +100 LMS coins for scoring 80%+ on exams, and extra coins on coding bounties. Coins can be used to unlock premium paid courses for free!

ACTIVE COURSES ON PLATFORM:
{db_context}

GUIDELINES:
1. When asked about user's courses, progress, or coins, refer directly to CURRENT LOGGED-IN STUDENT INFORMATION above.
2. Provide clear, direct, and actionable guidance. If explaining code, write clean, well-commented code snippets.
3. Suggest platform destinations with markdown links (e.g. [View My Exams](/my-exams/) or [Browse Courses](/courses/)).
4. Keep answers friendly, structured, and focused on student learning, technical education, and career growth.
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-6:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    # Multi-model fallback chain to guarantee 100% uptime without 429 limits
    models_to_try = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    for model_name in models_to_try:
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.6,
                max_tokens=1000,
                timeout=45.0,
            )
            raw = chat_completion.choices[0].message.content or ""
            return strip_think_tags(raw)
        except Exception as e:
            print(f"AI Service Error on model {model_name}: {e}. Trying fallback...")
            continue

    return "I am having trouble connecting to my brain right now! Please try again in a moment. 🚀"