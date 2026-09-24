import os
from groq import Groq
from django.conf import settings
from .models import Course  # Importing Course model to get real data

def get_course_context():
    """
    Fetches course data from the database to give the AI 'Context'.
    Includes: Title, Instructor (Faculty), Level, and Description.
    """
    courses = Course.objects.filter(is_published=True)
    
    if not courses.exists():
        return "No specific course data is currently available on the platform."
    
    # Building the context string
    # CRITICAL FIX: Added 'faculty_name' so AI knows the mentor.
    course_list_text = "Here is the list of active courses on Learning-365:\n"
    for c in courses:
        course_list_text += f"- Course: '{c.title}' | Mentor: {c.faculty_name} | Level: {c.difficulty_level} | Description: {c.description[:150]}...\n"
    
    return course_list_text

def generate_learning_assistant_response(user_message, chat_history=[]):
    """
    Generates a response using Llama 3 with Memory and Database Context.
    """
    
    # 1. Initialize Groq Client
    client = Groq(
        api_key=settings.GROQ_API_KEY, 
    )

    # 2. Get Real-time Data (Context)
    db_context = get_course_context()

    # 3. The "Next Level" System Prompt (Updated for Friendly Persona)
    system_prompt = f"""
    ROLE & PERSONA:
    You are 'Learning-365 AI', a super friendly, enthusiastic, and expert coding mentor.
    You are NOT a robot; speak like a helpful human teacher. 
    Use emojis occasionally (🚀, 💡, ✅) to make the conversation lively.

    YOUR KNOWLEDGE BASE (REAL-TIME DATA):
    {db_context}
    
    STRICT GUIDELINES:
    1. **Context First:** If the user asks about mentors, courses, or details, look at the KNOWLEDGE BASE above. 
       - Example: If asked "Who is the React mentor?", check the list for the React course and answer with the Mentor's name.
    
    2. **Domain Restriction:** Only answer questions about Education, Coding, Technology, and Career guidance.
       - If asked about movies/politics, politely refuse: "I'm here to help you learn! Let's focus on your studies. 🎓"

    3. **Memory:** Remember what the user said in previous messages (provided in history).

    4. **Tone:** Encouraging, clear, and beginner-friendly. Keep answers concise unless asked for detailed code.
    """

    # 4. Construct Message Chain (System + History + User)
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append History (Fixes the "Forgetting" issue)
    # We take the last 6 messages to keep context without exceeding token limits
    for msg in chat_history[-6:]:
        messages.append(msg)

    # Append Current User Message
    messages.append({"role": "user", "content": user_message})

    try:
        # 5. Call AI API
        chat_completion = client.chat.completions.create(
            messages=messages,
            # UPDATE: Changed to a stable model with better free-tier limits
            model="llama-3.1-8b-instant",  # Updated from qwen
            temperature=0.7,         
            max_tokens=400,
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm having a bit of trouble connecting to my brain right now! 🧠💥 Please try again in a moment."