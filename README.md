# ⚡ AdvancedLMS — Enterprise AI-Powered Learning Management System & Cloud IDE

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Groq AI](https://img.shields.io/badge/Groq_AI-Qwen_3.8--27B-F55036?style=for-the-badge&logo=openai&logoColor=white)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Hardened_RBAC-success?style=for-the-badge&logo=shield)](https://github.com)
[![Architecture](https://img.shields.io/badge/Architecture-Modular_Monolith-purple?style=for-the-badge)](https://github.com)

**An ultra-modern, high-performance Learning Management System fusing native multi-compiler cloud execution, Groq-accelerated AI tutoring, gamified virtual economies, and an Obsidian Cyberpunk glassmorphic experience.**

[Key Features](#-key-features) • [System Architecture](#-system-architecture) • [Directory Structure](#-repository-structure) • [Quick Start](#-quick-start) • [Environment Setup](#-environment-variables) • [RBAC Security](#-role-based-access-control-rbac) • [API & Endpoints](#-api--key-routes-reference)

---

</div>

## 📌 Executive Overview

**AdvancedLMS** is an enterprise-grade educational ecosystem engineered for technical universities, coding academies, and corporate development programs. Traditional LMS platforms act as passive video repositories; **AdvancedLMS** transforms learning into an active, immersive workstation by integrating:

1. **Subprocess-isolated native compilation** for Python, JavaScript (Node.js), C++, and Java directly within the browser.
2. **Groq LPU-accelerated AI intelligence** delivering near-instant lecture notes, automated code diagnostics, and document-parsed dynamic quiz synthesis.
3. **An internal tokenized economy (LMS Coins)** rewarding consistency, lesson mastery, and peer code bounties.
4. **Hardened Multi-Tier RBAC** ensuring strict separation between Super Admins, Staff Administrators, Faculty, and Students.
5. **Zero-framework Obsidian Glassmorphic UI** engineered with pure vanilla CSS and JavaScript for blazing fast 60fps responsiveness.

---

## 🚀 Key Features

### 🎓 1. Continuous Learning Cinema Workstation (`course_watch.html`)
- **Dual-Engine Media Pipeline**: Seamlessly switches between the YouTube IFrame API and native HTML5 video with persistent playback speed controls (0.75x to 2x), theater mode, and full-screen support.
- **Smart Progress Tracking**: Real-time AJAX heartbeat automatically saves playback timestamps and grants lesson completion tokens upon reaching completion thresholds.
- **Groq AI Video Notes Synthesizer**: Generates instant structured lecture summaries, code snippets, and key exam takeaways on-demand using high-throughput Groq LLM inference.
- **Integrated Code Sandbox**: In-browser split-view code editor allowing students to test concepts alongside live video lectures without context switching.
- **Auto-Advance Playback**: Intelligently queues and transitions to the subsequent curriculum module upon lesson conclusion.

### ⚡ 2. Multi-Compiler Cloud IDE (`compiler_service.py`)
- **Multi-Language Support**:
  - 🐍 **Python 3.14+** (Native CPython runtime with AST safety checks)
  - 🟨 **JavaScript / Node.js** (V8 runtime execution)
  - ⚡ **C++ (GCC / MinGW)** (Real-time compilation and execution)
  - ☕ **Java (OpenJDK)** (Single-file compilation and class execution)
- **Subprocess Isolation & Security**: Enforces process execution timeouts (default 5.0s), restricted environment variables, and memory-safe buffer caps to prevent resource exhaustion.
- **AI-Powered Code Review**: Integrates Groq AI to critique time/space complexity, detect edge-case logic flaws, and offer targeted refactoring recommendations.
- **Docker-Ready Fallback**: Ready for containerized execution sandboxing in high-concurrency production deployments.

### 🧠 3. Document-to-Quiz AI Academic Engine (`ai_utils.py`)
- **Automated Curriculum Extraction**: Ingests raw course materials (`.pdf`, `.docx`, `.txt`) using `PyPDF2` and `python-docx`.
- **Dynamic Quiz Generation**: Prompts Groq Qwen/Llama models with strict JSON schema constraints to generate multi-choice questions with answer keys, explanations, and difficulty ratings.
- **Interactive Evaluation**: Instant grading with coin awards for high scores and detailed AI feedback explaining incorrect options.

### 🪙 4. Gamified LMS Economy & Marketplace
- **Earning Loop**: Students earn **+20 LMS Coins** per verified lesson completion, alongside active learning streak multipliers and community bounty payouts.
- **Course Unlocks & Coupons**: Coins can be redeemed to unlock premium advanced courses or coupled with administrator coupon codes.
- **Double-Entry Ledger**: Full transaction history recorded in `CoinTransaction` models, preventing replay or balance inflation exploits.
- **Competitive Leaderboard**: Global and batch-level ranking calculated dynamically from learning streak metrics, tasks completed, and cumulative coin yield.

### 💬 5. Real-Time Collaborative Community Hub
- **Study Group Chatrooms**: Course-specific discussion threads with code snippet highlighting and live emoji reactions.
- **Peer Bounty System**: Students can stake LMS Coins on complex programming challenges; peers who submit verified solutions claim the escrowed bounty.
- **Moderation Controls**: Administrative pinned announcements, content flags, and toxic language filtering.

### 📊 6. Executive Administrator Command Center
- **Telemetry Dashboards**: Interactive Chart.js graphs tracking 30-day enrollment velocity, coin circulation, and lesson completion trends.
- **Student & Faculty Management**: Granular user status auditing, password reset dispatchers, and profile inspection.
- **Course & Lesson Authoring**: Rich curriculum builder supporting module reordering, video URL ingestion, document attachments, and automated AI quiz binding.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Obsidian Glassmorphic UI)"]
        UI_Student["Student Workspace<br/>(Dashboard / Watch / IDE)"]
        UI_Admin["Admin Command Center<br/>(Analytics / User Control)"]
        UI_Chat["Community Hub<br/>(Bounties / Realtime Chat)"]
    end

    subgraph Gateway ["Application Gateway & Security"]
        AuthMiddleware["Authentication & RBAC Enforcement"]
        CSRF["CSRF Protection & Session Validator"]
    end

    subgraph Backend ["Django Application Core (lms_core / students)"]
        Router["URL Dispatcher"]
        Views["Student & Admin Views"]
        
        subgraph Services ["Core Services"]
            CompilerService["Compiler Sandbox Service<br/>(Python, JS, C++, Java)"]
            AIEngine["Groq AI Engine<br/>(Notes, Quizzes, Code Review)"]
            EconomyEngine["LMS Coin Ledger & Reward Engine"]
        end
        
        ORM["Django ORM Models"]
    end

    subgraph Storage ["Data & Sandboxing Layer"]
        DB[(SQLite / PostgreSQL DB)]
        DocParser["Document Ingestion<br/>(PyPDF2 / docx)"]
        HostProcess["Isolated Execution Subprocesses"]
    end

    Client --> Gateway
    Gateway --> Router
    Router --> Views
    Views --> Services
    Services --> ORM
    CompilerService --> HostProcess
    AIEngine --> DocParser
    ORM --> DB
```

---

## 📁 Repository Structure

```text
AdvancedLMS/
├── lms_core/                      # Project Configuration Root
│   ├── __init__.py
│   ├── asgi.py                    # ASGI asynchronous interface
│   ├── settings.py                # Core Django settings & third-party configs
│   ├── urls.py                    # Global URL route orchestration
│   └── wsgi.py                    # WSGI web server entry point
│
├── students/                      # Primary Application Module
│   ├── admin.py                   # Django admin registrations
│   ├── ai_utils.py                # Groq API wrappers, prompt templates, PDF parsers
│   ├── apps.py                    # App configuration
│   ├── compiler_service.py        # Multi-compiler runner & execution sandbox
│   ├── forms.py                   # User profile, login, & course authoring forms
│   ├── models.py                  # User, Course, Lesson, Quiz, Bounty, Coin models
│   ├── tests.py                   # Unit & integration test suites
│   ├── urls.py                    # Student & core API endpoints
│   └── views.py                   # Business logic, dashboard, watch, & admin views
│
├── frontend/                      # Presentation Layer
│   ├── static/                    # Static Assets
│   │   ├── css/                   # Custom stylesheets (Cyberpunk Obsidian theme)
│   │   ├── js/                    # Client-side reactivity, player API, compiler client
│   │   └── images/                # Brand badges, UI icons, default banners
│   └── templates/                 # Server-Side Django Templates
│       ├── base.html              # Core layout scaffold
│       ├── course_watch.html      # Continuous learning cinema & AI notes
│       ├── live_compiler.html     # Fullscreen multi-compiler workstation
│       ├── student_dashboard.html # Unified student overview & progress
│       ├── community_chat.html    # Collaborative chatroom & bounty exchange
│       └── custom_admin/          # Dedicated administration control center
│           ├── admin_dashboard.html
│           ├── admin_profile.html
│           ├── course_management.html
│           └── student_management.html
│
├── media/                         # User-uploaded course assets & document uploads
├── manage.py                      # Django CLI management utility
├── requirements.txt               # Locked production dependencies
├── .env.example                   # Environment configuration template
└── README.md                      # Project documentation
```

---

## 🛡️ Role-Based Access Control (RBAC)

AdvancedLMS features enterprise-grade permission segregation. The custom `User` model (`students.models.User`) implements strict DB hooks to prevent privilege elevation and cross-panel leakage:


| Capability | Super Admin | Staff Administrator | Faculty | Student |
| :--- | :---: | :---: | :---: | :---: |
| **System Superuser (`is_superuser=True`)** | ✅ Full | ❌ Restricted | ❌ Restricted | ❌ Restricted |
| **Manage Staff Admins & Global Passwords** | ✅ Full | ❌ Forbidden | ❌ Forbidden | ❌ Forbidden |
| **Course & Curriculum Authoring** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Read Only |
| **View Financials & Token Circulation** | ✅ Full | ✅ Full | ❌ Restricted | ❌ Restricted |
| **Access Admin Command Center** | ✅ Yes | ✅ Yes | ❌ Forbidden | ❌ Forbidden |
| **Enrolled Course Video Playback** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Earn LMS Coins on Lesson Mastery** | ❌ Excluded | ❌ Excluded | ❌ Excluded | ✅ Enforced |
| **Compete on Global Leaderboard** | ❌ Excluded | ❌ Excluded | ❌ Excluded | ✅ Active |

> [!IMPORTANT]
> **Data Integrity Guard**: An automated `pre_save` signal hook on the `User` model guarantees that any account assigned `is_staff=True` or `is_superuser=True` is strictly set to `is_student=False`. Administrative profiles are completely segregated from student leaderboards and enrollment queries.


---

## 💻 Native Multi-Compiler Execution Matrix

The internal compiler engine (`students/compiler_service.py`) dynamically detects installed system toolchains and securely executes code submissions:


```
User Code Submission (Web UI)
       │
       ▼
[Compiler Service Router]
       ├── Python   ───► AST Validation  ───► Subprocess python.exe -u (5s timeout)
       ├── Node.js  ───► Temp Script     ───► Subprocess node.exe (5s timeout)
       ├── C++      ───► MinGW g++ -O2   ───► Compiled Binary Runner (5s timeout)
       └── Java     ───► JDK javac       ───► Subprocess java Class (5s timeout)
       │
       ▼
Standard Output & Error Capture (Truncated to 10KB safe buffer)
       │
       ▼
JSON Response to Browser (Output, Memory, Status, Execution Time)
```

- **Output Sanitization**: Captures `stdout` and `stderr` up to a maximum buffer of 10,000 characters to prevent DOM denial-of-service.
- **Execution Limits**: Hard 5.0-second process termination timer protects CPU cores against infinite `while` loops or recursion overflow.

---

## ⚡ Quick Start

### 1. Prerequisites
- **Python 3.12+** or **Python 3.14+**
- **Git**
- Optional Compilers (for full IDE functionality):
  - **Node.js** (for JavaScript execution)
  - **MinGW GCC/g++** (for C++ compilation)
  - **OpenJDK 17+** (for Java compilation)

### 2. Clone and Setup Environment

```bash
# 1. Clone the repository
git clone https://github.com/your-username/AdvancedLMS.git
cd AdvancedLMS

# 2. Create and activate a Python virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment configuration:

```bash
cp .env.example .env
```

Edit your `.env` file and supply your configuration keys:

```ini
# Django Security
SECRET_KEY=your-super-secret-django-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Groq Cloud AI Engine (Required for Notes, Quiz Gen, & Code Reviews)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Database Configuration (Defaults to local SQLite if omitted)
# DATABASE_URL=postgresql://user:password@localhost:5432/advanced_lms
```

### 4. Database Migrations & Initial Setup

```bash
# Run database migrations
python manage.py makemigrations
python manage.py migrate

# Create the initial Super Administrator
python manage.py createsuperuser
```

### 5. Launch the Local Development Server

```bash
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000/` in your browser:
- **Student Dashboard**: `http://127.0.0.1:8000/dashboard/`
- **Continue Learning Cinema**: `http://127.0.0.1:8000/course/<course_id>/watch/`
- **Cloud Compiler**: `http://127.0.0.1:8000/compiler/`
- **Admin Command Center**: `http://127.0.0.1:8000/custom-admin/`

---

## 🔧 Environment Variables Reference

| Variable | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `SECRET_KEY` | String | *Auto-generated* | Django cryptographic secret key for session signing and tokens. |
| `DEBUG` | Boolean | `True` | Set to `False` in production deployments. |
| `ALLOWED_HOSTS` | List | `*` | Comma-separated list of host/domain names this site can serve. |
| `GROQ_API_KEY` | String | *None* | Groq Cloud API key for ultra-fast LPU inference (Qwen/Llama). |
| `COMPILER_TIMEOUT` | Float | `5.0` | Max seconds before an active compiler process is terminated. |
| `DATABASE_URL` | String | *SQLite* | Connection URI for production PostgreSQL / MySQL backends. |

---

## 📡 API & Key Routes Reference

| Route / Endpoint | HTTP Method | Access Level | Description |
| :--- | :---: | :---: | :--- |
| `/` | `GET` | Public | Landing page showcasing featured courses & platform overview. |
| `/dashboard/` | `GET` | Student | Primary student command hub with enrolled courses and analytics. |
| `/course/<id>/watch/` | `GET` | Student | Continuous learning cinema with video player and curriculum tree. |
| `/api/lesson/<id>/complete/` | `POST` | Student | Marks a lesson completed and awards +20 LMS Coins. |
| `/api/lesson/<id>/ai-notes/` | `POST` | Student | Synthesizes instant AI lecture notes using Groq LLM inference. |
| `/api/compile/` | `POST` | Authenticated | Executes submitted code in Python, JS, C++, or Java. |
| `/api/ai-review/` | `POST` | Authenticated | Provides automated AI feedback on code in the live compiler. |
| `/community/` | `GET`, `POST` | Authenticated | Study group chatroom with bounty submissions and reactions. |
| `/custom-admin/` | `GET` | Admin / Staff | Administrative analytics, user manager, and course creator. |
| `/custom-admin/profile/` | `GET`, `POST` | Admin / Staff | Admin profile manager with password reset security controls. |

---

## 🧪 Testing & Code Quality

AdvancedLMS includes automated test suites covering authentication boundaries, code compiler execution timeouts, and coin transaction integrity.

```bash
# Run the entire test suite
python manage.py test students

# Run compiler sandbox safety verification
python manage.py test students.tests.CompilerSafetyTests

# Check for security vulnerabilities
python manage.py check --deploy
```

---

## 🤝 Contributing

We welcome contributions from developers of all skill levels! To contribute:

1. **Fork the Repository** on GitHub.
2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/awesome-new-capability
   ```
3. **Commit Your Changes** with clean, conventional commit messages:
   ```bash
   git commit -m "feat(compiler): add memory limit monitoring for Java runtime"
   ```
4. **Push to Your Branch**:
   ```bash
   git push origin feature/awesome-new-capability
   ```
5. **Open a Pull Request** describing your changes and relevant screenshots.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for complete details.

<div align="center">

Built with precision for the next generation of software engineers.

⭐ **If you find this project helpful, please give it a star on GitHub!** ⭐

</div>
