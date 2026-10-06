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
    """Removes <think>...</think> blocks that Qwen models add, including unclosed tags."""
    if not text:
        return text
    # Remove closed <think>...</think>
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Also strip any trailing/unclosed <think>... if generation cut off mid-thought
    cleaned = re.sub(r'<think>.*', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()

# 1. CORE AI COMMUNICATOR (The Brain)

def get_groq_response(system_instruction, user_message, max_tokens=2500):
    """
    Sends data to Groq API with automatic model fallback to avoid OTPM rate limits.
    Models: qwen/qwen3.8-27b -> openai/gpt-oss-120b -> openai/gpt-oss-20b
    """
    models_to_try = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    last_error = None
    for model_name in models_to_try:
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
                model=model_name,
                temperature=0.3,
                max_tokens=max_tokens,
                timeout=65.0,
            )
            raw = chat_completion.choices[0].message.content or ""
            return strip_think_tags(raw)
        except Exception as e:
            last_error = e
            print(f"Groq API error on model {model_name}: {e}. Trying fallback model...")
            continue

    print(f"All Groq models failed. Last error: {last_error}")
    return "I am having trouble connecting to the brain right now. Please try again later."

# 2. FILE EXTRACTION UTILITIES

def extract_text_from_file(file_path):
    """
    Extracts text from PDF, DOCX, DOC, or TXT files using modern and fallback parsers.
    """
    if not file_path or not os.path.exists(file_path):
        return ""

    text = ""
    try:
        ext = file_path.split('.')[-1].lower()
        
        if ext == 'pdf':
            # Attempt 1: Try modern pypdf
            try:
                import pypdf
                with open(file_path, 'rb') as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
            except Exception as pe:
                print(f"pypdf reader error: {pe}, attempting PyPDF2...")
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            extracted = page.extract_text()
                            if extracted:
                                text += extracted + "\n"
                except Exception as p2e:
                    print(f"PyPDF2 reader error: {p2e}")
                        
        elif ext in ['docx', 'doc']:
            try:
                import docx
                doc = docx.Document(file_path)
                for para in doc.paragraphs:
                    if para.text:
                        text += para.text + "\n"
            except Exception as docx_err:
                print(f"docx Document error: {docx_err}")
                # Fallback for older .doc or plain files: extract printable ASCII
                try:
                    with open(file_path, 'rb') as f:
                        raw = f.read()
                        printable = re.findall(rb'[\x20-\x7E\r\n]{4,}', raw)
                        text = " ".join([p.decode('ascii', errors='ignore') for p in printable])
                except Exception:
                    pass
                
        elif ext in ['txt', 'csv', 'md']:
            for enc in ['utf-8', 'latin-1', 'cp1252', 'utf-16']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        text = f.read()
                    if text:
                        break
                except Exception:
                    continue
                
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""
        
    return text.strip()

# 3. AI QUIZ GENERATOR (Powered by Groq)

def generate_quiz_from_text(text, num_questions=15):
    """
    Uses Groq AI to generate a JSON quiz from the provided text.
    Generates between 10 and 20 questions (default 15).
    Returns list of dicts: [{'question': str, 'options': [str, str, str, str], 'answer': int (0-3)}]
    """
    if not text or len(text.strip()) < 20:
        return []

    # Ensure num_questions is between 10 and 20
    try:
        num_questions = max(10, min(20, int(num_questions)))
    except (ValueError, TypeError):
        num_questions = 15

    system_prompt = f"""/no_think
You are an expert Teacher and Quiz Generator.
Task: Create {num_questions} unique, high-quality multiple-choice questions based strictly on the provided text.

OUTPUT FORMAT (Strict JSON):
Return ONLY a valid raw JSON list of objects. No extra text, no markdown formatting, no thinking tags, no explanation.
Structure:
[
    {{
        "question": "Question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": 0
    }}
]
Rules:
- Generate exactly {num_questions} distinct questions covering different concepts from the text.
- "options" must be a list of exactly 4 choices.
- "answer" must be an integer index (0 for Option A, 1 for Option B, 2 for Option C, 3 for Option D).
"""
    
    # Allow larger text window (up to 15,000 characters) for rich question variety
    safe_text = text[:15000] 
    
    # Scale max_tokens dynamically to ensure 10-20 questions fit comfortably without truncation
    needed_tokens = max(2500, num_questions * 220)
    
    try:
        response = get_groq_response(system_prompt, f"Generate quiz from this text:\n\n{safe_text}", max_tokens=needed_tokens)
        if not response or "trouble connecting to the brain" in response:
            return []

        # Clean up markdown backticks
        clean_response = response.replace('```json', '').replace('```', '').strip()
        
        quiz_data = None
        # Try direct parse
        try:
            quiz_data = json.loads(clean_response)
        except Exception:
            pass

        # Try regex search for array [...]
        if quiz_data is None:
            match_arr = re.search(r'\[.*\]', clean_response, re.DOTALL)
            if match_arr:
                try:
                    quiz_data = json.loads(match_arr.group(0))
                except Exception:
                    pass

        # Try regex search for object {...}
        if quiz_data is None:
            match_obj = re.search(r'\{.*\}', clean_response, re.DOTALL)
            if match_obj:
                try:
                    quiz_data = json.loads(match_obj.group(0))
                except Exception:
                    pass

        # If wrapped in dict (e.g. {"quiz": [...]}), extract inner list
        if isinstance(quiz_data, dict):
            for key in ['quiz', 'questions', 'data', 'mcqs', 'quiz_data']:
                if key in quiz_data and isinstance(quiz_data[key], list):
                    quiz_data = quiz_data[key]
                    break
            if isinstance(quiz_data, dict):
                for val in quiz_data.values():
                    if isinstance(val, list):
                        quiz_data = val
                        break

        # Fallback: extract individual valid JSON question objects using regex
        if not isinstance(quiz_data, list):
            object_matches = re.findall(r'\{\s*"question".*?"options"\s*:\s*\[.*?\].*?"answer"\s*:\s*[^}]+\}', clean_response, re.DOTALL)
            if object_matches:
                repaired = []
                for m in object_matches:
                    try:
                        obj = json.loads(m)
                        if isinstance(obj, dict) and ('question' in obj or 'question_text' in obj):
                            repaired.append(obj)
                    except Exception:
                        continue
                if repaired:
                    quiz_data = repaired

        if not isinstance(quiz_data, list):
            print(f"Quiz data could not be parsed as list. Raw: {clean_response[:300]}")
            return []

        # Normalize questions
        normalized = []
        for item in quiz_data:
            if not isinstance(item, dict):
                continue
            q_text = item.get('question') or item.get('question_text') or item.get('text') or ''
            if not q_text:
                continue

            raw_opts = item.get('options') or item.get('choices') or []
            if isinstance(raw_opts, dict):
                opts = [str(raw_opts.get(k, '')) for k in ['A', 'B', 'C', 'D'] if k in raw_opts]
                if not opts:
                    opts = [str(v) for v in raw_opts.values()]
            elif isinstance(raw_opts, list):
                opts = [str(o) for o in raw_opts]
            else:
                opts = []

            while len(opts) < 4:
                opts.append(f"Option {chr(65 + len(opts))}")
            opts = opts[:4]

            raw_ans = item.get('answer')
            if raw_ans is None:
                raw_ans = item.get('correct_option', 0)

            ans_idx = 0
            if isinstance(raw_ans, int):
                if 0 <= raw_ans <= 3:
                    ans_idx = raw_ans
                elif 1 <= raw_ans <= 4:
                    ans_idx = raw_ans - 1
            elif isinstance(raw_ans, str):
                cleaned_ans = raw_ans.strip().upper()
                if cleaned_ans in ['A', 'OPTION A', 'A)']:
                    ans_idx = 0
                elif cleaned_ans in ['B', 'OPTION B', 'B)']:
                    ans_idx = 1
                elif cleaned_ans in ['C', 'OPTION C', 'C)']:
                    ans_idx = 2
                elif cleaned_ans in ['D', 'OPTION D', 'D)']:
                    ans_idx = 3
                elif cleaned_ans.isdigit():
                    num = int(cleaned_ans)
                    ans_idx = num if num <= 3 else (num - 1 if num <= 4 else 0)
                else:
                    for i, o in enumerate(opts):
                        if cleaned_ans == o.strip().upper():
                            ans_idx = i
                            break

            normalized.append({
                'question': q_text,
                'options': opts,
                'answer': ans_idx
            })

        return normalized
        
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