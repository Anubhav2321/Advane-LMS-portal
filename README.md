# 🎓 Learning-365: The Syntax Singularity Ecosystem
### *Next-Generation AI-Powered EdTech Platform*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-green?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![AI-Groq](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange?style=for-the-badge)](https://groq.com/)

**Learning-365** is an advanced Learning Management System (LMS) designed to go beyond standard video courses. It leverages Artificial Intelligence to help students build coding logic through a highly gamified, cyberpunk-themed environment. The platform features an advanced "Syntax Singularity" coding arena, a real-time community hub, and a secure local Docker-based code execution engine.

---

## 🌟 Key Features

### 🧠 1. Syntax Singularity (AI Coding Arena)
- **Dynamic Problem Generation:** Utilizes Groq AI (Llama 3.3) to generate unique coding challenges based on the student's selected topic, language, and difficulty level.
- **AI Logic Check:** Instead of just checking output, the AI evaluates the student's raw logic and syntax, providing human-like feedback and hints.
- **One-Shot Bounty System:** Students are rewarded with "LMS Coins" only if they successfully solve the mission on their **First Attempt**. Subsequent attempts evaluate the code but yield no financial reward, encouraging dry-runs and deep thinking.

### 🏆 2. Gamified Economy & Social Features
- **LMS Coins:** A virtual currency earned by completing video lessons, passing quizzes, and solving AI coding missions.
- **Global Leaderboard (Hall of Fame):** Displays the top 10 hackers on the platform based on their LMS Coin balance, featuring custom gold, silver, and bronze glowing tiers.
- **GitHub-Style Contribution Heatmap:** A visual 365-day activity graph on the student profile that glows neon-cyan to track daily coding streaks.

### 💬 3. Community Commlink (Real-Time Hub)
- **Interactive Multi-Threaded Chat:** A Discord/WhatsApp style secure commlink for course enrolled students. Supports image, document, and audio sharing.
- **Bounty Support:** Students can attach a "Coin Bounty" to their questions. The user who provides the correct solution is awarded the coins via a 1-click "Accept & Award" button.
- **Integrated IDE & Emojis:** Students can open a floating VS Code-style editor directly inside the chat, run code via Docker, and attach the output to their messages.

### 🛡️ 4. Advanced System Architecture
- **Local Docker Engine:** Executes student code securely inside isolated Docker containers with strict CPU and memory limits to prevent infinite loops and malicious commands.
- **Auto-Google Profile Sync:** Automatically fetches and saves high-resolution Google profile pictures and handles missing names during Google OAuth login.
- **Deep Work Focus Mode:** An integrated Pomodoro timer with Lo-Fi study beats to help students maintain focus during intense coding sessions.

---

## 🛠️ Installation & Setup Guide

Follow these steps to deploy the Learning-365 ecosystem on your local machine:

### Prerequisites
- Python 3.10+
- Docker Desktop (Required for the Local Execution Engine)
- Groq Cloud API Key

### 1. Clone the Repository
```bash
git clone [https://github.com/Anubhav2321/Learning-365.git](https://github.com/Anubhav2321/Learning-365.git)
cd Learning-365
### 1. Clone the Repository
```bash
git clone [https://github.com/Anubhav2321/Learning-365.git](https://github.com/Anubhav2321/Learning-365.git)
cd Learning-365
```
### 2. Virtual Environment Setup
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Mac/Linux
source venv/bin/activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Configure Environment Variables
Create a .env file in the project's main directory and enter the following data:
```bash
DEBUG=True
SECRET_KEY=your_django_secret_key
GROQ_API_KEY=your_groq_api_key_here
```
### 5. Docker Setup (Optional for IDE)
To enable the safe execution of code inside the VS Code chat modal, you must build the local compiler image:
```bash
docker build -t local-compiler .
```
### 6. Database Migrations & Superuser
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```
### 7. Initialize the Mainframe
```bash
python manage.py runserver
```
Visit: ```http://127.0.0.1:8000/``` in your browser.

### 📂 System Architecture
```
Learning-365/
├── core/                   # Main Django configuration & URL routing
├── students/               # Core Application Logic
│   ├── models.py           # Database Schema (Users, Courses, Bounty Arena)
│   ├── views.py            # Backend Controllers (Leaderboard, Heatmap, API)
│   ├── ai_service.py       # Groq AI communication protocol
│   └── temp_codes/         # Ephemeral storage for Docker execution
├── templates/              # Glassmorphic & Cyberpunk HTML UI
│   ├── landing.html        # Main Entry Node
│   ├── student_dashboard/  # Leaderboard & Active Missions
│   ├── student_profile/    # Cyber-Log Timeline & Contribution Graph
│   ├── community_chat/     # Discord-style Commlink & VS Code Modal
│   └── syntax_singularity/ # The AI Coding Arena
├── static/                 # CSS, JS, and Premium VFX Assets
├── media/                  # Profile Pictures & Course Thumbnails
├── Dockerfile              # Local compiler container specifications
└── manage.py
```
## 👤 About the Architect
## Anubhav Samanta

🎓 BCA Student at Techno India University.

💻 Full-Stack Developer specializing in AI integration and UI/UX design.

🛠️ Creator of ARIS (Advanced Desktop AI Assistant).

🏅 Certified in AI Fundamentals & Prompt Engineering by IBM SkillsBuild.

Connect:

GitHub

 <a href="https://www.linkedin.com/in/anubhav-samanta-187549379 " target="_blank">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
  </a> 

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

"Code, Learn, Conquer. Repeat 365 days."
***

### 📝 Next Steps for Your Project:
All your files (`models.py`, `views.py`, HTML templates) are now fully structured, bug-free, and aligned with this professional documentation. 

If you are ready to push this to GitHub, simply:
1. Create the `README.md` file in your project folder.
2. Paste the text above.
3. Run `git add .`, `git commit -m "Major UI & AI Feature Update"`, and `git push`.

Let me know if you need to build any new features like the **Multiplayer 1v1 Hacker Arena** or the **Auto-Certificate Generator**!



