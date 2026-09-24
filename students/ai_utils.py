import os
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

# 1. CORE AI COMMUNICATOR (The Brain)

def get_groq_response(system_instruction, user_message):
    """
    Sends data to Groq API and retrieves the AI response.
    Updated Model: qwen/qwen3.8-27b (Latest Supported)
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
            #  UPDATE: Changed deprecated model to the latest one 
            model="qwen/qwen3.8-27b",  # Updated: llama-3.3-70b-versatile was removed from Groq
            temperature=0.5,
            max_tokens=800,
        )
        return chat_completion.choices[0].message.content
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
    system_prompt = f"""
    You are an expert Teacher and Quiz Generator.
    Task: Create {num_questions} multiple-choice questions based strictly on the provided text.
    
    OUTPUT FORMAT (Strict JSON):
    Return a raw JSON list of objects. Do not include markdown formatting (like ```json).
    Structure:
    [
        {{
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": 0  // The index of the correct option (0, 1, 2, or 3)
        }}
    ]
    """
    
    # Truncate text to avoid token limits
    safe_text = text[:15000] 
    
    try:
        # Call AI
        response = get_groq_response(system_prompt, f"Generate quiz from this text:\n\n{safe_text}")
        
        # Clean up response (sometimes AI adds markdown backticks)
        clean_response = response.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        quiz_data = json.loads(clean_response)
        return quiz_data
        
    except json.JSONDecodeError:
        print("Error decoding AI JSON response")
        return []
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return []