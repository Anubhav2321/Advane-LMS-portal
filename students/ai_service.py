import os
import re
from groq import Groq
from django.conf import settings
from .models import Course, Enrollment, Exam, LibraryDocument, LiveClass, LessonProgress, DynamicBountyProblem

# Helper: Strip <think>...</think> tags from Qwen model responses
def strip_think_tags(text):
    """Removes <think>...</think> blocks that Qwen models add, including trailing blocks."""
    if not text:
        return text
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

def get_platform_knowledge():
    """
    Fetches comprehensive real-time portal data from the database.
    Covers courses, exams, library documents, live classes, and coding bounties on Learning-365.
    """
    context_parts = []

    # 1. Active Courses
    courses = Course.objects.filter(is_published=True)
    if courses.exists():
        course_lines = []
        for c in courses[:20]:
            coin_info = f" | Coin Price: {c.coin_price} Coins" if c.is_coin_purchasable else ""
            course_lines.append(
                f"- [Course ID {c.id}] '{c.title}' (Slug: {c.slug}) | Mentor: {c.faculty_name} | Level: {c.difficulty_level} | Price: ₹{c.price}{coin_info} | URL: /courses/watch/{c.id}/"
            )
        context_parts.append("ACTIVE LEARNING-365 COURSES CATALOG:\n" + "\n".join(course_lines))
    else:
        context_parts.append("ACTIVE COURSES: No published courses found currently.")

    # 2. Active Exams
    exams = Exam.objects.filter(is_active=True)
    if exams.exists():
        exam_lines = []
        for ex in exams[:10]:
            course_name = ex.course.title if ex.course else "General Assessment"
            exam_lines.append(
                f"- [Exam ID {ex.id}] '{ex.title}' | Course: {course_name} | Duration: {ex.duration_minutes} Mins | Total Marks: {ex.total_marks} | Pass Mark: 60% | URL: /take-exam/{ex.id}/"
            )
        context_parts.append("ACTIVE EXAMINATIONS & QUIZZES:\n" + "\n".join(exam_lines))

    # 3. Syntax Singularity (Algorithmic Bounties)
    try:
        bounties = DynamicBountyProblem.objects.filter(is_solved=False)[:6]
        if bounties.exists():
            b_lines = [f"- [{b.language.upper()}] '{b.title}' ({b.topic}) | Difficulty: {b.difficulty} | Bounty Reward: +{b.base_bounty_coins} Coins" for b in bounties]
            context_parts.append("ACTIVE SYNTAX SINGULARITY BOUNTIES:\n" + "\n".join(b_lines))
    except Exception:
        pass

    # 4. Library Documents
    docs = LibraryDocument.objects.all()[:8]
    if docs.exists():
        doc_lines = [f"- '{d.title}' (Category: {d.category})" for d in docs]
        context_parts.append("DIGITAL LIBRARY DOCUMENTS:\n" + "\n".join(doc_lines))

    # 5. Live Classes
    classes = LiveClass.objects.all()[:5]
    if classes.exists():
        class_lines = [f"- '{lc.title}' | Schedule: {lc.date_time}" for lc in classes]
        context_parts.append("SCHEDULED LIVE SESSIONS:\n" + "\n".join(class_lines))

    return "\n\n".join(context_parts)

def get_student_dossier(user):
    """
    Compiles real-time profile, enrollments, and progress for the logged-in student.
    """
    if not user or not user.is_authenticated:
        return "CURRENT USER STATUS: Anonymous / Guest Visitor (Not logged in)."

    enrollments = Enrollment.objects.filter(student=user).select_related('course')
    enrolled_info = []
    for e in enrollments:
        progress_data = e.get_real_progress()
        enrolled_info.append(
            f"  • Course: '{e.course.title}' | Real Progress: {progress_data['percent']}% ({progress_data['completed']}/{progress_data['total']} tasks) | Status: {'Completed' if e.is_completed else 'In Progress'} | Watch URL: /courses/watch/{e.course.id}/"
        )

    completed_lessons_count = LessonProgress.objects.filter(student=user, is_completed=True).count()
    try:
        solved_bounties_count = DynamicBountyProblem.objects.filter(student=user, is_solved=True).count()
    except Exception:
        solved_bounties_count = 0

    return f"""CURRENT LOGGED-IN CADET DOSSIER (LEARNING-365):
- Full Name: {user.first_name or user.username} {user.last_name or ''}
- Username: @{user.username}
- Student Stream / Department: {getattr(user, 'stream', 'Engineering')}
- Skill Level: {getattr(user, 'student_level', 'Beginner')}
- LMS Coins Treasury: {getattr(user, 'lms_coins', 0)} Coins
- Total Completed Video Lessons: {completed_lessons_count}
- Solved Syntax Singularity Bounties: {solved_bounties_count}
- Enrolled Courses ({len(enrolled_info)} total):
{chr(10).join(enrolled_info) if enrolled_info else '  • No courses enrolled currently. Guide the student to explore /courses/.'}
"""

def generate_learning_assistant_response(user_message, chat_history=[], user=None):
    """
    Generates an authoritative, precise, and portal-bounded response using Groq AI with multi-model fallback.
    """
    client = Groq(api_key=settings.GROQ_API_KEY)

    platform_data = get_platform_knowledge()
    student_data = get_student_dossier(user)

    system_prompt = f"""/no_think
ROLE & IDENTITY:
You are the "Learning-365 AI Copilot" — the official, built-in intelligent academic & technical assistant for the Learning-365 LMS Portal.
You operate directly inside the Learning-365 Student Dashboard.
Your tone is ultra-professional, tech-sharp, encouraging, structured, and authoritative.

STRICT DOMAIN BOUNDARY & KNOWLEDGE DIRECTIVE:
1. You have COMPLETE, EXHAUSTIVE knowledge of the Learning-365 LMS portal, its courses, features, exams, coding arena, compiler, and coin economy.
2. You are STRICTLY DEDICATED to Learning-365 and academic/computer science topics (coding, algorithms, web development, exams, and platform navigation).
3. If a student asks questions about the outside world that are unrelated to computer science, academic learning, or Learning-365 (e.g., celebrity gossip, pop culture drama, politics, external entertainment), politely decline and redirect:
   "I am the dedicated Learning-365 Copilot, calibrated specifically for your coursework, coding challenges, exams, and portal navigation. How can I help you with your Learning-365 studies today?"
4. Always prioritize the student's real enrolled courses, active exams, and coin balance when answering personal queries.

{student_data}

{platform_data}

EXHAUSTIVE LEARNING-365 FEATURE DIRECTORY:
1. Student Dashboard (/dashboard/):
   - Real-time 14-Day Learning Velocity telemetry chart tracking tasks, watched lectures, and quizzes.
   - Progress Matrix: Real-time progress rings for enrolled courses based on lessons, quizzes, live classes, documents, and assignments.
   - Quick access to recent documents, urgent notices, and cadet stats.
2. Course Watch & Learning Engine (/courses/watch/<course_id>/):
   - Interactive lecture video player with curriculum drawer.
   - Progress Tracking: Watch time is monitored automatically; when watch time reaches 80%, the lesson marks complete and rewards +20 LMS Coins!
   - AI Smart Lesson Notes: Instant bullet concept summaries for any lesson via /api/lesson/ai-notes/<lesson_id>/.
3. Examinations & Quizzes (/my-exams/ and /take-exam/<exam_id>/):
   - Course-linked evaluations and AI quizzes with countdown timers and anti-cheat proctoring.
   - Passing threshold is 60%. Passing is required for course completion and certificate issuance.
   - Coin Rewards: +50 Coins for a perfect 100% score, +25 Coins for scoring 80%+.
4. Syntax Singularity - AI Coding Arena (/syntax-singularity/):
   - LeetCode-style competitive algorithmic arena.
   - Dynamic AI challenge generation across Python, C++, Java, and JavaScript.
   - Automated sandbox evaluation with visible and hidden test cases.
   - Correct submissions reward instant LMS Coin bounties (+10 to +100 Coins).
5. Cloud Code Studio & Compiler (IDE):
   - In-browser sandbox code runner powered by Piston engine.
   - Supports Python 3.10+, C++17, Java 15+, and JavaScript / Node.js with custom stdin.
   - Accessible anywhere via the dashboard IDE launcher.
6. LMS Coins Treasury & Economy:
   - Students earn coins by watching lectures (+20), scoring high on exams (+25/+50), and solving syntax bounties (+10 to +100).
   - Students can spend coins to UNLOCK PAID COURSES FOR 100% FREE without cash via /courses/payment/<course_id>/coin-purchase/!
7. Course Community & Discussion Forum (/community/<slug>/):
   - Course-specific discussion rooms with message pinning, emoji reactions, and code sharing.
   - Peer Bounty System: Students can attach coin bounties to questions to reward peers who provide solutions!
8. Digital Library (/library/):
   - Textbooks, lecture PDFs, and whitepapers.
   - 1-Click AI Quiz Generator converts any library document into an interactive practice quiz.
9. Live Classes (/live-classes/):
   - Scheduled interactive live lectures with faculty meeting links. Attendance logs automatically.
10. Cadet Profile & Certification (/profile/):
    - Update bio, stream, password, and avatar (auto-clarified with facial clarity filter).
    - Completion certificates unlock when real course progress reaches 100% and passing grades (≥60%) are earned on exams. Includes verifiable QR code.

RESPONSE FORMATTING RULES:
- Use clean Markdown: bold headers (###), bold keywords (**text**), bullet points (•), and clickable markdown links ([Page Name](/url/)).
- When explaining code or algorithms, provide clean, well-commented code blocks with language tags (```python, ```cpp, etc.).
- Keep explanations structured, actionable, and directly tied to the student's Learning-365 journey.
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-6:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    # Multi-model fallback chain for 100% uptime
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
            print(f"Learning-365 AI Service fallback trigger on {model_name}: {e}")
            continue

    return "⚠️ The Learning-365 AI Core is momentarily recalibrating. Please retry your query in a few moments."