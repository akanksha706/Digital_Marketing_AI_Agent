# 42 WORKS Studio — Digital Marketing AI Creative Platform

An enterprise-grade, autonomous AI creative suite that converts plain prompts, brand concepts, or campaign briefs into studio-quality marketing posters, 14-second cinema video reels, and ready-to-publish social media campaigns in seconds.

---

## Table of Contents
1. [Overview & Core Capabilities](#overview--core-capabilities)
2. [Role-Based Authentication & Access Control](#role-based-authentication--access-control)
3. [Complete Directory & File Structure](#complete-directory--file-structure)
4. [Environment Configuration (Single Source of Truth)](#environment-configuration-single-source-of-truth)
5. [How to Run the Project (Step-by-Step)](#how-to-run-the-project-step-by-step)
   - [Prerequisites](#prerequisites)
   - [Step 1: Running the Backend](#step-1-running-the-backend)
   - [Step 2: Running the Frontend](#step-2-running-the-frontend)
   - [Step 3: Running the Automated Test Suite](#step-3-running-the-automated-test-suite)
6. [Interactive Video Typography & Motion Engine](#interactive-video-typography--motion-engine)
7. [API Endpoints Reference](#api-endpoints-reference)
8. [Git Push Instructions](#git-push-instructions)

---

## Overview & Core Capabilities

Traditional digital marketing requires juggling multiple design tools, stock photo sites, video editors, and copywriting templates. **42 WORKS Studio** unifies the entire workflow into a single, intuitive platform:

- **Cinematic Poster Generation (1080 × 1080, 4:5, 16:9, 9:16)**: High-resolution visual art generated with Flux.1 Schnell, complete with intelligent headroom placement, authentic cultural details, and brand identity safeguards.
- **14-Second Cinema Video Reels (720 × 1280, 9:16 Vertical)**: Realistic motion reels synthesized with **Wan 2.2 neural diffusion**, featuring genuine human gestures (e.g. smooth circular aarti motion, devotional smiles, water ripples), ambient camera push-in, and a branded outro card.
- **Multimodal AI Safe Headroom Placement**: Computer vision automatically scans clean background imagery to detect open safe spaces (headroom or floor) and chooses optimal high-contrast colors so text never covers faces, hands, or props.
- **Interactive Drag-and-Drop Typography Editor**: Move, scale, stretch, and rotate typography directly over the poster canvas or live video player with instant sub-6-second streaming parallel FFmpeg re-composition.
- **Campaign Copywriting & Social Dispatch**: AI-generated structured captions with narrative hooks, bulleted insights, emojis, and hashtags, with one-click direct publishing to LinkedIn and Instagram or scheduled dispatch.
- **Role-Based Access Control**: Pre-configured user roles with fine-grained permissions for administrators and creative teams.

---

## Role-Based Authentication & Access Control

The platform implements strict role-based access control (RBAC) with pre-configured team account tiers:

| Role | Permissions & Scope |
| :--- | :--- |
| **Admin Lead** | Full administrative access, user creation in `/admin`, brand guidelines configuration, and system oversight |
| **Creator Member** | Prompt input, poster generation, review & edit, video reel creation, social dispatch |

> [!NOTE]
> For security standards in public repositories, default team login credentials are documented in the internal product guide (`PRODUCT_KNOWLEDGE_BASE.md`) and are initialized upon running `python scripts/manage_db.py`.

---

## Complete Directory & File Structure

Below is the complete project tree detailing every file, directory, and its responsibility:

```text
Digital_Marketing/
├── .env                                  # Single active environment secrets file (never committed)
├── .env.example                          # Clean template of all environment variables
├── .gitignore                            # Comprehensive git ignore rules
├── README.md                             # Primary repository guide & execution manual
├── PRODUCT_KNOWLEDGE_BASE.md             # Complete product user guide, credentials, and feature manual
├── Digital_Marketing_AI_Agent.md         # In-depth technical architecture and engineering guide
│
├── Backend/                              # FastAPI Python Backend Application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                       # Application entry point, CORS, and static mount
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── dependencies.py           # Dependency injection (Auth, DB session, Services)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py             # Master API router grouping all v1 endpoints
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           ├── admin.py          # User management, brand settings, and system rules
│   │   │           ├── assistant.py      # Interactive Sparky AI assistant endpoints
│   │   │           ├── auth.py           # JWT token generation, login, and user profile
│   │   │           ├── custom_creatives.py # User-uploaded imagery and custom layout compositor
│   │   │           ├── linkedin_oauth.py # OAuth2 flow and callback handling for LinkedIn
│   │   │           ├── posters.py        # Generation, autocomplete, library listing, and deletion
│   │   │           ├── reviews.py        # Plain-language edits, manual typography updates, approval
│   │   │           ├── schedules.py      # Post scheduling, dispatch queue, and instant publishing
│   │   │           ├── url_campaigns.py  # Web URL scraping and automatic poster concept creation
│   │   │           └── videos.py         # Prompt-to-video reel generation and fast re-composition
│   │   ├── adapters/                     # Modular third-party service adapters
│   │   │   ├── __init__.py
│   │   │   ├── ai/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cloudflare_image.py   # Flux.1 Schnell image diffusion adapter
│   │   │   │   ├── cloudflare_text.py    # LLaMA 3.1 8B Instruct copywriting adapter
│   │   │   │   └── video_adapter.py      # Wan 2.2 / Wan 2.1 video reel diffusion adapter
│   │   │   ├── publishers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── instagram_adapter.py  # Instagram Graph API publisher
│   │   │   │   └── linkedin_adapter.py   # LinkedIn REST API publisher
│   │   │   ├── safety/
│   │   │   │   ├── __init__.py
│   │   │   │   └── guardrails.py         # Content moderation and banned-word filtering
│   │   │   ├── scrapers/
│   │   │   │   ├── __init__.py
│   │   │   │   └── firecrawl_adapter.py  # Firecrawl real-time web retrieval
│   │   │   └── storage/
│   │   │       ├── __init__.py
│   │   │       └── local_storage.py      # Local file system storage provider
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # Pydantic Settings loading root .env
│   │   │   ├── errors.py                 # User-friendly error formatting and translations
│   │   │   ├── prompts.py                # System prompts for copy, art direction, and physical realism
│   │   │   └── security.py               # Password hashing (bcrypt) and JWT encode/decode
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                   # SQLAlchemy Declarative Base
│   │   │   ├── models.py                 # ORM models (User, Brand, Poster, StyleRule, Schedule)
│   │   │   └── session.py                # Async session factory and engine lifecycle
│   │   ├── domain/
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analytics.py          # Analytics and performance data schemas
│   │   │   │   ├── auth.py               # Login, register, token, and user schemas
│   │   │   │   ├── brand.py              # Brand guidelines schemas
│   │   │   │   ├── knowledge_graph.py    # Knowledge graph and learned style rule schemas
│   │   │   │   ├── poster.py             # Poster creation, response, and layout schemas
│   │   │   │   ├── review.py             # Edit requests and revision history schemas
│   │   │   │   └── schedule.py           # Scheduling job schemas
│   │   ├── services/                     # Core business logic services
│   │   │   ├── __init__.py
│   │   │   ├── custom_upload_service.py  # Image upload and layout detection
│   │   │   ├── generation_service.py     # End-to-end prompt-to-poster pipeline coordinator
│   │   │   ├── google_calendar_service.py# Upcoming holiday and festival auto-calendar
│   │   │   ├── knowledge_graph.py        # Pinecone vector memory and style rule learner
│   │   │   ├── poster_compositor.py      # Pillow typography, drop shadow, and logo compositor
│   │   │   ├── review_service.py         # Revision engine and plain-language revision parsing
│   │   │   ├── scheduling_service.py     # Job scheduler and social media dispatch orchestrator
│   │   │   ├── url_crawler_service.py    # URL extraction and brand tone analysis
│   │   │   ├── video_service.py          # Fast streaming FFmpeg video compositor (sub-6s)
│   │   │   ├── visual_director.py        # Computer vision contrast & headroom analyzer
│   │   │   └── visual_knowledge_service.py # Live web retrieval for cultural & factual accuracy
│   │   └── workers/
│   │       ├── __init__.py
│   │       └── scheduler_worker.py       # Background task processor for scheduled posts
│   ├── scripts/                          # Utility & setup scripts
│   │   ├── add_analytics_cols.py         # Schema update helper
│   │   ├── check_tables.py               # Database inspection script
│   │   ├── manage_db.py                  # Database initialization and default user seeding
│   │   ├── setup_guide_table.py          # Knowledge base guide table setup
│   │   ├── test_dynamic_inpaint.py       # Diffusion test script
│   │   ├── update_password.py            # Password update utility
│   │   └── upsert_to_pinecone.py         # Knowledge embedding upsert script
│   ├── storage/                          # Local asset storage directory (ignored by git)
│   │   ├── posters/                      # Generated static poster PNGs (.gitkeep preserved)
│   │   └── videos/                       # Generated video reel MP4s (.gitkeep preserved)
│   ├── tests/                            # Automated test suite (16 tests, 100% green)
│   │   ├── conftest.py                   # Pytest fixtures, mock sessions, and test client
│   │   ├── test_auth_and_users.py        # Auth, JWT, and admin user creation tests
│   │   ├── test_knowledge_graph_and_admin.py # Brand rules and knowledge graph tests
│   │   ├── test_poster_generation.py     # Prompt-to-poster generation and safety tests
│   │   ├── test_review_workflow.py       # Edit revisions and approval locking tests
│   │   └── test_scheduling_workflow.py   # Scheduled dispatch and LinkedIn publishing tests
│   ├── requirements.txt                  # Python dependencies
│   └── pytest.ini                        # Pytest configuration
│
└── Frontend/                             # React 19 + TypeScript + Vite Frontend Application
    ├── index.html                        # Application HTML root
    ├── package.json                      # Node dependencies and scripts
    ├── vite.config.ts                    # Vite build and proxy configuration
    ├── tsconfig.json                     # TypeScript compiler configuration
    └── src/
        ├── App.tsx                       # Root view router with protected routes
        ├── App.css                       # Application styling
        ├── index.css                     # Tailwind CSS design system rules
        ├── main.tsx                      # React DOM mount point
        ├── api/
        │   └── client.ts                 # Axios HTTP client with JWT interceptors
        ├── components/
        │   ├── AppreciativePoster.tsx    # Visual poster preview card with badges
        │   ├── ChangePasswordModal.tsx   # User profile password update modal
        │   ├── Footer.tsx                # Studio footer
        │   ├── Navbar.tsx                # Navigation bar with workspace tabs and user menu
        │   ├── RadialCursor.tsx          # Interactive ambient cursor illumination
        │   ├── SocialIcons.tsx           # Platform icons (LinkedIn, Instagram, X)
        │   └── SparkyMascot.tsx          # Interactive AI mascot helper
        ├── context/
        │   └── AuthContext.tsx           # Authentication state provider (login/logout/token)
        ├── types/
        │   └── index.ts                  # TypeScript interfaces for Posters, Brands, and Users
        └── views/
            ├── AdminPage.tsx             # Team user management and brand guidelines editor
            ├── LibraryPage.tsx           # Filterable gallery of created posters and video reels
            ├── LoginPage.tsx             # Role-based login screen
            ├── ReviewModal.tsx           # Interactive canvas editor with live video typography
            ├── SchedulesPage.tsx         # Publishing queue and calendar schedule management
            └── StudioPage.tsx            # Main prompt studio with upcoming occasion cards
```

---

## Environment Configuration (Single Source of Truth)

All backend services, database connections, and AI models read from a **single unified `.env` file** located at the repository root. Duplicate nested env files inside `Backend/` have been removed to prevent confusion.

### Creating Your `.env` File
Copy the provided `.env.example` file at the root:

```bash
# On Windows (PowerShell):
Copy-Item .env.example .env

# On macOS / Linux:
cp .env.example .env
```

### Essential Settings in `.env`:
```ini
# Database Connection (PostgreSQL on port 5434)
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5434/poster_studio

# Cloudflare Workers AI Secrets
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

# Google Gemini API (Multimodal Vision & Fallback)
GEMINI_API_KEY=your_gemini_api_key

# Hugging Face Access Token (Wan 2.2 / Fast Video Diffusion)
HUGGINGFACE_API_KEY=your_hugging_face_token
HUGGING_FACE_TOKEN=your_hugging_face_token

# Firecrawl / Web Retrieval
FIRECRAWL_API_KEY=your_firecrawl_api_key

# Pinecone Vector DB
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=poster-studio-knowledge

# Security
JWT_SECRET_KEY=dev_secret_key_change_in_production
```

---

## How to Run the Project (Step-by-Step)

### Prerequisites

Verify the following tools are installed on your system:
- **Python**: 3.11 or 3.12 (`python --version`)
- **Node.js**: v18 or higher with npm (`node -v` and `npm -v`)
- **PostgreSQL**: Running on port `5434` (or port `5432` matching your `DATABASE_URL`)
- **FFmpeg**: Installed and accessible in your system PATH (`ffmpeg -version`)

---

### Step 1: Running the Backend

Open a terminal and navigate into the `Backend` directory:

```bash
# 1. Navigate to the Backend folder
cd "Backend"

# 2. Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.venv\Scripts\activate.bat
# On macOS / Linux:
source .venv/bin/activate

# 3. (Optional) Install dependencies if running for the first time:
pip install -r requirements.txt

# 4. Initialize database tables and seed pre-configured users:
python scripts/manage_db.py

# 5. Start the FastAPI backend server with auto-reload:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once running:
- **Backend API**: `http://127.0.0.1:8000`
- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

### Step 2: Running the Frontend

Open a **second terminal window** and navigate into the `Frontend` directory:

```bash
# 1. Navigate to the Frontend folder
cd "Frontend"

# 2. (Optional) Install npm packages if running for the first time:
npm install

# 3. Start the Vite development server:
npm run dev
```

Once running:
- **Web Application**: `http://localhost:5173/`

Sign in using your configured **Admin Lead** or **Creator Member** account credentials.

---




### Step 3: Running the Automated Test Suite

To run all backend unit, integration, and security tests:

```bash
# From the root directory:
Backend\.venv\Scripts\python.exe -m pytest Backend\tests\ -v

# Or from inside the Backend directory:
cd Backend
python -m pytest tests/ -v
```

All 16 tests pass green with 100% test coverage across core workflows.

---

## Interactive Video Typography & Motion Engine

The application includes an ultra-fast streaming video composition engine:

1. **AI Headroom Detection**: When generating a reel, computer vision analyzes the clean source image to identify safe open space (headroom or floor) and places typography automatically without obscuring faces or subjects.
2. **Interactive Drag & Reposition**: When viewing the video reel tab in the Review window, users can freely drag, scale, stretch, and rotate the typography bounding box over the video canvas.
3. **Approval Action Bar**: An action bar directly beneath the video displays:
   `Video Text Position: Y%` | `Cancel` | `[✓ Approve & Place Here]`
4. **Streaming Parallel FFmpeg Re-Composition**:
   - Precomputes glow templates and text overlays outside the frame loop.
   - Streams raw RGB24 frames directly into FFmpeg via standard input using `-preset ultrafast` and `-crf 20`.
   - Re-composites the full 14-second video reel in **under 6 seconds** (>83% faster than traditional renders).

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Authenticate user and return JWT bearer token |
| `GET` | `/api/v1/auth/me` | Fetch authenticated user profile and brand details |
| `POST` | `/api/v1/posters/generate` | Synthesize creative poster visual, copy, and layout |
| `GET` | `/api/v1/posters/autocomplete` | Real-time predictive prompt autocomplete suggestions |
| `GET` | `/api/v1/posters` | List all saved posters and video reels |
| `POST` | `/api/v1/videos/generate-from-prompt` | Direct one-click prompt-to-video reel generation |
| `POST` | `/api/v1/videos/from-poster` | Animate an approved poster into a 9:16 video reel |
| `POST` | `/api/v1/reviews/{id}/edit` | Apply plain-language or manual coordinate revisions |
| `POST` | `/api/v1/reviews/{id}/approve` | Approve poster and lock typography coordinates |
| `POST` | `/api/v1/schedules/post-now` | Publish immediately to LinkedIn or Instagram |
| `POST` | `/api/v1/schedules` | Schedule a future post in the dispatch queue |
| `GET` | `/api/v1/admin/users` | List team members (Admin only) |
| `POST` | `/api/v1/admin/users` | Create new team member (Admin only) |

---