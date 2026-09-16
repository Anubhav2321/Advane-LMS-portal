# 🎓 Learning-365 — AI-Powered Learning Management Ecosystem

### *Learn. Practice. Compete. Build. Repeat — 365 Days.*

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Sandbox-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/AI-Groq%20Llama-F55036?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Database-SQLite%20%2F%20PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
</p>


<p align="center">
  <strong>Learning-365</strong> is a next-generation AI-powered Learning Management System designed to combine structured education, AI-driven coding practice, digital learning resources, examinations, gamification, community interaction, and administrative management into one unified ecosystem.
</p>

<p align="center">
  <img src="frontend/static/images/dashboard.png" alt="Learning-365 Dashboard Preview" width="100%" />
</p>

---

## 🚀 What is Learning-365?

**Learning-365** is more than a traditional Learning Management System.

It is a complete digital learning ecosystem where students can:

* 🔐 Create an account and securely log in
* 🌐 Sign in using Google OAuth
* 📚 Enroll in multiple courses
* 💎 Access premium courses
* 🎥 Attend live classes
* 📖 Read and download learning resources
* 📂 Upload and download different types of educational files
* 🤖 Practice AI-generated coding problems
* 🧠 Take AI-generated examinations
* 🪙 Earn and spend LMS Coins
* 🏆 Compete on a global leaderboard
* 📊 Track their learning activity for the last 365 days
* 👤 Build a personalized premium student profile
* 💬 Interact with other learners through the community system
* ⚙️ Manage their complete learning journey from one dashboard

For administrators, Learning-365 provides a dedicated management environment to operate the entire LMS ecosystem.

---

# ✨ Core Platform Features

## 🔐 1. Real Authentication & User Management

Learning-365 includes a complete authentication system rather than a static/demo login interface.

### Authentication Features


* 👤 User Registration
* 🔑 Secure Login
* 🚪 Logout
* 🔒 Password-based authentication
* 🌐 **Sign in with Google**
* 👨‍🎓 Student profile creation
* 🖼️ Google profile picture synchronization
* 📝 User profile management
* 🔐 Session-based authentication
* 🛡️ Protected student pages
* ⚡ Automatic authentication state handling

The authentication architecture is designed to separate public pages, authenticated student areas, and administrator-only functionality.

---

# 📚 2. Multi-Course Learning Platform

Learning-365 supports a complete multi-course learning architecture.

Students can discover and access different courses from a centralized course library.

### Course Features

* 📖 Multiple courses
* 🏷️ Course categories
* 📝 Course descriptions
* 🎓 Course enrollment
* 📊 Learning progress
* 🎥 Video lessons
* 📄 Course resources
* 📚 Course materials
* 🔗 Lesson-based learning structure
* 💎 Premium course support

### Example Course Ecosystem

```text
Courses
│
├── Python Programming
├── Web Development
├── Data Structures & Algorithms
├── Database Management
├── Artificial Intelligence
├── Machine Learning
├── Cyber Security
└── More Courses
```

The architecture allows new courses and learning content to be added through the administration system without redesigning the student interface.

---

# 💎 3. Premium Course Ecosystem

Learning-365 supports premium learning content for advanced learners.

Premium courses can contain:

* 🎥 Premium video lessons
* 📄 Exclusive PDFs
* 📦 Downloadable resources
* 🧪 Premium examinations
* 💻 Advanced coding challenges
* 🎯 Specialized learning paths
* 🔐 Restricted-access course materials

This creates a foundation for building a scalable **free + premium educational platform**.

---

# 🎥 4. Live Class System

Learning-365 also supports live education instead of relying only on recorded lessons.

Students can access:

* 🔴 Live class information
* 📅 Class schedules
* 🎓 Course-specific live sessions
* 🔗 Live class access links
* 📝 Class-related resources
* 📚 Supporting study materials

The system can be extended to integrate platforms such as Google Meet, Zoom, or other live-class infrastructure.

---

# 📖 5. Digital Learning Library

The platform includes a centralized digital library for educational resources.

Students can access different types of learning materials including:

* 📕 PDF books
* 📄 Notes
* 📝 Documents
* 📊 Presentations
* 🗂️ ZIP resources
* 🖼️ Images
* 🎵 Audio resources
* 🎬 Video resources
* 💻 Source-code files
* 📦 Other educational assets

### Resource Operations

Students can:

**View → Open → Download → Learn**

while administrators can manage the available resources.

---

# 📂 6. File Upload & Download System

Learning-365 supports educational file management inside the LMS.

Depending on the resource type, the platform can provide:

```text
Upload
   ↓
Store
   ↓
Organize
   ↓
Display
   ↓
Download
```

This allows instructors/administrators to distribute course materials without requiring students to search for files externally.

---

# 🤖 7. Syntax Singularity — AI Coding Arena

## *An AI-generated LeetCode-style coding environment*

One of the core features of Learning-365 is **Syntax Singularity**.

Instead of depending entirely on a fixed database of coding questions, the system can use AI to dynamically generate coding practice challenges.

### How it works

```text
Student selects
      │
      ├── Programming Language
      ├── Topic
      └── Difficulty
              │
              ▼
        AI Question Engine
              │
              ▼
     Dynamically Generated
        Coding Challenge
              │
              ▼
        Student writes code
              │
              ▼
       Code Execution Engine
              │
              ▼
       Result + AI Evaluation
              │
              ▼
       Feedback / Hint / Score
```

### Supported Practice Concept

The experience is inspired by platforms such as **LeetCode**, but the challenge generation is AI-driven.

Students can practice:

* 🐍 Python
* ☕ Java
* 🌐 JavaScript
* 💻 C/C++
* 🧠 Data Structures
* 🔢 Algorithms
* 🗄️ SQL
* 🔀 Custom programming topics

### AI Challenge Generation

The AI can generate challenges based on:

* Topic
* Difficulty
* Programming language
* Problem type
* Learning objective

This makes the practice environment much more dynamic than a static question bank.

---

# 🧠 8. AI Code Logic Evaluation

Syntax Singularity is not limited to checking whether the final output is correct.

The AI-powered evaluation system can analyze the student's submitted solution and provide educational feedback.

Possible evaluation areas include:

* ✅ Correctness
* 🧠 Logical approach
* 📝 Syntax
* ⚡ Efficiency
* 🐛 Potential bugs
* 📈 Complexity
* 💡 Hints
* 📚 Improvement suggestions

The goal is to help students understand **why** their solution works or fails rather than simply showing a pass/fail result.

---

# 🐳 9. Secure Docker Code Execution

Student code can be executed through an isolated Docker-based execution environment.

Instead of executing arbitrary student code directly inside the Django server process:

```text
Student Code
     │
     ▼
Django Backend
     │
     ▼
Docker Sandbox
     │
     ├── CPU Limits
     ├── Memory Limits
     ├── Execution Limits
     └── Isolated Environment
     │
     ▼
Execution Result
     │
     ▼
Student
```

This architecture provides a stronger isolation boundary for coding practice.

> **Important:** Docker sandboxing improves isolation, but production deployment should still use defense-in-depth security controls such as strict resource limits, restricted networking, filesystem controls, timeouts, and container hardening.

---

# 🧪 10. AI Examination System

Learning-365 includes an AI-powered examination layer.

Instead of having only manually created questions, the platform can dynamically generate examination content using AI.

### AI Exam Capabilities

* 🧠 AI-generated questions
* 🎯 Topic-based exams
* 📊 Difficulty-based questions
* ⏱️ Timed examinations
* 📝 Multiple-choice questions
* 📈 Score calculation
* 📊 Performance evaluation
* 🏆 Result tracking
* 💡 Learning feedback

### Exam Flow

```text
Select Course / Topic
        ↓
Select Difficulty
        ↓
Generate AI Examination
        ↓
Attempt Questions
        ↓
Submit Exam
        ↓
Evaluate Result
        ↓
Score + Performance Analysis
```

---

# 🪙 11. LMS Coins — Gamified Learning Economy

Learning-365 introduces a virtual learning currency called:

## 🪙 LMS Coins

Students can earn coins through meaningful learning activities.

For example:

```text
Complete Lesson        → + Coins
Pass Quiz              → + Coins
Complete Coding Mission→ + Coins
Maintain Activity      → + Coins
Complete Challenges    → + Coins
```

The coin system transforms learning from a passive experience into a gamified progression system.

---

# 🏆 12. Global Leaderboard — Hall of Fame

Students can compete through a global leaderboard.

The leaderboard can rank students based on their LMS Coin achievements.

### Hall of Fame

```text
🥇 Rank #1
🥈 Rank #2
🥉 Rank #3
────────────────
#4
#5
#6
...
#10
```

The system encourages:

* Healthy competition
* Consistent learning
* Coding practice
* Course completion
* Community participation

---

# 📊 13. Premium Student Profile

Each student gets a dedicated profile ecosystem.

The profile can display:

* 👤 Profile picture
* 🧑 Student information
* 🪙 LMS Coins
* 🏆 Rank
* 📚 Enrolled courses
* 🎓 Completed courses
* 🧠 Coding activity
* 🧪 Examination performance
* 🔥 Learning streak
* 📈 Activity history

---

# 📈 14. Activity Graph — Last 365 Days

One of the major profile features is a GitHub-inspired contribution activity graph.

## **Activity Graph // Last 365 Days**

The graph visualizes a student's learning activity throughout the year.

Example activity sources:

```text
Coding Practice
Course Completion
Quiz Attempts
Exam Attempts
Learning Sessions
Challenges Completed
```

Conceptually:

```text
Activity Graph // Last 365 Days

Less Activity  ░ ▒ ▓ █  More Activity

Mon  ░ ░ ▒ ▓ █ ▒ ░ ░ ▓ █
Tue  ░ ▒ ▓ ▓ █ ░ ▒ ░ ▓ ▒
Wed  ▒ ▓ █ ░ ░ ▒ ▓ █ ▓ ░
Thu  ░ ░ ▒ ▓ █ ▓ ▒ ░ ░ ▓
Fri  ▓ █ ▓ ▒ ░ ▒ ▓ █ ░ ▒
```

This gives students a visual representation of their consistency over the previous **365 days**.

---

# 💬 15. Community Commlink

Learning-365 includes a dedicated student community environment.

Students can communicate with other learners through a modern real-time-style interface.

### Community Features

* 💬 Student-to-student communication
* 🧵 Multi-threaded discussions
* 📎 File attachments
* 🖼️ Image sharing
* 🎵 Audio sharing
* 📄 Document sharing
* 😀 Emoji support
* 💻 Integrated coding editor
* 🐳 Code execution
* 🪙 Coin bounty system

---

# 🪙 16. Community Bounty System

Students can attach an LMS Coin bounty to a question.

Example:

```text
Student A
   │
   ├── Posts coding problem
   └── Adds 100 LMS Coins bounty
             │
             ▼
       Community Members
             │
             ▼
       Student B provides
          correct solution
             │
             ▼
      "Accept & Award"
             │
             ▼
       +100 LMS Coins
```

This creates a community-driven learning and problem-solving ecosystem.

---

# 💻 17. Integrated VS Code-Style Editor

Students can access a coding environment directly inside supported LMS interfaces.

The editor provides a familiar developer experience with:

* Syntax highlighting
* Code editing
* Language selection
* Run functionality
* Execution output
* Error output
* Docker-powered execution
* Code attachment to discussions

The objective is to reduce the friction between **learning → coding → testing → sharing**.

---

# ⏱️ 18. Deep Work Focus Mode

Learning-365 includes a productivity-focused study environment.

### Focus Mode

* ⏱️ Pomodoro timer
* 🎧 Lo-Fi study experience
* 📚 Dedicated study environment
* 🔥 Focus sessions
* 📊 Activity tracking

Students can use Focus Mode while studying courses or practicing coding challenges.

---

# 🛠️ 19. Premium Admin Management System

Learning-365 is not only a student-facing application.

It includes a dedicated administrative environment designed to operate and manage the LMS.

## 🛡️ Admin Control Center

Administrators can manage the core platform ecosystem.

### User Management

* 👥 View students
* 🔍 Search users
* 📝 Manage student profiles
* 🔐 Manage account access
* 📊 Monitor user activity

### Course Management

* ➕ Create courses
* ✏️ Edit courses
* 🗑️ Remove courses
* 📚 Manage lessons
* 🎥 Manage course videos
* 💎 Manage premium courses
* 👨‍🎓 Manage enrollments

### Content Management

Administrators can manage:

* PDFs
* Documents
* Videos
* Images
* Notes
* Source code
* Course resources
* Other educational files

### Examination Management

* Create exams
* Manage questions
* Configure difficulty
* Review results
* Monitor student performance

### AI Configuration

The administrative architecture can also support management of AI-powered learning services and their configuration.

---

# 📊 20. Admin Dashboard

The admin interface is designed as a centralized control center.

Possible operational metrics include:

```text
┌─────────────────────────────────────────────┐
│              ADMIN CONTROL CENTER           │
├─────────────────────────────────────────────┤
│                                             │
│  Students       Courses       Premium       │
│     ↓              ↓             ↓          │
│  Analytics      Content       Revenue*      │
│                                             │
│  Exams          Resources      Activity      │
│     ↓              ↓             ↓          │
│  Results       Downloads      Engagement     │
│                                             │
└─────────────────────────────────────────────┘
```

*Revenue/payment functionality can be integrated as the platform evolves.

---

# 🎨 21. Cyberpunk / Glassmorphic UI

Learning-365 follows a futuristic developer-focused visual identity.

### Design Philosophy

* 🌌 Dark interface
* 💎 Glassmorphism
* ⚡ Neon accents
* 🧊 Translucent cards
* 💻 Developer-inspired components
* 📊 Data visualization
* ✨ Interactive animations
* 🎯 Dashboard-oriented UX

The visual language is designed to make an educational platform feel closer to a **developer command center** than a traditional LMS.

---

# 🚀 Recent Updates: Advanced Analytics & Tracking

Learning-365 has recently undergone a major feature update focusing on advanced analytics, progress tracking, and UI/UX improvements.

### 📊 Advanced Analytics & Student Tracking
* **Granular Activity Tracking:** Implemented new architectural data models (`StudentActivity`, `LessonProgress`, `DocumentView`, `LiveClassAttendance`) to securely capture fine-grained user interactions across the platform.
* **Real-Time Admin Analytics:** The Admin Dashboard now features dynamic visualizations, including daily activity graphs, course progress metrics, and quiz score trends, providing a bird's-eye view of platform engagement.
* **Intelligent Progress Monitoring:** Administrators can deeply analyze specific students and courses to view a complete breakdown of their learning journey, recent actions, and resource utilization.

### 🎨 UI/UX & Dashboard Redesign
* **Student Panel Revamp:** Upgraded the Student Dashboard, Profile, and Course Watch interfaces for a more immersive, seamless, and intuitive learning experience.
* **Community Chat Enhancements:** Refined the community interface to align perfectly with the platform's premium glassmorphic, developer-focused aesthetic.
* **Premium Admin Experience:** Complete overhaul of the Admin Control Center, transforming it into a sleek, data-rich command center for managing the entire educational ecosystem.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │      STUDENT        │
                         │   Web Application   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       Django        │
                         │    Application      │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
       │ Authentication│       │  LMS Core   │       │ Community   │
       │ & Google OAuth│       │   System    │       │   System    │
       └─────────────┘       └──────┬──────┘       └─────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
             ┌────────────┐  ┌────────────┐  ┌──────────────┐
             │    Groq    │  │  Database  │  │    Docker    │
             │ AI Engine  │  │            │  │   Sandbox    │
             └────────────┘  └────────────┘  └──────────────┘
                    │               │               │
                    ▼               ▼               ▼
             AI Questions     User / LMS       Code Execution
             AI Exams        Data / Content
             AI Feedback
```

---

# 📂 Project Structure

```text
Learning-365/
│
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── students/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── ai_service.py
│   └── temp_codes/
│
├── templates/
│   ├── landing/
│   ├── authentication/
│   │   ├── login.html
│   │   ├── register.html
│   │   └── google_login.html
│   │
│   ├── student_dashboard/
│   ├── student_profile/
│   ├── courses/
│   ├── premium_courses/
│   ├── live_classes/
│   ├── library/
│   ├── community_chat/
│   ├── syntax_singularity/
│   ├── examinations/
│   ├── leaderboard/
│   ├── focus_mode/
│   └── admin/
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── assets/
│
├── media/
│   ├── profile_pictures/
│   ├── course_materials/
│   ├── documents/
│   └── thumbnails/
│
├── Dockerfile
├── requirements.txt
├── manage.py
├── .env.example
├── .gitignore
└── README.md
```

---

# 🧰 Technology Stack

| Layer                | Technology                           |
| -------------------- | ------------------------------------ |
| Backend              | Django                               |
| Programming Language | Python                               |
| Frontend             | HTML, CSS, JavaScript                |
| UI                   | Custom Cyberpunk / Glassmorphic UI   |
| AI Engine            | Groq API / Llama                     |
| Database             | SQLite / PostgreSQL                  |
| Authentication       | Django Authentication + Google OAuth |
| Code Execution       | Docker                               |
| File Storage         | Django Media System                  |
| Version Control      | Git + GitHub                         |
| Deployment           | Docker-compatible hosting            |

---

# 🔐 Security Architecture

Security is an important part of the Learning-365 architecture.

The platform is designed around:

* 🔑 Authenticated sessions
* 🛡️ Protected routes
* 🔐 Environment-based secrets
* 🚫 No API keys inside source code
* 🐳 Isolated code execution
* ⏱️ Execution time limits
* 💾 Resource restrictions
* 👨‍💼 Admin-only management areas
* 🔒 CSRF protection through Django
* 🧹 Temporary code cleanup

For production deployments, additional security hardening should be applied according to the hosting environment.

---

# ⚙️ Installation & Setup

## Prerequisites

Before running Learning-365, install:

* Python 3.10+
* Git
* Docker Desktop
* A supported database
* Groq API Key
* Google OAuth credentials

---

## 1️⃣ Clone Repository

```bash
git clone https://github.com/Anubhav2321/Learning-365.git

cd Learning-365
```

---

## 2️⃣ Create Virtual Environment

### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 4️⃣ Environment Configuration

Create a `.env` file in the root directory.

```env
DEBUG=True

SECRET_KEY=your_django_secret_key

GROQ_API_KEY=your_groq_api_key

GOOGLE_CLIENT_ID=your_google_client_id

GOOGLE_CLIENT_SECRET=your_google_client_secret
```

> Never commit `.env` files or private API credentials to GitHub.

---

# 🐳 5️⃣ Build Docker Code Execution Environment

If Syntax Singularity code execution is enabled:

```bash
docker build -t local-compiler .
```

Verify Docker:

```bash
docker --version
```

---

# 🗄️ 6️⃣ Database Setup

Run:

```bash
python manage.py makemigrations

python manage.py migrate
```

---

# 👨‍💼 7️⃣ Create Administrator

Create the initial administrator account:

```bash
python manage.py createsuperuser
```

Follow the terminal instructions.

The administrator can then access the Django administration environment.

---

# ▶️ 8️⃣ Start Learning-365

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

# 🔄 Platform User Flow

```text
                    ┌──────────────┐
                    │    Landing   │
                    │     Page     │
                    └──────┬───────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
           Register                Login
                │                     │
                └──────────┬──────────┘
                           │
                           ▼
                    Student Dashboard
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
       Courses        Syntax Singularity   Community
          │                │                 │
          ▼                ▼                 ▼
     Learn / Watch    AI Coding Practice   Discuss
          │                │                 │
          └────────────────┼─────────────────┘
                           │
                           ▼
                     LMS Coins
                           │
                           ▼
                    Leaderboard
                           │
                           ▼
                  Premium Profile
                           │
                           ▼
                Activity Graph
                Last 365 Days
```

---

# 🌐 Deployment

Learning-365 can be deployed to a production environment using a Docker-compatible hosting architecture.

A typical deployment can include:

```text
                    Internet
                       │
                       ▼
                 Web Application
                       │
                       ▼
                    Django
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Database       AI API      Storage
          │
          ▼
     PostgreSQL
```

For production:

* Set `DEBUG=False`
* Use a strong `SECRET_KEY`
* Configure allowed hosts
* Use PostgreSQL or another production database
* Configure static/media storage
* Secure OAuth credentials
* Configure HTTPS
* Harden Docker execution
* Store secrets outside Git

---

# 📈 Future Roadmap

Learning-365 is designed to grow into a complete EdTech ecosystem.

### Planned / Potential Extensions

* [ ] 💳 Online payment integration
* [ ] 💎 Subscription-based premium membership
* [ ] 📜 Automatic course certificates
* [ ] 🏅 Digital achievement badges
* [ ] 🤝 Multiplayer 1v1 Coding Arena
* [ ] 🧠 AI Personal Learning Assistant
* [ ] 📊 Advanced student analytics
* [ ] 🎯 AI-generated personalized learning paths
* [ ] 📱 Progressive Web App / Mobile Application
* [ ] 🔴 Integrated live-class infrastructure
* [ ] 🔔 Real-time notifications
* [ ] 🏆 Seasonal coding competitions
* [ ] 👨‍🏫 Instructor dashboard
* [ ] 📚 AI-powered course recommendations
* [ ] 🧑‍💻 Advanced code similarity detection

---

# 👨‍💻 About the Architect

## Anubhav Samanta

🎓 **BCA Student — Techno India University, West Bengal**

💻 **Full-Stack Developer | AI Integration | UI/UX**

🤖 Creator of **ARIS — Advanced Desktop AI Assistant**

🧠 Interested in **Artificial Intelligence, Machine Learning, Full-Stack Development and Developer Tools**

🏅 Certified in **AI Fundamentals & Prompt Engineering — IBM SkillsBuild**

---

# 🔗 Connect With Me

<p>
  <a href="https://github.com/Anubhav2321" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white" />
  </a>

  <a href="https://www.linkedin.com/in/anubhav-samanta-187549379" target="_blank">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" />
  </a>
</p>

---

# 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for more information.

---

# ⭐ Project Philosophy

> **"Code. Learn. Compete. Build. Repeat — 365 Days."**

Learning-365 is built with one goal:

### To transform learning from a passive activity into an interactive, competitive and intelligent experience.

From **AI-generated coding challenges** to **365-day activity tracking**, from **premium courses** to **real authentication**, from **LMS Coins** to a complete **administrative control center** — Learning-365 brings the major components of a modern EdTech platform into one ecosystem.

---

<p align="center">
  <strong>🎓 Learning-365</strong>
  <br>
  <sub>AI-Powered Learning • Coding Practice • Gamification • Community • Education</sub>
</p>
