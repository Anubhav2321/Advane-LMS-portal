import os
import re
import json
# pyrefly: ignore [missing-import]
import PyPDF2
# pyrefly: ignore [missing-import]
import docx
from groq import Groq
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Initialize Groq Client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Helper: Strip <think>...</think> tags from Qwen model responses
def strip_think_tags(text):
    """Removes <think>...</think> blocks that Qwen models add."""
    if not text:
        return text
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

# 1. CORE AI COMMUNICATOR (The Brain)

def get_groq_response(system_instruction, user_message, max_tokens=900):
    """
    Sends data to Groq API and retrieves the AI response.
    Updated Model: qwen/qwen3.8-27b (Latest Supported)
    Note: Free tier has 1000 output tokens/min limit, so max_tokens defaults to 900.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_instruction,
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="qwen/qwen3.8-27b",
            temperature=0.5,
            max_tokens=max_tokens,
        )
        raw = chat_completion.choices[0].message.content
        return strip_think_tags(raw)
    except Exception as e:
        print(f"Error in Groq API: {e}")
        return "I am having trouble connecting to the brain right now. Please try again later."

# 2. FILE EXTRACTION UTILITIES

def extract_text_from_file(file_path):
    """
    Extracts text from PDF, DOCX, or TXT files.
    """
    text = ""
    try:
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                        
        elif ext in ['doc', 'docx']:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
                
        elif ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""
        
    return text.strip()

# 3. AI QUIZ GENERATOR (Powered by Groq)

def generate_quiz_from_text(text, num_questions=5):
    """
    Uses Groq AI to generate a JSON quiz from the provided text.
    """
    system_prompt = f"""/no_think
You are an expert Teacher and Quiz Generator.
Task: Create {num_questions} multiple-choice questions based strictly on the provided text.

OUTPUT FORMAT (Strict JSON):
Return ONLY a raw JSON list of objects. No extra text, no markdown formatting, no explanation.
Structure:
[
    {{
        "question": "Question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": 0
    }}
]
"""
    
    # Truncate text to avoid token limits
    safe_text = text[:6000] 
    
    try:
        # Call AI (keep max_tokens within free-tier OTPM limit of 1000)
        response = get_groq_response(system_prompt, f"Generate quiz from this text:\n\n{safe_text}", max_tokens=900)
        
        # Clean up response (remove markdown backticks, think tags already stripped)
        clean_response = response.replace('```json', '').replace('```', '').strip()
        
        # Extract just the JSON array from the response
        match = re.search(r'\[.*\]', clean_response, re.DOTALL)
        if match:
            clean_response = match.group(0)
        
        # Parse JSON
        quiz_data = json.loads(clean_response)
        return quiz_data
        
    except json.JSONDecodeError as e:
        print(f"Error decoding AI JSON response: {e}")
        print(f"Raw response was: {response[:500]}")
        return []
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return []


# 4. SMART LESSON NOTES GENERATOR (Powered by Groq)

def generate_ai_lesson_notes(lesson_title, lesson_content="", course_title=""):
    """
    Generates smart, structured study notes and key takeaways for a lesson using Groq AI.
    Returns a dict with 'summary' and 'key_points'.
    """
    system_prompt = """/no_think
You are an expert AI Academic Tutor and technical summarizer.
Summarize the educational lesson into concise, ultra-clear key takeaways.

OUTPUT FORMAT (Strict JSON):
Return ONLY a raw JSON object with no markdown formatting around it:
{
    "summary": "Clear, informative 2-3 sentence executive summary of the lesson core concepts.",
    "key_points": [
        "Core takeaway 1 with specific technical detail",
        "Core takeaway 2 highlighting practical application",
        "Core takeaway 3 pointing out best practices or common pitfalls",
        "Pro tip or interview question note"
    ]
}
"""
    prompt_text = f"Course: {course_title}\nLesson: {lesson_title}\n"
    if lesson_content and len(lesson_content.strip()) > 10:
        prompt_text += f"Lesson Details/Notes:\n{lesson_content[:3000]}\n"
    else:
        prompt_text += f"Generate deep technical educational notes and key concepts covering '{lesson_title}' in the context of '{course_title}'."
        
    try:
        response = get_groq_response(system_prompt, prompt_text, max_tokens=750)
        clean_response = response.replace('```json', '').replace('```', '').strip()
        match = re.search(r'\{.*\}', clean_response, re.DOTALL)
        if match:
            clean_response = match.group(0)
        data = json.loads(clean_response)
        summary = data.get('summary', '').strip()
        key_points = data.get('key_points', [])
        if isinstance(key_points, list):
            formatted_points = "\n".join([f"• {str(p).strip().lstrip('•*- ')}" for p in key_points if str(p).strip()])
        else:
            formatted_points = str(key_points)
            
        if not summary:
            summary = f"Essential concepts and architectural deep dive into {lesson_title} in {course_title}."
        if not formatted_points:
            formatted_points = f"• Mastered foundational patterns of {lesson_title}.\n• Hands-on exercises and practical implementations.\n• Industry standards and optimal architectures."
            
        return {
            'summary': summary,
            'key_points': formatted_points
        }
    except Exception as e:
        print(f"Error generating AI lesson notes: {e}")
        return {
            'summary': f"This lesson covers key theoretical and practical frameworks for {lesson_title} within {course_title}. Follow along with the code and practical demonstrations.",
            'key_points': f"• Key mechanics of {lesson_title}\n• Industry-standard patterns and implementation strategies\n• Error handling, edge cases, and optimization benchmarks\n• Integration with the broader architecture"
        }